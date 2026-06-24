"""Universal Split-Flap Firmware discovery, provisioning, and diagnostics.

Splitflap OS has one shared RS-485 receive buffer. Any operation that expects a
reply must own the serial lock for its full write/read transaction; otherwise an
idle observer can consume bytes intended for that operation. This manager
follows the same rule as the existing calibration code:

* the passive reader only observes unsolicited traffic while the bus is idle;
* Universal Firmware commands that expect replies write and read under the
  shared serial lock, then feed those bytes through the same parser.
"""

from collections import deque
import logging
import re
import threading
import time


SERIAL_RE = re.compile(r"^[0-9A-F]{20}$")
ADVERTISEMENT_RE = re.compile(r"^mXadv:([0-9A-Fa-f]{20})$")
# Firmware examples exist with and without the colon after "mXack".
ACK_RE = re.compile(r"^mXack:?([0-9A-Fa-f]{20}):(\d{1,3})$")
VERSION_RE = re.compile(
    r"^m(\d+)v:([^:\s]+)(?::(\d+):([0-9A-Fa-f]{20}))?$"
)
SNAPSHOT_RE = re.compile(
    r"^m(\d+)Q:(\d+):(\d+):(\d+):(\d+):(-?\d+)$"
)
HALL_RE = re.compile(
    r"^m(\d+)T:(\d+):(\d+):(\d+)(?::(\d+))?$"
)
MECHANICAL_RE = re.compile(r"^m(\d+)M:(.*)$")


class UniversalFirmwareError(RuntimeError):
    """A user-facing Universal Firmware operation error."""


def parse_firmware_number(value):
    """Return the numeric part of a firmware version such as ``v29``."""
    match = re.search(r"\d+", str(value or ""))
    return int(match.group(0)) if match else 0


def parse_universal_line(line):
    """Parse one RS-485 response line into a normalized event dictionary."""
    line = str(line or "").strip()
    if not line:
        return None

    match = ADVERTISEMENT_RE.match(line)
    if match:
        return {"type": "advertisement", "serial": match.group(1).upper()}

    match = ACK_RE.match(line)
    if match:
        module_id = int(match.group(2))
        if module_id <= 254:
            return {
                "type": "ack",
                "serial": match.group(1).upper(),
                "id": module_id,
            }
        return None

    match = VERSION_RE.match(line)
    if match:
        address = int(match.group(1))
        reported_id = int(match.group(3)) if match.group(3) is not None else address
        serial_number = match.group(4)
        return {
            "type": "version",
            "id": address,
            "reported_id": reported_id,
            "firmware": match.group(2),
            "serial": serial_number.upper() if serial_number else "",
            "universal": bool(serial_number),
        }

    match = SNAPSHOT_RE.match(line)
    if match:
        return {
            "type": "snapshot",
            "id": int(match.group(1)),
            "reset_cause": int(match.group(2)),
            "boot_count": int(match.group(3)),
            "vcc_mv": int(match.group(4)),
            "eeprom_ok": int(match.group(5)) == 1,
            "current_index": int(match.group(6)),
        }

    match = HALL_RE.match(line)
    if match:
        return {
            "type": "hall",
            "id": int(match.group(1)),
            "code": int(match.group(2)),
            "rising_edges": int(match.group(3)),
            "active_samples": int(match.group(4)),
            "falling_edges": int(match.group(5)) if match.group(5) is not None else None,
        }

    match = MECHANICAL_RE.match(line)
    if match:
        values = match.group(2).split(":")
        if len(values) < 6:
            return None
        try:
            event = {
                "type": "mechanical",
                "id": int(match.group(1)),
                "code": int(values[0]),
                "minimum": int(values[1]),
                "maximum": int(values[2]),
                "spread_tenths_percent": int(values[3]),
                "gate_active": int(values[4]),
                "gate_span": int(values[5]),
                "average_magnet_width": None,
                "revolutions": [],
            }
            if len(values) >= 7 and values[6] != "":
                event["average_magnet_width"] = int(values[6])
            if len(values) >= 8 and values[7]:
                event["revolutions"] = [
                    int(value) for value in values[7].split(",") if value
                ]
            return event
        except ValueError:
            return None

    return {"type": "other", "line": line}


