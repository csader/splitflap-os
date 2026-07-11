"""Regression tests for GatewayTransport frame decoding.

The RS485 bus is single-byte Windows-1252 (cp1252): one displayed glyph is one
byte. A frame read back from the gateway -- most importantly a module's
``A``-command character-map response -- can therefore carry raw high bytes
(0x80-0xFF) that are *invalid* standalone UTF-8. The RX path must preserve those
bytes verbatim so the downstream ``.decode('cp1252')`` in app.get_module_char_map
recovers the real characters. These tests lock in that byte-transparent behaviour
(previously the code decoded/re-encoded as UTF-8 with errors="ignore", which
silently dropped every extended character).
"""

import pathlib
import sys
import unittest


SERVER_DIR = pathlib.Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(SERVER_DIR))

from gateway_transport import GatewayTransport  # noqa: E402


# A char map with real cp1252 extended glyphs (no " or \\, which the physical
# reel aliases to 'q' anyway and which would need JSON escaping).
CHAR_MAP = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789éöüàçñ€£¥"
FRAME = "m05A:64:" + CHAR_MAP           # module's A-command response frame
FRAME_BYTES = FRAME.encode("cp1252")    # the exact bytes on the bus


class ExtractFrameTests(unittest.TestCase):
    def _recover(self, frame):
        # Mirrors _on_message: what lands in the RX buffer is the frame encoded
        # latin-1; get_module_char_map later slices it and decodes cp1252.
        self.assertIsNotNone(frame)
        return frame.encode("latin-1")

    def test_json_form_preserves_extended_bytes(self):
        # The gateway's {"command": "..."} form with raw high bytes in the string.
        payload = b'{"command": "' + FRAME_BYTES + b'"}'
        recovered = self._recover(GatewayTransport._extract_frame(payload))
        self.assertEqual(recovered, FRAME_BYTES)
        # Round-trips to the original characters via the downstream cp1252 decode.
        self.assertEqual(recovered.decode("cp1252"), FRAME)

    def test_bare_frame_preserves_extended_bytes(self):
        # Plain-text fallback (no JSON wrapper).
        recovered = self._recover(GatewayTransport._extract_frame(FRAME_BYTES))
        self.assertEqual(recovered.decode("cp1252"), FRAME)

    def test_plain_ascii_unaffected(self):
        payload = b'{"command": "m00-A"}'
        self.assertEqual(GatewayTransport._extract_frame(payload), "m00-A")

    def test_utf8_would_have_corrupted(self):
        # Documents the bug being fixed: the old utf-8/errors=ignore path drops
        # the lone high bytes, losing every extended glyph.
        lossy = FRAME_BYTES.decode("utf-8", errors="ignore")
        self.assertLess(len(lossy), len(FRAME))
        self.assertNotIn("é", lossy)
        self.assertNotIn("€", lossy)


if __name__ == "__main__":
    unittest.main()
