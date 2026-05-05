"""Decode and assemble multi-frame packet transmissions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2

from common.ecc import decode_reed_solomon
from common.frame_config import DEFAULT_FRAME_CONFIG, FrameConfig
from common.packet import Packet, decode_packet
from common.png_reader import read_grayscale_png
from receiver.decoder import decode_data_bits
from receiver.perspective import rectify_frame_image
from receiver.photo_decoder import parse_crop


@dataclass(frozen=True)
class DecodedSequence:
    """Decoded multi-frame message and transmission metadata."""

    message: str
    packets_received: int
    total_packets: int
    payload_bytes: int
    corrected_symbols: int


def decode_packet_from_pixels(
    pixels: list[list[int]],
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    threshold: float | None = None,
) -> Packet:
    """Decode one rectified frame image into a packet."""
    decoded_bits = decode_data_bits(pixels, config=config, threshold=threshold)
    return decode_packet(decoded_bits.bits)


def decode_packet_from_image(
    image_path: str | Path,
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    threshold: float | None = None,
) -> Packet:
    """Decode one canonical PNG packet frame."""
    return decode_packet_from_pixels(read_grayscale_png(image_path), config=config, threshold=threshold)


def decode_sequence_folder(
    input_dir: str | Path,
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    error_correction_bytes: int = 0,
) -> DecodedSequence:
    """Decode all PNG frames in a folder and reconstruct the message."""
    paths = sorted(Path(input_dir).glob("*.png"))
    if not paths:
        raise ValueError(f"No PNG frames found in {input_dir}")

    packets = [decode_packet_from_image(path, config=config) for path in paths]
    return assemble_packets(packets, error_correction_bytes=error_correction_bytes)


def assemble_packets(
    packets: list[Packet],
    error_correction_bytes: int = 0,
) -> DecodedSequence:
    """Assemble packets into the original message."""
    if not packets:
        raise ValueError("No packets to assemble")

    total_packets = packets[0].total_packets
    packet_map: dict[int, Packet] = {}
    for packet in packets:
        if packet.total_packets != total_packets:
            raise ValueError("Inconsistent packet total count")
        packet_map[packet.sequence] = packet

    missing = [sequence for sequence in range(total_packets) if sequence not in packet_map]
    if missing:
        raise ValueError(f"Missing packet sequences: {missing}")

    transmitted_payload = b"".join(packet_map[sequence].payload for sequence in range(total_packets))
    corrected_symbols = 0
    if error_correction_bytes > 0:
        decoded = decode_reed_solomon(transmitted_payload, error_correction_bytes)
        payload = decoded.payload
        corrected_symbols = decoded.corrected_symbols
    else:
        payload = transmitted_payload

    return DecodedSequence(
        message=payload.decode("utf-8"),
        packets_received=len(packet_map),
        total_packets=total_packets,
        payload_bytes=len(payload),
        corrected_symbols=corrected_symbols,
    )


def decode_video_stream(
    camera_index: int = 0,
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    error_correction_bytes: int = 0,
    crop: str | None = None,
    auto_perspective: bool = True,
    max_frames: int = 900,
) -> DecodedSequence:
    """Capture camera frames until all packet sequences are received."""
    crop_rect = parse_crop(crop)
    capture = cv2.VideoCapture(camera_index)
    if not capture.isOpened():
        raise RuntimeError(f"No se pudo abrir la camara {camera_index}")

    packets: dict[int, Packet] = {}
    total_packets: int | None = None
    try:
        for _ in range(max_frames):
            ok, frame = capture.read()
            if not ok:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if crop_rect is not None:
                x, y, width, height = crop_rect
                gray = gray[y : y + height, x : x + width]
            if auto_perspective:
                gray = rectify_frame_image(gray, config=config).image
            else:
                gray = cv2.resize(gray, (config.image_width, config.image_height), interpolation=cv2.INTER_AREA)

            try:
                packet = decode_packet_from_pixels(gray.astype("uint8").tolist(), config=config)
            except Exception:
                continue

            packets[packet.sequence] = packet
            total_packets = packet.total_packets
            print(f"Paquete {packet.sequence + 1}/{packet.total_packets} recibido")
            if total_packets is not None and len(packets) == total_packets:
                return assemble_packets(list(packets.values()), error_correction_bytes=error_correction_bytes)
    finally:
        capture.release()

    raise TimeoutError(f"No se recibieron todos los paquetes. Recibidos: {sorted(packets)}")

