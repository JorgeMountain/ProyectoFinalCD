"""Generate and display multi-frame transmissions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2

from common.ecc import encode_reed_solomon
from common.frame_config import DEFAULT_FRAME_CONFIG, FrameConfig
from common.frame_layout import marker_origins
from common.modulation import normalize_modulation
from common.packet import Packet, encode_packet, packet_payload_capacity, split_payload
from common.png_writer import write_grayscale_png
from transmitter.generator import build_frame_grid, render_grid_to_pixels


CORNER_MARKER_COLORS_BGR = (
    (0, 255, 255),  # yellow
    (0, 255, 255),  # yellow
    (0, 255, 255),  # yellow
    (0, 255, 255),  # yellow
)


@dataclass(frozen=True)
class GeneratedSequence:
    """Metadata for a generated multi-frame transmission."""

    output_dir: Path
    frame_paths: list[Path]
    payload_bytes: int
    transmitted_bytes: int
    packet_payload_capacity: int
    error_correction_bytes: int
    modulation: str


def generate_frame_sequence(
    message: str,
    output_dir: str | Path = "data/generated/sequence",
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    error_correction_bytes: int = 0,
    modulation: str = "ook",
) -> GeneratedSequence:
    """Generate a folder of packetized PNG frames."""
    normalized = normalize_modulation(modulation)
    payload = message.encode("utf-8")
    transmitted_payload = payload
    if error_correction_bytes > 0:
        transmitted_payload = encode_reed_solomon(payload, error_correction_bytes)

    chunks = split_payload(transmitted_payload, config, normalized)
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    for stale_frame in path.glob("frame_*.png"):
        stale_frame.unlink()
    frame_paths: list[Path] = []

    for sequence, chunk in enumerate(chunks):
        packet = Packet(
            sequence=sequence,
            total_packets=len(chunks),
            payload=chunk,
            is_end=sequence == len(chunks) - 1,
        )
        grid = build_frame_grid(
            encode_packet(packet, config, normalized),
            config,
            normalized,
        )
        pixels = render_grid_to_pixels(grid, config)
        frame_path = path / f"frame_{sequence:04d}.png"
        write_grayscale_png(frame_path, pixels)
        frame_paths.append(frame_path)

    return GeneratedSequence(
        output_dir=path,
        frame_paths=frame_paths,
        payload_bytes=len(payload),
        transmitted_bytes=len(transmitted_payload),
        packet_payload_capacity=packet_payload_capacity(config, normalized),
        error_correction_bytes=error_correction_bytes,
        modulation=normalized,
    )


def display_frame_sequence(
    frame_paths: list[Path],
    frame_duration_ms: int = 150,
    repeat: int = 1,
    window_name: str = "Transmisor multi-frame",
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    fullscreen: bool = True,
    window_size: tuple[int, int] = (960, 540),
    window_position: tuple[int, int] | None = None,
) -> None:
    """Display generated frames in sequence."""
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    if fullscreen:
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    else:
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, window_size[0], window_size[1])
        if window_position is not None:
            cv2.moveWindow(window_name, window_position[0], window_position[1])

    try:
        for _ in range(repeat):
            for frame_path in frame_paths:
                image = cv2.imread(str(frame_path), cv2.IMREAD_GRAYSCALE)
                if image is None:
                    raise ValueError(f"No se pudo leer frame: {frame_path}")
                cv2.imshow(window_name, colorize_corner_markers(image, config))
                key = cv2.waitKey(frame_duration_ms) & 0xFF
                if key in (27, ord("q")):
                    return
    finally:
        cv2.destroyWindow(window_name)


def colorize_corner_markers(grayscale_image, config: FrameConfig = DEFAULT_FRAME_CONFIG):
    """Paint finder marker borders with saturated colors for easier camera detection."""
    image = cv2.cvtColor(grayscale_image, cv2.COLOR_GRAY2BGR)
    marker_size = config.marker_cells
    center = marker_size // 2

    for (row_start, col_start), color in zip(marker_origins(config), CORNER_MARKER_COLORS_BGR):
        for row_offset in range(marker_size):
            for col_offset in range(marker_size):
                if row_offset == center and col_offset == center:
                    continue
                row = row_start + row_offset
                col = col_start + col_offset
                y0 = row * config.cell_height
                y1 = y0 + config.cell_height
                x0 = col * config.cell_width
                x1 = x0 + config.cell_width
                image[y0:y1, x0:x1] = color

    return image

