import tempfile
import unittest
from pathlib import Path

from common.frame_config import DEFAULT_FRAME_CONFIG
from common.frame_layout import pilot_cells_with_bits
from common.png_reader import read_grayscale_png
from common.png_writer import write_grayscale_png
from receiver.calibration import estimate_ook_calibration, validate_markers
from receiver.decoder import decode_static_frame, sample_grid_levels
from transmitter.generator import generate_static_frame


def _apply_linear_levels(pixels: list[list[int]], dark_offset: int, scale: float) -> list[list[int]]:
    shifted: list[list[int]] = []
    for row in pixels:
        shifted.append([max(0, min(255, int(dark_offset + value * scale))) for value in row])
    return shifted


class PilotCalibrationTests(unittest.TestCase):
    def test_pilots_include_black_and_white_references(self):
        expected_bits = [bit for _, bit in pilot_cells_with_bits(DEFAULT_FRAME_CONFIG)]

        self.assertIn(0, expected_bits)
        self.assertIn(1, expected_bits)

    def test_calibration_uses_pilots_and_validates_markers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "frame.png"
            generate_static_frame("Hola mundo", output_path=output)
            grid = sample_grid_levels(read_grayscale_png(output), DEFAULT_FRAME_CONFIG)

            calibration = estimate_ook_calibration(grid)

            self.assertEqual(calibration.black_level, 0)
            self.assertEqual(calibration.white_level, 255)
            self.assertEqual(calibration.threshold, 127.5)
            self.assertTrue(calibration.markers_valid)
            self.assertTrue(validate_markers(grid, threshold=calibration.threshold))

    def test_decode_with_brightness_shift_uses_adaptive_threshold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original = Path(tmpdir) / "original.png"
            shifted = Path(tmpdir) / "shifted.png"
            generate_static_frame("Hola mundo", output_path=original)

            pixels = read_grayscale_png(original)
            write_grayscale_png(shifted, _apply_linear_levels(pixels, dark_offset=40, scale=0.55))

            result = decode_static_frame(shifted)

            self.assertEqual(result.message, "Hola mundo")
            self.assertGreater(result.calibration.threshold, 40)
            self.assertTrue(result.calibration.markers_valid)


if __name__ == "__main__":
    unittest.main()

