"""Offline decoder for static transmitter frames."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.bit_utils import bits_to_text, remove_length_prefix
from common.frame_config import DEFAULT_FRAME_CONFIG, FrameConfig
from common.frame_layout import data_cells
from common.modulation import ook_demodulate
from common.png_reader import read_grayscale_png
from receiver.calibration import OokCalibration, estimate_ook_calibration


@dataclass(frozen=True)
class DecodedFrame:
    """Metadata returned after decoding a static frame."""

    message: str
    transmitted_bits: int
    payload_bits: int
    average_levels: list[float]
    calibration: OokCalibration


def decode_static_frame(
    image_path: str | Path = "data/generated/frame_test.png",
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    threshold: float | None = None,
    length_prefix_width: int = 16,
) -> DecodedFrame:
    """Decode a PNG static frame back into text."""
    pixels = read_grayscale_png(image_path)
    grid_levels = sample_grid_levels(pixels, config)
    calibration = estimate_ook_calibration(grid_levels, config)
    decision_threshold = calibration.threshold if threshold is None else threshold
    if not calibration.markers_valid:
        raise ValueError("Frame finder markers do not match the expected pattern")

    data_levels = [grid_levels[row][col] for row, col in data_cells(config)]
    raw_bits = ook_demodulate(data_levels, threshold=decision_threshold)
    payload_bits = remove_length_prefix(raw_bits, width=length_prefix_width)
    message = bits_to_text(payload_bits)

    return DecodedFrame(
        message=message,
        transmitted_bits=length_prefix_width + len(payload_bits),
        payload_bits=len(payload_bits),
        average_levels=data_levels,
        calibration=calibration,
    )


def sample_grid_levels(pixels: list[list[int]], config: FrameConfig) -> list[list[float]]:
    """Average each macropixel cell from a rendered frame image."""
    _validate_dimensions(pixels, config)

    grid: list[list[float]] = []
    for grid_row in range(config.grid_rows):
        row_levels: list[float] = []
        pixel_row_start = grid_row * config.cell_height
        pixel_row_end = pixel_row_start + config.cell_height

        for grid_col in range(config.grid_cols):
            pixel_col_start = grid_col * config.cell_width
            pixel_col_end = pixel_col_start + config.cell_width
            total = 0
            count = 0

            for pixel_row in range(pixel_row_start, pixel_row_end):
                row = pixels[pixel_row]
                total += sum(row[pixel_col_start:pixel_col_end])
                count += config.cell_width

            row_levels.append(total / count)
        grid.append(row_levels)

    return grid


def _validate_dimensions(pixels: list[list[int]], config: FrameConfig) -> None:
    if len(pixels) != config.image_height:
        raise ValueError(f"Expected image height {config.image_height}, got {len(pixels)}")
    if not pixels:
        raise ValueError("Image has no pixels")
    width = len(pixels[0])
    if width != config.image_width:
        raise ValueError(f"Expected image width {config.image_width}, got {width}")
    for row in pixels:
        if len(row) != width:
            raise ValueError("Image rows have inconsistent widths")
