"""Configuration values for the visual frame grid."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameConfig:
    """Basic dimensions for a screen frame divided into macropixels."""

    image_width: int = 1280
    image_height: int = 720
    grid_cols: int = 32
    grid_rows: int = 18
    marker_cells: int = 3
    pilot_cells: int = 8

    @property
    def cell_width(self) -> int:
        return self.image_width // self.grid_cols

    @property
    def cell_height(self) -> int:
        return self.image_height // self.grid_rows

    @property
    def total_cells(self) -> int:
        return self.grid_cols * self.grid_rows

    @property
    def marker_reserved_cells(self) -> int:
        # Four square finder markers, one per corner.
        return 4 * self.marker_cells * self.marker_cells

    @property
    def data_capacity_bits_ook(self) -> int:
        """Approximate one-bit-per-cell capacity after reserved cells."""
        return self.total_cells - self.marker_reserved_cells - self.pilot_cells


DEFAULT_FRAME_CONFIG = FrameConfig()

