import pathlib
import sys
import threading
import time
import unittest


SERVER_DIR = pathlib.Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(SERVER_DIR))

from hardware.universal_firmware import (  # noqa: E402
    UniversalFirmwareManager,
    parse_universal_line,
)


SERIAL_NUMBER = "A3F24C0018E7D29B3F01"


class FakeSerial:
    def __init__(self):
        self.is_open = True
        self.writes = []
        self.write_hook = None
        self.read_count = 0
        self._rx = bytearray()
        self._lock = threading.Lock()

    def write(self, payload):
        self.writes.append(payload)
        if self.write_hook:
            self.write_hook(payload, self)
        return len(payload)

    def flush(self):
        pass

    def queue_read(self, payload):
        if isinstance(payload, str):
            payload = payload.encode("ascii")
        with self._lock:
            self._rx.extend(payload)

    @property
    def in_waiting(self):
        with self._lock:
            return len(self._rx)

    def read(self, size=1):
        with self._lock:
            self.read_count += 1
            chunk = bytes(self._rx[:size])
            del self._rx[:size]
            return chunk

    def reset_input_buffer(self):
        with self._lock:
            self._rx.clear()


class ProtocolParserTests(unittest.TestCase):
    def test_parses_advertisement_and_both_ack_formats(self):
        self.assertEqual(
            parse_universal_line("mXadv:" + SERIAL_NUMBER),
            {"type": "advertisement", "serial": SERIAL_NUMBER},
        )
        expected = {"type": "ack", "serial": SERIAL_NUMBER, "id": 38}
        self.assertEqual(
            parse_universal_line("mXack:" + SERIAL_NUMBER + ":38"),
            expected,
        )
        self.assertEqual(
            parse_universal_line("mXack" + SERIAL_NUMBER + ":38"),
            expected,
        )

    def test_parses_current_version_and_diagnostic_frames(self):
        version = parse_universal_line(
            "m38v:29:38:" + SERIAL_NUMBER
        )
        self.assertTrue(version["universal"])
        self.assertEqual(version["reported_id"], 38)
        self.assertEqual(version["firmware"], "29")

        snapshot = parse_universal_line("m38Q:8:12:4930:1:-1")
        self.assertEqual(snapshot["reset_cause"], 8)
        self.assertEqual(snapshot["current_index"], -1)

        hall = parse_universal_line("m38T:0:1:168:1")
        self.assertEqual(hall["falling_edges"], 1)

        mechanical = parse_universal_line(
            "m38M:0:4095:4097:1:168:4500:167:4096,4095,4097,4096,4096"
        )
        self.assertEqual(mechanical["average_magnet_width"], 167)
        self.assertEqual(mechanical["revolutions"], [4096, 4095, 4097, 4096, 4096])


