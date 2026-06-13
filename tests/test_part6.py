import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from common.frame_config import DEFAULT_FRAME_CONFIG
from common.png_reader import read_grayscale_png
from receiver.photo_decoder import decode_photo_frame, load_photo_pixels
from receiver.perspective import detect_frame_corners, rectify_frame_image
from transmitter.generator import generate_static_frame


class PerspectiveCorrectionTests(unittest.TestCase):
    def test_decode_4ask_perspective_warped_photo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            photo = _make_warped_photo(Path(tmpdir), "Hola mundo", modulation="4ask")

            result = decode_photo_frame(
                photo,
                auto_perspective=True,
                modulation="4ask",
            )

            self.assertEqual(result.message, "Hola mundo")

    def test_detect_corners_on_generated_frame(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            frame = Path(tmpdir) / "frame.png"
            generate_static_frame("Hola mundo", output_path=frame)
            image = np.array(read_grayscale_png(frame), dtype=np.uint8)

            corners = detect_frame_corners(image)

            self.assertAlmostEqual(corners[0][0], 0, delta=3)
            self.assertAlmostEqual(corners[0][1], 0, delta=3)
            self.assertAlmostEqual(corners[2][0], DEFAULT_FRAME_CONFIG.image_width - 1, delta=3)
            self.assertAlmostEqual(corners[2][1], DEFAULT_FRAME_CONFIG.image_height - 1, delta=3)

    def test_decode_perspective_warped_photo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            photo = _make_warped_photo(Path(tmpdir), "Hola mundo")

            result = decode_photo_frame(photo, auto_perspective=True)

            self.assertEqual(result.message, "Hola mundo")

    def test_load_photo_pixels_auto_perspective_returns_canonical_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            photo = _make_warped_photo(Path(tmpdir), "Hola mundo")

            pixels = load_photo_pixels(photo, auto_perspective=True)

            self.assertEqual(len(pixels), DEFAULT_FRAME_CONFIG.image_height)
            self.assertEqual(len(pixels[0]), DEFAULT_FRAME_CONFIG.image_width)

    def test_rectify_frame_image_returns_corners(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            photo = _make_warped_photo(Path(tmpdir), "Hola mundo")
            image = cv2.imread(str(photo), cv2.IMREAD_GRAYSCALE)

            result = rectify_frame_image(image)

            self.assertEqual(len(result.corners), 4)
            self.assertEqual(result.image.shape, (720, 1280))


def _make_warped_photo(tmpdir: Path, message: str, modulation: str = "ook") -> Path:
    config = DEFAULT_FRAME_CONFIG
    frame = tmpdir / "frame.png"
    photo = tmpdir / "warped.png"
    generate_static_frame(message, output_path=frame, modulation=modulation)
    source_image = np.array(read_grayscale_png(frame), dtype=np.uint8)

    canvas_width = 1500
    canvas_height = 900
    source = np.array(
        [
            [0, 0],
            [config.image_width - 1, 0],
            [config.image_width - 1, config.image_height - 1],
            [0, config.image_height - 1],
        ],
        dtype=np.float32,
    )
    destination = np.array(
        [
            [120, 90],
            [1340, 135],
            [1260, 760],
            [190, 700],
        ],
        dtype=np.float32,
    )
    homography = cv2.getPerspectiveTransform(source, destination)
    warped = cv2.warpPerspective(
        source_image,
        homography,
        (canvas_width, canvas_height),
        flags=cv2.INTER_LINEAR,
        borderValue=20,
    )
    cv2.imwrite(str(photo), warped)
    return photo


if __name__ == "__main__":
    unittest.main()
