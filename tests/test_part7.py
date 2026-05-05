import tempfile
import unittest
from pathlib import Path

from common.ecc import decode_reed_solomon, encode_reed_solomon
from common.frame_config import DEFAULT_FRAME_CONFIG
from common.frame_layout import data_cells
from common.png_reader import read_grayscale_png
from common.png_writer import write_grayscale_png
from receiver.decoder import decode_static_frame
from transmitter.generator import generate_static_frame


class ReedSolomonTests(unittest.TestCase):
    def test_reed_solomon_corrects_corrupted_bytes(self):
        encoded = bytearray(encode_reed_solomon(b"Hola mundo", parity_bytes=16))
        encoded[0] ^= 0x01
        encoded[3] ^= 0x80
        encoded[8] ^= 0x22

        decoded = decode_reed_solomon(bytes(encoded), parity_bytes=16)

        self.assertEqual(decoded.payload, b"Hola mundo")
        self.assertEqual(decoded.corrected_symbols, 3)

    def test_static_frame_decodes_after_corrupted_data_cells(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original = Path(tmpdir) / "frame.png"
            corrupted = Path(tmpdir) / "corrupted.png"
            generate_static_frame("Hola mundo", output_path=original, error_correction_bytes=16)
            pixels = read_grayscale_png(original)

            # Keep the 16-bit length prefix intact and damage five different
            # encoded payload bytes. RS(16) can correct up to eight byte errors.
            bit_indices = [16 + byte_index * 8 for byte_index in range(5)]
            for bit_index in bit_indices:
                _flip_data_cell(pixels, bit_index)

            write_grayscale_png(corrupted, pixels)
            result = decode_static_frame(corrupted, error_correction_bytes=16)

            self.assertEqual(result.message, "Hola mundo")
            self.assertEqual(result.corrected_symbols, 5)


def _flip_data_cell(pixels: list[list[int]], bit_index: int) -> None:
    config = DEFAULT_FRAME_CONFIG
    row, col = data_cells(config)[bit_index]
    row_start = row * config.cell_height
    row_end = row_start + config.cell_height
    col_start = col * config.cell_width
    col_end = col_start + config.cell_width

    current = pixels[row_start][col_start]
    replacement = 0 if current >= 128 else 255
    for pixel_row in range(row_start, row_end):
        for pixel_col in range(col_start, col_end):
            pixels[pixel_row][pixel_col] = replacement


if __name__ == "__main__":
    unittest.main()

