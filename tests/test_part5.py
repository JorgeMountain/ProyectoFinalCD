import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from common.frame_config import DEFAULT_FRAME_CONFIG
from common.png_reader import read_grayscale_png
from receiver.photo_decoder import decode_photo_frame, load_photo_pixels, parse_crop
from transmitter.generator import generate_static_frame


class PhotoDecoderTests(unittest.TestCase):
    def test_parse_crop(self):
        self.assertEqual(parse_crop("10,20,300,200"), (10, 20, 300, 200))
        self.assertIsNone(parse_crop(None))

    def test_decode_generated_png_through_photo_loader(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            frame = Path(tmpdir) / "frame.png"
            generate_static_frame("Hola mundo", output_path=frame)

            result = decode_photo_frame(frame)

            self.assertEqual(result.message, "Hola mundo")

    def test_decode_manual_crop_from_larger_image(self):
        config = DEFAULT_FRAME_CONFIG
        with tempfile.TemporaryDirectory() as tmpdir:
            frame = Path(tmpdir) / "frame.png"
            photo = Path(tmpdir) / "photo.png"
            generate_static_frame("Hola mundo", output_path=frame)

            frame_pixels = np.array(read_grayscale_png(frame), dtype=np.uint8)
            canvas = np.full(
                (config.image_height + 80, config.image_width + 120),
                30,
                dtype=np.uint8,
            )
            x, y = 70, 35
            canvas[y : y + config.image_height, x : x + config.image_width] = frame_pixels
            cv2.imwrite(str(photo), canvas)

            result = decode_photo_frame(photo, crop=(x, y, config.image_width, config.image_height))

            self.assertEqual(result.message, "Hola mundo")

    def test_load_photo_pixels_resizes_to_frame_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "small.png"
            cv2.imwrite(str(image_path), np.zeros((100, 200), dtype=np.uint8))

            pixels = load_photo_pixels(image_path)

            self.assertEqual(len(pixels), DEFAULT_FRAME_CONFIG.image_height)
            self.assertEqual(len(pixels[0]), DEFAULT_FRAME_CONFIG.image_width)


if __name__ == "__main__":
    unittest.main()

