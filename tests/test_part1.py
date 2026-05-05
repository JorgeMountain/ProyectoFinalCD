import unittest

from common.bit_utils import (
    add_length_prefix,
    bits_to_int,
    bits_to_text,
    int_to_bits,
    remove_length_prefix,
    text_to_bits,
)
from common.frame_config import DEFAULT_FRAME_CONFIG, FrameConfig
from common.modulation import (
    bpsk_demodulate,
    bpsk_modulate,
    manchester_decode,
    manchester_encode,
    ook_demodulate,
    ook_modulate,
)


class BitUtilsTests(unittest.TestCase):
    def test_text_round_trip(self):
        original = "Hola mundo"
        bits = text_to_bits(original)

        self.assertEqual(bits_to_text(bits), original)

    def test_length_prefix_round_trip(self):
        payload = text_to_bits("Mensaje corto")
        framed = add_length_prefix(payload, width=16)

        self.assertEqual(remove_length_prefix(framed, width=16), payload)

    def test_integer_round_trip(self):
        bits = int_to_bits(500, width=16)

        self.assertEqual(bits_to_int(bits), 500)


class ModulationTests(unittest.TestCase):
    def test_ook_round_trip(self):
        bits = text_to_bits("OK")
        symbols = ook_modulate(bits)

        self.assertEqual(ook_demodulate(symbols), bits)

    def test_bpsk_round_trip(self):
        bits = text_to_bits("BPSK")
        symbols = bpsk_modulate(bits)

        self.assertEqual(bpsk_demodulate(symbols), bits)

    def test_manchester_round_trip(self):
        bits = text_to_bits("CLK")
        chips = manchester_encode(bits)

        self.assertEqual(manchester_decode(chips), bits)


class FrameConfigTests(unittest.TestCase):
    def test_default_capacity_is_positive(self):
        self.assertGreater(DEFAULT_FRAME_CONFIG.data_capacity_bits_ook, 0)

    def test_cell_dimensions(self):
        config = FrameConfig(image_width=1280, image_height=720, grid_cols=32, grid_rows=18)

        self.assertEqual(config.cell_width, 40)
        self.assertEqual(config.cell_height, 40)


if __name__ == "__main__":
    unittest.main()

