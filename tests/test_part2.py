import tempfile
import unittest
from pathlib import Path

from common.bit_utils import remove_length_prefix
from common.frame_config import FrameConfig
from common.frame_layout import (
    data_capacity_bits,
    data_cells,
    marker_cells,
    pilot_cells,
    pilot_cells_with_symbols,
)
from transmitter.generator import (
    BACKGROUND_LEVEL,
    build_frame_grid,
    generate_static_frame,
    message_to_frame_bits,
)


class FrameLayoutTests(unittest.TestCase):
    def test_4ask_doubles_data_bit_capacity(self):
        config = FrameConfig(grid_cols=8, grid_rows=8, marker_cells=2, pilot_cells=4)

        self.assertEqual(
            data_capacity_bits(config, modulation="4ask"),
            2 * data_capacity_bits(config, modulation="ook"),
        )

    def test_4ask_pilots_cover_all_four_symbols(self):
        config = FrameConfig(grid_cols=8, grid_rows=8, marker_cells=2, pilot_cells=8)

        symbols = [symbol for _, symbol in pilot_cells_with_symbols(config, modulation="4ask")]

        self.assertEqual(symbols, [0, 1, 2, 3, 0, 1, 2, 3])

    def test_layout_does_not_overlap_reserved_cells(self):
        config = FrameConfig(grid_cols=8, grid_rows=8, marker_cells=2, pilot_cells=4)
        reserved = marker_cells(config) | set(pilot_cells(config))

        self.assertTrue(reserved.isdisjoint(data_cells(config)))


class StaticTransmitterTests(unittest.TestCase):
    def test_message_bits_include_recoverable_length_prefix(self):
        frame_bits = message_to_frame_bits("Hola mundo")

        self.assertEqual(len(remove_length_prefix(frame_bits)), 80)

    def test_grid_contains_payload_symbols(self):
        config = FrameConfig(
            image_width=80,
            image_height=80,
            grid_cols=8,
            grid_rows=8,
            marker_cells=2,
            pilot_cells=4,
        )
        bits = [1, 0, 1, 1]
        grid = build_frame_grid(bits, config)
        cells = data_cells(config)

        self.assertEqual(grid[cells[0][0]][cells[0][1]], 255)
        self.assertEqual(grid[cells[1][0]][cells[1][1]], 0)
        self.assertNotEqual(grid[0][0], BACKGROUND_LEVEL)

    def test_generate_static_frame_writes_png(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "frame.png"
            result = generate_static_frame("Hola mundo", output_path=output)

            self.assertTrue(output.exists())
            self.assertEqual(output.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(result.output_path, output)


if __name__ == "__main__":
    unittest.main()
