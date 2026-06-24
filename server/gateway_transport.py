"""
gateway_transport.py
====================

A drop-in, serial-compatible transport that talks to a *SplitFlap Gateway*
(an ESP32 running SplitFlapGateway_2.ino) over MQTT instead of a local serial
port.

The rest of splitflap-os was written against a pyserial ``Serial`` object and
uses only a small slice of its API:

    * ``.write(bytes)``        -> send a frame to the bus
    * ``.flush()``             -> no-op for us (MQTT publish is already flushed)
    * ``.reset_input_buffer()``-> drop any buffered RX data
    * ``.in_waiting``          -> number of RX bytes available to read
    * ``.read(n)``             -> read up to ``n`` RX bytes
    * ``.close()``             -> tear down

``GatewayTransport`` implements exactly that surface so the existing call sites
in app.py work unchanged.

Protocol (see SplitFlapGateway_2.ino):

    App -> Gateway   topic  <prefix>/send
        The gateway accepts a *plain* RS485 frame as the payload (e.g.
        ``b"m05-A\n"``) and forwards it verbatim onto the bus.  We publish the
        exact bytes the old code used to write to the serial port.

    Gateway -> App   topic  <prefix>/rx
        For every frame the gateway *receives back* from a module it publishes
        JSON: ``{"ts":<ms>,"wt":"<walltime>","command":"<ascii frame>"}``.
        The ``command`` field holds the ASCII frame with its trailing newline
        stripped.  We re-append a newline and feed the bytes into an internal
        RX buffer so the existing ``in_waiting`` / ``read`` loops (which scan
        for target strings like ``m05d:...``) behave just like a serial port.

Only those two topics are touched, matching the requirement to minimise the
splitflap-os footprint.
"""

import json
import logging
import os
import threading
import time

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover - handled by caller
    mqtt = None


class GatewayConnectionError(Exception):
    """Raised when the gateway broker cannot be reached at startup."""