class ManagerCommandTests(unittest.TestCase):
    def setUp(self):
        self.serial = FakeSerial()
        self.manager = UniversalFirmwareManager(
            get_serial=lambda: self.serial,
            serial_lock=threading.Lock(),
            get_sim_mode=lambda: False,
        )

    def tearDown(self):
        self.manager.stop()

    def wait_for_writes(self, count, timeout=1.0):
        deadline = time.time() + timeout
        while len(self.serial.writes) < count and time.time() < deadline:
            time.sleep(0.005)
        self.assertGreaterEqual(len(self.serial.writes), count)

    def test_commands_match_provision_py_examples(self):
        self.manager.home_by_serial(SERIAL_NUMBER)
        self.manager.home_module(38)
        self.manager.deprovision(38)
        self.manager.deprovision_all()
        self.manager.scan(0)
        self.wait_for_writes(5)

        self.assertEqual(
            self.serial.writes[:5],
            [
                ("mXH" + SERIAL_NUMBER + "\n").encode("ascii"),
                b"m38h\n",
                b"m38R\n",
                b"m*R\n",
                b"m*v0-0\n",
            ],
        )

    def test_fragmented_serial_reads_are_reassembled(self):
        self.manager.feed_bytes(b"mXadv:A3F24C0018E7")
        self.manager.feed_bytes(b"D29B3F01\nm4v:29:4:B10055")
        self.manager.feed_bytes(b"FFA3C2918D7E44\n")

        status = self.manager.status(module_limit=45)
        self.assertEqual(
            [item["serial"] for item in status["unprovisioned"]],
            [SERIAL_NUMBER],
        )
        self.assertEqual(status["modules"][0]["id"], 4)
        self.assertEqual(status["modules"][0]["firmware_number"], 29)

    def test_provision_waits_for_ack_and_queries_version(self):
        def respond(payload, serial_port):
            if payload == ("mXI" + SERIAL_NUMBER + ":7\n").encode("ascii"):
                serial_port.queue_read("mXack" + SERIAL_NUMBER + ":7\n")
            elif payload == b"m7v\n":
                serial_port.queue_read("m7v:29:7:" + SERIAL_NUMBER + "\n")

        self.serial.write_hook = respond
        acknowledged = self.manager.provision(SERIAL_NUMBER, 7, timeout=0.5)

        self.assertTrue(acknowledged)
        self.assertEqual(
            self.serial.writes,
            [
                ("mXI" + SERIAL_NUMBER + ":7\n").encode("ascii"),
                b"m7v\n",
            ],
        )
        status = self.manager.status(module_limit=45)
        self.assertEqual(status["modules"][0]["id"], 7)
        self.assertEqual(status["modules"][0]["firmware_number"], 29)

    def test_mechanical_count_is_only_sent_to_v29_or_newer(self):
        self.manager.handle_line("m3v:28:3:" + SERIAL_NUMBER)

        def answer_mechanical(payload, serial_port):
            if payload in (b"m3M\n", b"m3M8\n"):
                serial_port.queue_read("m3M:0:4096:4096:0:168:4500\n")

        self.serial.write_hook = answer_mechanical
        result = self.manager.run_diagnostic(3, "mechanical", revolutions=8)
        self.assertEqual(self.serial.writes[-1], b"m3M\n")
        self.assertEqual(result["type"], "mechanical")

        self.serial.writes.clear()
        self.manager.handle_line("m3v:29:3:" + SERIAL_NUMBER)

        self.manager.run_diagnostic(3, "mechanical", revolutions=8)
        self.assertEqual(self.serial.writes[-1], b"m3M8\n")

    def test_transaction_owns_the_serial_lock_until_response_is_read(self):
        lock = threading.Lock()
        self.manager = UniversalFirmwareManager(
            get_serial=lambda: self.serial,
            serial_lock=lock,
            get_sim_mode=lambda: False,
        )

        def respond(payload, serial_port):
            self.assertTrue(lock.locked())
            serial_port.queue_read("m4Q:0:2:3312:1:12\n")

        self.serial.write_hook = respond
        result = self.manager.run_diagnostic(4, "snapshot")

        self.assertEqual(result["type"], "snapshot")
        self.assertEqual(result["vcc_mv"], 3312)
        self.assertGreater(self.serial.read_count, 0)

    def test_passive_reader_backs_off_while_another_transaction_owns_lock(self):
        lock = threading.Lock()
        self.manager = UniversalFirmwareManager(
            get_serial=lambda: self.serial,
            serial_lock=lock,
            get_sim_mode=lambda: False,
        )
        self.serial.queue_read("mXadv:" + SERIAL_NUMBER + "\n")

        lock.acquire()
        try:
            self.manager.ensure_started()
            time.sleep(0.05)
            self.assertEqual(self.serial.read_count, 0)
        finally:
            lock.release()

        deadline = time.time() + 1
        while self.serial.read_count == 0 and time.time() < deadline:
            time.sleep(0.01)

        self.assertGreater(self.serial.read_count, 0)
        self.assertEqual(
            [item["serial"] for item in self.manager.status()["unprovisioned"]],
            [SERIAL_NUMBER],
        )

    def test_status_filters_expired_advertisements_without_mutating_state(self):
        self.manager.handle_line("mXadv:" + SERIAL_NUMBER)
        with self.manager._condition:
            self.manager._unprovisioned[SERIAL_NUMBER]["last_seen"] -= (
                self.manager.ADVERTISEMENT_TTL_SECONDS + 1
            )

        status = self.manager.status(module_limit=45)

        self.assertEqual(status["unprovisioned"], [])
        with self.manager._condition:
            self.assertIn(SERIAL_NUMBER, self.manager._unprovisioned)


if __name__ == "__main__":
    unittest.main()
