"""Calibration helpers based on known pilots and finder markers."""

from __future__ import annotations

from dataclasses import dataclass

from common.frame_config import DEFAULT_FRAME_CONFIG, FrameConfig
from common.frame_layout import marker_origins, pilot_cells_with_bits, pilot_cells_with_symbols


@dataclass(frozen=True)
class OokCalibration:
    """Decision data estimated from known pilot cells."""

    threshold: float
    black_level: float
    white_level: float
    contrast: float
    markers_valid: bool


@dataclass(frozen=True)
class Ask4Calibration:
    """Four calibrated decision centers estimated from known pilot cells."""

    levels: tuple[float, float, float, float]
    thresholds: tuple[float, float, float]
    contrast: float
    markers_valid: bool


def estimate_ook_calibration(
    grid_levels: list[list[float]],
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
) -> OokCalibration:
    """Estimate OOK threshold from alternating black/white pilot cells."""
    black_levels: list[float] = []
    white_levels: list[float] = []

    for (row, col), expected_bit in pilot_cells_with_bits(config):
        if expected_bit == 1:
            white_levels.append(grid_levels[row][col])
        else:
            black_levels.append(grid_levels[row][col])

    if not black_levels or not white_levels:
        raise ValueError("At least one black and one white pilot cell are required")

    black_level = sum(black_levels) / len(black_levels)
    white_level = sum(white_levels) / len(white_levels)
    threshold = (black_level + white_level) / 2

    return OokCalibration(
        threshold=threshold,
        black_level=black_level,
        white_level=white_level,
        contrast=white_level - black_level,
        markers_valid=validate_markers(grid_levels, config, threshold),
    )


def estimate_ask4_calibration(
    grid_levels: list[list[float]],
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
) -> Ask4Calibration:
    """Estimate four 4-ASK decision centers from known pilot cells."""
    samples: list[list[float]] = [[], [], [], []]
    for (row, col), symbol in pilot_cells_with_symbols(config, modulation="4ask"):
        samples[symbol].append(grid_levels[row][col])

    if any(not level_samples for level_samples in samples):
        raise ValueError("At least one pilot cell is required for every 4-ASK level")

    levels = tuple(sum(values) / len(values) for values in samples)
    if any(levels[index] >= levels[index + 1] for index in range(3)):
        raise ValueError("4-ASK pilot levels must be strictly increasing")

    thresholds = tuple((levels[index] + levels[index + 1]) / 2 for index in range(3))
    marker_threshold = (levels[0] + levels[-1]) / 2
    return Ask4Calibration(
        levels=levels,  # type: ignore[arg-type]
        thresholds=thresholds,  # type: ignore[arg-type]
        contrast=levels[-1] - levels[0],
        markers_valid=validate_markers(grid_levels, config, marker_threshold),
    )


def validate_markers(
    grid_levels: list[list[float]],
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    threshold: float = 127.5,
) -> bool:
    """Check whether the four corner markers match the expected pattern."""
    marker_size = config.marker_cells
    if marker_size < 1:
        return False

    center = marker_size // 2
    for row_start, col_start in marker_origins(config):
        for row_offset in range(marker_size):
            for col_offset in range(marker_size):
                row = row_start + row_offset
                col = col_start + col_offset
                expected_is_white = not (row_offset == center and col_offset == center)
                actual_is_white = grid_levels[row][col] >= threshold
                if actual_is_white != expected_is_white:
                    return False
    return True
