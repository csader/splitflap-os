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

    def write(self, payload):
        self.writes.append(payload)
        return len(payload)

    def flush(self):
        pass


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

    def test_commands_match_provision_py_examples(self):
        self.manager.home_by_serial(SERIAL_NUMBER)
        self.manager.home_module(38)
        self.manager.deprovision(38)
        self.manager.deprovision_all()
        self.manager.scan(44)

        self.assertEqual(
            self.serial.writes,
            [
                ("mXH" + SERIAL_NUMBER + "\n").encode("ascii"),
                b"m38h\n",
                b"m38R\n",
                b"m*R\n",
                b"m*v0-44\n",
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
        def acknowledge():
            deadline = time.time() + 1
            while not self.serial.writes and time.time() < deadline:
                time.sleep(0.005)
            self.manager.handle_line("mXack" + SERIAL_NUMBER + ":7")

        thread = threading.Thread(target=acknowledge)
        thread.start()
        acknowledged = self.manager.provision(SERIAL_NUMBER, 7, timeout=0.5)
        thread.join()

        self.assertTrue(acknowledged)
        self.assertEqual(
            self.serial.writes,
            [
                ("mXI" + SERIAL_NUMBER + ":7\n").encode("ascii"),
                b"m7v\n",
            ],
        )

    def test_mechanical_count_is_only_sent_to_v29_or_newer(self):
        self.manager.handle_line("m3v:28:3:" + SERIAL_NUMBER)

        def answer_v28():
            deadline = time.time() + 1
            while not self.serial.writes and time.time() < deadline:
                time.sleep(0.005)
            self.manager.handle_line("m3M:0:4096:4096:0:168:4500")

        thread = threading.Thread(target=answer_v28)
        thread.start()
        result = self.manager.run_diagnostic(3, "mechanical", revolutions=8)
        thread.join()
        self.assertEqual(self.serial.writes[-1], b"m3M\n")
        self.assertEqual(result["type"], "mechanical")

        self.serial.writes.clear()
        self.manager.handle_line("m3v:29:3:" + SERIAL_NUMBER)

        def answer_v29():
            deadline = time.time() + 1
            while not self.serial.writes and time.time() < deadline:
                time.sleep(0.005)
            self.manager.handle_line("m3M:0:4096:4096:0:168:4500")

        thread = threading.Thread(target=answer_v29)
        thread.start()
        self.manager.run_diagnostic(3, "mechanical", revolutions=8)
        thread.join()
        self.assertEqual(self.serial.writes[-1], b"m3M8\n")


if __name__ == "__main__":
    unittest.main()
