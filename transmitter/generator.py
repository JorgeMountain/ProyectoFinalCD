"""Static frame generator for the optical modem transmitter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from common.bit_utils import add_length_prefix, bytes_to_bits
from common.ecc import encode_reed_solomon
from common.frame_config import DEFAULT_FRAME_CONFIG, FrameConfig
from common.frame_layout import (
    data_capacity_bits,
    data_cells,
    marker_cells,
    marker_origins,
    pilot_cells_with_symbols,
    require_capacity,
)
from common.modulation import ASK4_LEVELS, ask4_modulate, normalize_modulation, ook_modulate
from common.png_writer import write_grayscale_png


BACKGROUND_LEVEL = 24
UNUSED_DATA_LEVEL = 64


@dataclass(frozen=True)
class GeneratedFrame:
    """Metadata returned after creating a static transmitter frame."""

    output_path: Path
    payload_bits: int
    transmitted_bits: int
    data_capacity_bits: int
    error_correction_bytes: int
    modulation: str


def message_to_frame_bits(
    message: str,
    length_prefix_width: int = 16,
    error_correction_bytes: int = 0,
) -> list[int]:
    """Convert a message into length-prefixed payload bits."""
    payload = message.encode("utf-8")
    if error_correction_bytes > 0:
        payload = encode_reed_solomon(payload, error_correction_bytes)
    return add_length_prefix(bytes_to_bits(payload), width=length_prefix_width)


def build_frame_grid(
    bits: list[int],
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    modulation: str = "ook",
) -> list[list[int]]:
    """Build a grid of grayscale levels for one visual frame."""
    normalized = normalize_modulation(modulation)
    checked_bits = require_capacity(bits, config, normalized)
    grid = [[BACKGROUND_LEVEL for _ in range(config.grid_cols)] for _ in range(config.grid_rows)]

    _place_markers(grid, config)
    _place_pilots(grid, config, normalized)
    _place_data(grid, checked_bits, config, normalized)

    return grid


def render_grid_to_pixels(grid: list[list[int]], config: FrameConfig) -> list[list[int]]:
    """Scale a cell-level grid into image pixels."""
    pixels: list[list[int]] = []
    for grid_row in grid:
        pixel_row: list[int] = []
        for level in grid_row:
            pixel_row.extend([level] * config.cell_width)
        for _ in range(config.cell_height):
            pixels.append(list(pixel_row))
    return pixels


def generate_static_frame(
    message: str,
    output_path: str | Path = "data/generated/frame_test.png",
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    error_correction_bytes: int = 0,
    modulation: str = "ook",
) -> GeneratedFrame:
    """Generate and save one PNG frame containing the message."""
    normalized = normalize_modulation(modulation)
    frame_bits = message_to_frame_bits(message, error_correction_bytes=error_correction_bytes)
    grid = build_frame_grid(frame_bits, config, normalized)
    pixels = render_grid_to_pixels(grid, config)
    path = Path(output_path)
    write_grayscale_png(path, pixels)

    return GeneratedFrame(
        output_path=path,
        payload_bits=len(message.encode("utf-8")) * 8,
        transmitted_bits=len(frame_bits),
        data_capacity_bits=data_capacity_bits(config, normalized),
        error_correction_bytes=error_correction_bytes,
        modulation=normalized,
    )


def _place_markers(grid: list[list[int]], config: FrameConfig) -> None:
    marker_size = config.marker_cells

    for row_start, col_start in marker_origins(config):
        for row_offset in range(marker_size):
            for col_offset in range(marker_size):
                row = row_start + row_offset
                col = col_start + col_offset
                is_center = row_offset == marker_size // 2 and col_offset == marker_size // 2
                grid[row][col] = 0 if is_center else 255


def _place_pilots(grid: list[list[int]], config: FrameConfig, modulation: str) -> None:
    for (row, col), symbol in pilot_cells_with_symbols(config, modulation):
        if modulation == "ook":
            grid[row][col] = 255 if symbol == 1 else 0
        else:
            grid[row][col] = ASK4_LEVELS[symbol]


def _place_data(
    grid: list[list[int]],
    bits: list[int],
    config: FrameConfig,
    modulation: str,
) -> None:
    symbols = ook_modulate(bits) if modulation == "ook" else ask4_modulate(bits)
    cells = data_cells(config)
    unused_level = UNUSED_DATA_LEVEL if modulation == "ook" else ASK4_LEVELS[0]

    for index, (row, col) in enumerate(cells):
        grid[row][col] = symbols[index] if index < len(symbols) else unused_level


def used_reserved_cells(config: FrameConfig = DEFAULT_FRAME_CONFIG) -> set[tuple[int, int]]:
    """Expose reserved cells for tests and later receiver work."""
    return marker_cells(config) | set(pilot_cells(config))
