import pathlib
import sys
import unittest


SERVER_DIR = pathlib.Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(SERVER_DIR))

from tuning import build_tuning_adjust_commands  # noqa: E402


class TuningCommandTests(unittest.TestCase):
    def test_adjustment_is_saved_and_immediately_previewed(self):
        self.assertEqual(
            build_tuning_adjust_commands(3, 51, 2618, 4096),
            ("m03w51:2618", "m03g2618"),
        )

    def test_preview_uses_absolute_step_position_not_character_index(self):
        _, preview_command = build_tuning_adjust_commands(3, 51, 2618, 4096)
        self.assertEqual(preview_command, "m03g2618")
        self.assertNotEqual(preview_command, "m03g51")

    def test_allows_last_valid_step_for_calibration(self):
        self.assertEqual(
            build_tuning_adjust_commands(3, 51, 4095, 4096),
            ("m03w51:4095", "m03g4095"),
        )

    def test_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            build_tuning_adjust_commands(-1, 10, 500, 4096)
        with self.assertRaises(ValueError):
            build_tuning_adjust_commands(1, 64, 500, 4096)
        with self.assertRaises(ValueError):
            build_tuning_adjust_commands(1, 10, 500, 0)
        with self.assertRaises(ValueError):
            build_tuning_adjust_commands(1, 10, -1, 4096)
        with self.assertRaises(ValueError):
            build_tuning_adjust_commands(1, 10, 4096, 4096)


if __name__ == "__main__":
    unittest.main()
