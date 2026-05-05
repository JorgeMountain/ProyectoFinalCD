"""Cell placement helpers for visual modem frames."""

from __future__ import annotations

from collections.abc import Iterable

from common.frame_config import FrameConfig


Cell = tuple[int, int]


def marker_cells(config: FrameConfig) -> set[Cell]:
    """Return cells reserved for four corner finder markers."""
    reserved: set[Cell] = set()
    marker_size = config.marker_cells
    corner_origins = (
        (0, 0),
        (0, config.grid_cols - marker_size),
        (config.grid_rows - marker_size, 0),
        (config.grid_rows - marker_size, config.grid_cols - marker_size),
    )

    for row_start, col_start in corner_origins:
        for row in range(row_start, row_start + marker_size):
            for col in range(col_start, col_start + marker_size):
                reserved.add((row, col))
    return reserved


def pilot_cells(config: FrameConfig) -> list[Cell]:
    """Return deterministic pilot cells, excluding marker regions."""
    reserved = marker_cells(config)
    pilots: list[Cell] = []

    for row in range(config.grid_rows):
        for col in range(config.grid_cols):
            cell = (row, col)
            if cell in reserved:
                continue
            pilots.append(cell)
            if len(pilots) == config.pilot_cells:
                return pilots

    return pilots


def data_cells(config: FrameConfig) -> list[Cell]:
    """Return cells available for payload data."""
    reserved = marker_cells(config) | set(pilot_cells(config))
    cells: list[Cell] = []

    for row in range(config.grid_rows):
        for col in range(config.grid_cols):
            cell = (row, col)
            if cell not in reserved:
                cells.append(cell)
    return cells


def require_capacity(bits: Iterable[int], config: FrameConfig) -> list[int]:
    """Materialize bits and validate that they fit in one frame."""
    bit_list = list(bits)
    capacity = len(data_cells(config))
    if len(bit_list) > capacity:
        raise ValueError(f"Payload needs {len(bit_list)} cells but frame capacity is {capacity}")
    return bit_list