class GatewayTransport:
    """Serial-compatible facade over an MQTT SplitFlap Gateway.

    Parameters
    ----------
    broker : str
        MQTT broker hostname / IP.
    port : int
        MQTT broker port (typically 1883).
    prefix : str
        Topic prefix configured on the gateway (default ``splitflap``).
        We only ever use ``<prefix>/send`` and ``<prefix>/rx``.
    username, password : str, optional
        MQTT credentials.  Leave blank for an anonymous broker.
    connect_timeout : float
        Seconds to wait for the initial connection before giving up.
    """

    def __init__(self, broker, port=1883, prefix="splitflap",
                 username="", password="", connect_timeout=8.0):
        if mqtt is None:
            raise GatewayConnectionError("paho-mqtt is not installed")

        self.broker = broker
        self.port = int(port)
        self.prefix = (prefix or "splitflap").strip().rstrip("/")
        self.send_topic = f"{self.prefix}/send"
        self.rx_topic = f"{self.prefix}/rx"

        # Internal RX byte buffer, emulating a serial input buffer.
        self._rx_buf = bytearray()
        self._rx_lock = threading.Lock()
        self._connected = threading.Event()
        self._closed = False

        # Include the PID so a crash-loop restart within the same second (common
        # on a Pi) doesn't collide with the previous session's client ID, which
        # would cause the broker to kick one of the two connections.
        client_id = f"splitflap-os-{os.getpid()}-{int(time.time())}"
        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2, client_id=client_id
        )
        if username:
            self._client.username_pw_set(username, password or "")
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        logging.info(
            "Gateway(MQTT) connecting to %s:%s prefix=%s",
            self.broker, self.port, self.prefix,
        )
        try:
            self._client.connect(self.broker, self.port, keepalive=30)
        except Exception as e:
            raise GatewayConnectionError(
                f"could not reach gateway broker {self.broker}:{self.port}: {e}"
            )
        self._client.loop_start()

        # Block briefly so the caller can fall back to simulation if the broker
        # is unreachable -- mirrors how _open_serial() fails fast.
        if not self._connected.wait(timeout=connect_timeout):
            self.close()
            raise GatewayConnectionError(
                f"timed out connecting to gateway broker "
                f"{self.broker}:{self.port}"
            )

    # ------------------------------------------------------------------
    # MQTT callbacks
    # ------------------------------------------------------------------
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        # paho VERSION2 passes a ReasonCode object; 0 / "Success" == OK.
        ok = (getattr(reason_code, "value", reason_code) == 0)
        if ok:
            client.subscribe(self.rx_topic, qos=0)
            self._connected.set()
            logging.info(
                "Gateway(MQTT) connected; subscribed to %s", self.rx_topic
            )
        else:
            logging.error("Gateway(MQTT) connect failed: %s", reason_code)

    def _on_disconnect(self, client, userdata, *args):
        self._connected.clear()
        if not self._closed:
            logging.warning("Gateway(MQTT) disconnected; will auto-reconnect")

    def _on_message(self, client, userdata, msg):
        if msg.topic != self.rx_topic:
            return
        frame = self._extract_frame(msg.payload)
        if frame is None:
            return
        # Re-append the newline the gateway stripped so downstream parsers that
        # look for '\n' terminators behave exactly as with raw serial.
        data = frame.encode("utf-8", errors="ignore") + b"\n"
        with self._rx_lock:
            self._rx_buf.extend(data)

    @staticmethod
    def _extract_frame(payload):
        """Pull the ASCII frame out of an /rx payload.

        Accepts the gateway's JSON form ``{"command":"..."}`` and also a bare
        plain-text frame, for robustness against future gateway changes.
        """
        try:
            text = payload.decode("utf-8", errors="ignore")
        except Exception:
            return None
        text = text.strip()
        if not text:
            return None
        if text[0] == "{":
            try:
                doc = json.loads(text)
            except Exception:
                return None
            cmd = doc.get("command")
            if cmd is None:
                return None
            return str(cmd)
        # Plain frame fallback.
        return text

    # ------------------------------------------------------------------
    # pyserial-compatible surface
    # ------------------------------------------------------------------
    def write(self, data):
        """Publish a raw frame to ``<prefix>/send``.

        ``data`` is bytes (as the existing code passes ``cmd.encode()``).
        The gateway forwards the payload to the bus verbatim, so we publish the
        exact bytes -- including the trailing newline -- unchanged.
        """
        if isinstance(data, str):
            data = data.encode()
        if not self._connected.is_set():
            # The broker is down / mid-reconnect. paho will silently queue (or
            # drop) the publish, so the frame may never reach the display and
            # the caller gets no signal. Surface the loss -- it matters most
            # during calibration / EEPROM writes, where a dropped frame leaves
            # the module in an inconsistent state.
            logging.warning(
                "Gateway(MQTT) not connected; command may not reach display: %r",
                data,
            )
        # paho accepts bytes payloads directly.
        info = self._client.publish(self.send_topic, payload=data, qos=0)
        rc = getattr(info, "rc", 0)
        if rc != 0:
            logging.warning(
                "Gateway(MQTT) publish failed (rc=%s); command not sent: %r",
                rc, data,
            )
        return len(data)

    def flush(self):
        # Publishing is synchronous from the caller's perspective; nothing to do.
        return None

    def reset_input_buffer(self):
        with self._rx_lock:
            self._rx_buf.clear()

    # reset_output_buffer is referenced by some pyserial code paths; provide it
    # for completeness even though splitflap-os doesn't call it.
    def reset_output_buffer(self):
        return None

    @property
    def in_waiting(self):
        with self._rx_lock:
            return len(self._rx_buf)

    def read(self, size=1):
        with self._rx_lock:
            if size <= 0:
                return b""
            chunk = bytes(self._rx_buf[:size])
            del self._rx_buf[:size]
            return chunk

    @property
    def is_open(self):
        return self._connected.is_set()

    def close(self):
        self._closed = True
        try:
            self._client.loop_stop()
        except Exception:
            pass
        try:
            self._client.disconnect()
        except Exception:
            pass
