import tempfile
import unittest
from pathlib import Path

from common.frame_config import FrameConfig
from common.png_reader import read_grayscale_png
from common.png_writer import write_grayscale_png
from receiver.decoder import decode_static_frame, sample_grid_levels
from transmitter.generator import generate_static_frame


class PngReaderTests(unittest.TestCase):
    def test_grayscale_png_round_trip(self):
        pixels = [
            [0, 64, 128],
            [255, 128, 0],
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "test.png"
            write_grayscale_png(output, pixels)

            self.assertEqual(read_grayscale_png(output), pixels)


class OfflineReceiverTests(unittest.TestCase):
    def test_decode_generated_4ask_static_frame(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "frame-4ask.png"
            generate_static_frame("Hola mundo", output_path=output, modulation="4ask")

            result = decode_static_frame(output, modulation="4ask")

            self.assertEqual(result.message, "Hola mundo")
            self.assertEqual(result.payload_bits, 80)

    def test_sample_grid_levels(self):
        config = FrameConfig(
            image_width=4,
            image_height=4,
            grid_cols=2,
            grid_rows=2,
            marker_cells=1,
            pilot_cells=0,
        )
        pixels = [
            [0, 0, 10, 10],
            [0, 0, 10, 10],
            [200, 200, 255, 255],
            [200, 200, 255, 255],
        ]

        self.assertEqual(sample_grid_levels(pixels, config), [[0, 10], [200, 255]])

    def test_decode_generated_static_frame(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "frame.png"
            generate_static_frame("Hola mundo", output_path=output)

            result = decode_static_frame(output)

            self.assertEqual(result.message, "Hola mundo")
            self.assertEqual(result.payload_bits, 80)


if __name__ == "__main__":
    unittest.main()
