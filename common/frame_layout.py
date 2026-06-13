"""Cell placement helpers for visual modem frames."""

from __future__ import annotations

from collections.abc import Iterable

from common.frame_config import FrameConfig
from common.modulation import bits_per_symbol, normalize_modulation


Cell = tuple[int, int]


def marker_origins(config: FrameConfig) -> tuple[Cell, Cell, Cell, Cell]:
    """Return top-left origins for the four corner finder markers."""
    marker_size = config.marker_cells
    return (
        (0, 0),
        (0, config.grid_cols - marker_size),
        (config.grid_rows - marker_size, 0),
        (config.grid_rows - marker_size, config.grid_cols - marker_size),
    )


def marker_cells(config: FrameConfig) -> set[Cell]:
    """Return cells reserved for four corner finder markers."""
    reserved: set[Cell] = set()
    marker_size = config.marker_cells

    for row_start, col_start in marker_origins(config):
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


def pilot_cells_with_bits(config: FrameConfig) -> list[tuple[Cell, int]]:
    """Return pilot cells paired with their expected OOK bit value."""
    return [
        (cell, 1 if symbol == 1 else 0)
        for cell, symbol in pilot_cells_with_symbols(config, modulation="ook")
    ]


def pilot_cells_with_symbols(
    config: FrameConfig,
    modulation: str = "ook",
) -> list[tuple[Cell, int]]:
    """Return pilot cells paired with their expected modulation symbol."""
    normalized = normalize_modulation(modulation)
    if normalized == "ook":
        return [
            (cell, 1 if index % 2 == 0 else 0)
            for index, cell in enumerate(pilot_cells(config))
        ]
    return [(cell, index % 4) for index, cell in enumerate(pilot_cells(config))]


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


def data_capacity_bits(config: FrameConfig, modulation: str = "ook") -> int:
    """Return the number of transport bits available in the data cells."""
    return len(data_cells(config)) * bits_per_symbol(modulation)


def require_capacity(
    bits: Iterable[int],
    config: FrameConfig,
    modulation: str = "ook",
) -> list[int]:
    """Materialize bits and validate that they fit in one frame."""
    bit_list = list(bits)
    capacity = data_capacity_bits(config, modulation)
    if len(bit_list) > capacity:
        raise ValueError(f"Payload needs {len(bit_list)} bits but frame capacity is {capacity}")
    return bit_list
