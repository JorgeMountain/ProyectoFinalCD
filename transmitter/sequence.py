"""Generate and display multi-frame transmissions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2

from common.ecc import encode_reed_solomon
from common.frame_config import DEFAULT_FRAME_CONFIG, FrameConfig
from common.packet import Packet, encode_packet, packet_payload_capacity, split_payload
from common.png_writer import write_grayscale_png
from transmitter.generator import build_frame_grid, render_grid_to_pixels


@dataclass(frozen=True)
class GeneratedSequence:
    """Metadata for a generated multi-frame transmission."""

    output_dir: Path
    frame_paths: list[Path]
    payload_bytes: int
    transmitted_bytes: int
    packet_payload_capacity: int
    error_correction_bytes: int


def generate_frame_sequence(
    message: str,
    output_dir: str | Path = "data/generated/sequence",
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    error_correction_bytes: int = 0,
) -> GeneratedSequence:
    """Generate a folder of packetized PNG frames."""
    payload = message.encode("utf-8")
    transmitted_payload = payload
    if error_correction_bytes > 0:
        transmitted_payload = encode_reed_solomon(payload, error_correction_bytes)

    chunks = split_payload(transmitted_payload, config)
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    frame_paths: list[Path] = []

    for sequence, chunk in enumerate(chunks):
        packet = Packet(
            sequence=sequence,
            total_packets=len(chunks),
            payload=chunk,
            is_end=sequence == len(chunks) - 1,
        )
        grid = build_frame_grid(encode_packet(packet, config), config)
        pixels = render_grid_to_pixels(grid, config)
        frame_path = path / f"frame_{sequence:04d}.png"
        write_grayscale_png(frame_path, pixels)
        frame_paths.append(frame_path)

    return GeneratedSequence(
        output_dir=path,
        frame_paths=frame_paths,
        payload_bytes=len(payload),
        transmitted_bytes=len(transmitted_payload),
        packet_payload_capacity=packet_payload_capacity(config),
        error_correction_bytes=error_correction_bytes,
    )


def display_frame_sequence(
    frame_paths: list[Path],
    frame_duration_ms: int = 150,
    repeat: int = 1,
    window_name: str = "Transmisor multi-frame",
) -> None:
    """Display generated frames full-screen in sequence."""
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    try:
        for _ in range(repeat):
            for frame_path in frame_paths:
                image = cv2.imread(str(frame_path), cv2.IMREAD_GRAYSCALE)
                if image is None:
                    raise ValueError(f"No se pudo leer frame: {frame_path}")
                cv2.imshow(window_name, image)
                key = cv2.waitKey(frame_duration_ms) & 0xFF
                if key in (27, ord("q")):
                    return
    finally:
        cv2.destroyWindow(window_name)

