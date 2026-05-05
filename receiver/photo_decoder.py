"""Decode manually cropped photos of the transmitter screen."""

from __future__ import annotations

from pathlib import Path

import cv2

from common.frame_config import DEFAULT_FRAME_CONFIG, FrameConfig
from receiver.decoder import DecodedFrame, decode_static_pixels


Crop = tuple[int, int, int, int]


def parse_crop(value: str | None) -> Crop | None:
    """Parse a crop string in x,y,width,height format."""
    if value is None or value.strip() == "":
        return None

    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 4:
        raise ValueError("Crop must have format x,y,width,height")

    x, y, width, height = (int(part) for part in parts)
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        raise ValueError("Crop values must be non-negative and width/height must be positive")
    return x, y, width, height


def load_photo_pixels(
    image_path: str | Path,
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    crop: Crop | None = None,
) -> list[list[int]]:
    """Load a photo, optionally crop it, and resize it to the receiver grid size."""
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    if crop is not None:
        x, y, width, height = crop
        if x + width > image.shape[1] or y + height > image.shape[0]:
            raise ValueError("Crop rectangle is outside the image bounds")
        image = image[y : y + height, x : x + width]

    interpolation = cv2.INTER_AREA if image.shape[1] >= config.image_width else cv2.INTER_LINEAR
    resized = cv2.resize(
        image,
        (config.image_width, config.image_height),
        interpolation=interpolation,
    )
    return resized.astype("uint8").tolist()


def decode_photo_frame(
    image_path: str | Path,
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    crop: Crop | None = None,
    threshold: float | None = None,
) -> DecodedFrame:
    """Decode a real photo or screenshot after optional manual cropping."""
    pixels = load_photo_pixels(image_path, config=config, crop=crop)
    return decode_static_pixels(pixels, config=config, threshold=threshold)