class UniversalFirmwareManager:
    """Observe and operate Universal Firmware modules on a shared serial bus."""

    ADVERTISEMENT_TTL_SECONDS = 45
    EVENT_HISTORY_SIZE = 256

    def __init__(self, get_serial, serial_lock, get_sim_mode=None):
        self._get_serial = get_serial
        self._serial_lock = serial_lock
        self._get_sim_mode = get_sim_mode or (lambda: False)
        self._state_lock = threading.RLock()
        self._condition = threading.Condition(self._state_lock)
        self._rx_lock = threading.Lock()
        self._modules = {}
        self._unprovisioned = {}
        self._events = deque(maxlen=self.EVENT_HISTORY_SIZE)
        self._event_sequence = 0
        self._rx_buffer = b""
        self._serial_identity = None
        self._scan_deadline = 0.0
        self._last_scan_at = 0.0
        self._last_cleanup_at = 0.0
        self._stop_event = threading.Event()
        self._reader_thread = None

    def start(self):
        if self._reader_thread and self._reader_thread.is_alive():
            return
        self._stop_event.clear()
        self._reader_thread = threading.Thread(
            target=self._reader_loop,
            name="universal-firmware-reader",
            daemon=True,
        )
        self._reader_thread.start()

    def ensure_started(self):
        """Start passive observation on demand."""
        self.start()

    def stop(self):
        self._stop_event.set()
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=1.0)

    def reset(self):
        """Clear bus-specific state, for example after changing serial ports."""
        with self._rx_lock:
            self._rx_buffer = b""
            with self._condition:
                self._modules.clear()
                self._unprovisioned.clear()
                self._events.clear()
                self._event_sequence = 0
                self._serial_identity = None
                self._scan_deadline = 0.0
                self._last_scan_at = 0.0
                self._last_cleanup_at = 0.0
                self._condition.notify_all()

    def _reader_loop(self):
        while not self._stop_event.is_set():
            serial_port = self._get_serial()
            if (
                serial_port is None
                or self._get_sim_mode()
                or getattr(serial_port, "is_open", True) is False
            ):
                time.sleep(0.1)
                continue

            identity = id(serial_port)
            if identity != self._serial_identity:
                self._serial_identity = identity
                with self._rx_lock:
                    self._rx_buffer = b""

            acquired = False
            try:
                acquired = self._serial_lock.acquire(timeout=0.01)
                if not acquired:
                    time.sleep(0.01)
                    continue
                waiting = int(getattr(serial_port, "in_waiting", 0) or 0)
                chunk = serial_port.read(waiting) if waiting > 0 else b""
            except Exception as exc:
                logging.debug("Universal Firmware serial observer: %s", exc)
                chunk = b""
            finally:
                if acquired:
                    self._serial_lock.release()

            if chunk:
                self.feed_bytes(chunk)
            else:
                self._cleanup_if_due()
                time.sleep(0.01)

    def feed_bytes(self, chunk):
        """Feed raw serial bytes into the line parser (also useful in tests)."""
        if not chunk:
            return
        with self._rx_lock:
            self._rx_buffer += bytes(chunk)
            if len(self._rx_buffer) > 8192 and b"\n" not in self._rx_buffer:
                self._rx_buffer = b""
                return
            while b"\n" in self._rx_buffer:
                raw_line, self._rx_buffer = self._rx_buffer.split(b"\n", 1)
                line = raw_line.decode("ascii", errors="ignore").strip()
                if line:
                    self.handle_line(line)

    @staticmethod
    def _consume_lines(buffer, chunk):
        """Return ``(remaining_buffer, decoded_lines)`` for a serial chunk."""
        buffer += bytes(chunk or b"")
        if len(buffer) > 8192 and b"\n" not in buffer:
            return b"", []

        lines = []
        while b"\n" in buffer:
            raw_line, buffer = buffer.split(b"\n", 1)
            line = raw_line.decode("ascii", errors="ignore").strip()
            if line:
                lines.append(line)
        return buffer, lines

    def _prune_expired_unprovisioned_locked(self, now):
        expired = [
            serial_number
            for serial_number, item in self._unprovisioned.items()
            if now - item["last_seen"] > self.ADVERTISEMENT_TTL_SECONDS
        ]
        for serial_number in expired:
            self._unprovisioned.pop(serial_number, None)

    def _cleanup_if_due(self):
        now = time.time()
        with self._condition:
            if now - self._last_cleanup_at < 5.0:
                return
            self._last_cleanup_at = now
            self._prune_expired_unprovisioned_locked(now)

    def handle_line(self, line):
        """Record one decoded bus line and update module discovery state."""
        event = parse_universal_line(line)
        if event is None:
            return None

        now = time.time()
        with self._condition:
            self._prune_expired_unprovisioned_locked(now)
            event = dict(event)
            self._event_sequence += 1
            event["sequence"] = self._event_sequence
            event["received_at"] = now
            event["line"] = str(line).strip()
            self._events.append(event)

            if event["type"] == "advertisement":
                serial_number = event["serial"]
                entry = self._unprovisioned.get(serial_number, {
                    "serial": serial_number,
                    "first_seen": now,
                })
                entry["last_seen"] = now
                self._unprovisioned[serial_number] = entry

            elif event["type"] == "ack":
                serial_number = event["serial"]
                module_id = event["id"]
                self._unprovisioned.pop(serial_number, None)
                module = self._modules.get(module_id, {})
                module.update({
                    "id": module_id,
                    "serial": serial_number,
                    "provisioned": True,
                    "acknowledged": True,
                    "last_seen": now,
                })
                self._modules[module_id] = module

            elif event["type"] == "version" and event["universal"]:
                module_id = event["reported_id"]
                module = self._modules.get(module_id, {})
                module.update({
                    "id": module_id,
                    "serial": event["serial"],
                    "firmware": event["firmware"],
                    "firmware_number": parse_firmware_number(event["firmware"]),
                    "provisioned": module_id != 255,
                    "acknowledged": module.get("acknowledged", False),
                    "last_seen": now,
                })
                if module_id == 255:
                    serial_number = event["serial"]
                    entry = self._unprovisioned.get(serial_number, {
                        "serial": serial_number,
                        "first_seen": now,
                    })
                    entry["last_seen"] = now
                    self._unprovisioned[serial_number] = entry
                else:
                    self._unprovisioned.pop(event["serial"], None)
                    self._modules[module_id] = module

            elif event["type"] in ("snapshot", "hall", "mechanical"):
                module = self._modules.get(event["id"])
                if module is not None:
                    module["last_seen"] = now
                    diagnostics = module.setdefault("diagnostics", {})
                    diagnostics[event["type"]] = {
                        key: value for key, value in event.items()
                        if key not in ("line", "sequence")
                    }

            self._condition.notify_all()
        return event

    def _connected(self):
        serial_port = self._get_serial()
        return bool(
            serial_port is not None
            and getattr(serial_port, "is_open", True) is not False
        )

    def _require_live_serial(self):
        if self._get_sim_mode():
            raise UniversalFirmwareError(
                "Switch the display to LIVE mode before using provisioning."
            )
        serial_port = self._get_serial()
        if serial_port is None or getattr(serial_port, "is_open", True) is False:
            raise UniversalFirmwareError("No serial hardware is connected.")
        return serial_port

    @staticmethod
    def _frame(command):
        return command if command.endswith("\n") else command + "\n"

    @staticmethod
    def _read_waiting(serial_port):
        waiting = int(getattr(serial_port, "in_waiting", 0) or 0)
        return serial_port.read(waiting) if waiting > 0 else b""

    def _write_unlocked(self, serial_port, command):
        frame = self._frame(command)
        serial_port.write(frame.encode("ascii"))
        serial_port.flush()

    def _write(self, command):
        self._require_live_serial()
        frame = command if command.endswith("\n") else command + "\n"
        try:
            with self._serial_lock:
                serial_port = self._get_serial()
                if serial_port is None:
                    raise UniversalFirmwareError("The serial connection was closed.")
                serial_port.write(frame.encode("ascii"))
                serial_port.flush()
        except UniversalFirmwareError:
            raise
        except Exception as exc:
            raise UniversalFirmwareError("Serial write failed: {}".format(exc))

    def _transaction(self, command, timeout, predicate=None, drain_before=True):
        """Write a command and collect its responses while owning the bus.

        ``predicate`` is optional. When provided, the transaction returns the
        first parsed event that matches it. Without a predicate, the transaction
        reads until ``timeout`` expires and returns ``None`` after feeding all
        complete response lines through ``handle_line``.
        """
        self._require_live_serial()
        deadline = time.monotonic() + max(0.0, float(timeout or 0.0))
        local_buffer = b""

        try:
            with self._serial_lock:
                serial_port = self._require_live_serial()
                if drain_before and hasattr(serial_port, "reset_input_buffer"):
                    try:
                        serial_port.reset_input_buffer()
                    except Exception:
                        pass

                self._write_unlocked(serial_port, command)

                while True:
                    if self._stop_event.is_set():
                        return None
                    chunk = self._read_waiting(serial_port)
                    if chunk:
                        matched_event = None
                        local_buffer, lines = self._consume_lines(local_buffer, chunk)
                        for line in lines:
                            event = self.handle_line(line)
                            if (
                                matched_event is None
                                and event is not None
                                and predicate
                                and predicate(event)
                            ):
                                matched_event = dict(event)
                        if matched_event is not None:
                            return matched_event

                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return None
                    time.sleep(min(0.01, remaining))
        except UniversalFirmwareError:
            raise
        except Exception as exc:
            raise UniversalFirmwareError("Serial transaction failed: {}".format(exc))

    def status(self, module_limit=45):
        now = time.time()
        with self._condition:
            modules = []
            for module_id in sorted(self._modules):
                module = dict(self._modules[module_id])
                module["online"] = now - module.get("last_seen", 0) <= 60
                modules.append(module)

            unprovisioned = []
            for serial_number in sorted(self._unprovisioned):
                item = dict(self._unprovisioned[serial_number])
                if now - item["last_seen"] > self.ADVERTISEMENT_TTL_SECONDS:
                    continue
                item["age_seconds"] = max(0, int(now - item["last_seen"]))
                unprovisioned.append(item)

            used_ids = {module["id"] for module in modules}
            preferred_limit = max(1, min(int(module_limit or 45), 255))
            suggested_id = next(
                (module_id for module_id in range(preferred_limit)
                 if module_id not in used_ids),
                next((module_id for module_id in range(255)
                      if module_id not in used_ids), None),
            )
            return {
                "connected": self._connected(),
                "live": not self._get_sim_mode(),
                "has_universal": bool(modules),
                "modules": modules,
                "unprovisioned": unprovisioned,
                "suggested_id": suggested_id,
                "scan_in_progress": time.monotonic() < self._scan_deadline,
                "last_scan_at": self._last_scan_at,
            }

    def scan(self, maximum_id):
        maximum_id = max(0, min(int(maximum_id), 254))
        self._require_live_serial()
        timeout = 0.75 + ((maximum_id + 1) * 0.1)
        with self._condition:
            self._last_scan_at = time.time()
            self._scan_deadline = time.monotonic() + timeout

        thread = threading.Thread(
            target=self._scan_worker,
            args=(maximum_id, timeout),
            name="universal-firmware-scan",
            daemon=True,
        )
        thread.start()

    def _scan_worker(self, maximum_id, timeout):
        try:
            self._transaction("m*v0-{}".format(maximum_id), timeout=timeout)
        except UniversalFirmwareError as exc:
            logging.warning("Universal Firmware scan failed: %s", exc)
        finally:
            with self._condition:
                self._scan_deadline = 0.0
                self._condition.notify_all()

    @staticmethod
    def validate_serial(serial_number):
        serial_number = str(serial_number or "").strip().upper()
        if not SERIAL_RE.match(serial_number):
            raise UniversalFirmwareError(
                "Serial number must be exactly 20 hexadecimal characters."
            )
        return serial_number

    @staticmethod
    def validate_id(module_id):
        try:
            module_id = int(module_id)
        except (TypeError, ValueError):
            raise UniversalFirmwareError("Module ID must be a number from 0 to 254.")
        if module_id < 0 or module_id > 254:
            raise UniversalFirmwareError("Module ID must be between 0 and 254.")
        return module_id

    def home_by_serial(self, serial_number):
        serial_number = self.validate_serial(serial_number)
        self._write("mXH{}".format(serial_number))

    def home_module(self, module_id):
        module_id = self.validate_id(module_id)
        self._write("m{}h".format(module_id))

    def provision(self, serial_number, module_id, timeout=2.0):
        serial_number = self.validate_serial(serial_number)
        module_id = self.validate_id(module_id)
        with self._condition:
            existing = self._modules.get(module_id)
            if existing and existing.get("serial") != serial_number:
                raise UniversalFirmwareError(
                    "Module ID {} is already assigned to {}.".format(
                        module_id, existing.get("serial", "another module")
                    )
                )

        acknowledgement = self._transaction(
            "mXI{}:{}".format(serial_number, module_id),
            timeout=timeout,
            predicate=lambda event: (
                event["type"] == "ack"
                and event["serial"] == serial_number
                and event["id"] == module_id
            ),
        )
        if acknowledgement:
            # Query after assignment so the inventory gains its firmware version.
            time.sleep(0.05)
            self._transaction(
                "m{}v".format(module_id),
                timeout=1.0,
                predicate=lambda event: (
                    event["type"] == "version"
                    and event.get("reported_id") == module_id
                    and event.get("universal")
                ),
            )
        return acknowledgement is not None

    def deprovision(self, module_id):
        module_id = self.validate_id(module_id)
        self._write("m{}R".format(module_id))
        with self._condition:
            self._modules.pop(module_id, None)

    def deprovision_all(self):
        self._write("m*R")
        with self._condition:
            self._modules.clear()

    def run_diagnostic(self, module_id, kind="snapshot", revolutions=5):
        module_id = self.validate_id(module_id)
        kind = str(kind or "snapshot").lower()
        if kind not in ("snapshot", "hall", "mechanical"):
            raise UniversalFirmwareError("Unknown diagnostic test.")

        with self._condition:
            module = self._modules.get(module_id)
            firmware_number = int((module or {}).get("firmware_number", 0))
            if firmware_number and firmware_number < 26:
                raise UniversalFirmwareError(
                    "Module {} needs Universal Firmware v26 or newer for diagnostics."
                    .format(module_id)
                )

        if kind == "snapshot":
            command = "m{}Q".format(module_id)
            timeout = 3.0
        elif kind == "hall":
            command = "m{}T".format(module_id)
            timeout = 35.0
        else:
            try:
                revolutions = int(revolutions)
            except (TypeError, ValueError):
                revolutions = 5
            revolutions = max(5, min(revolutions, 20))
            command = (
                "m{}M{}".format(module_id, revolutions)
                if firmware_number >= 29
                else "m{}M".format(module_id)
            )
            timeout = 20.0 + (revolutions * 7.0)

        result = self._transaction(
            command,
            timeout=timeout,
            predicate=lambda event: (
                event["type"] == kind
                and event.get("id") == module_id
            ),
        )
        if result is None:
            raise UniversalFirmwareError(
                "Module {} did not answer the {} test.".format(module_id, kind)
            )
        return {
            key: value for key, value in result.items()
            if key not in ("line", "sequence")
        }
