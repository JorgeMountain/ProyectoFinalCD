"""Multi-frame packet protocol for static visual frames."""

from __future__ import annotations

from dataclasses import dataclass

from common.bit_utils import bits_to_bytes, bytes_to_bits
from common.frame_config import DEFAULT_FRAME_CONFIG, FrameConfig
from common.frame_layout import data_cells


PACKET_MAGIC = b"OM"
PACKET_HEADER_BYTES = 10
FLAG_END = 0x01


@dataclass(frozen=True)
class Packet:
    """One byte-aligned packet carried by a visual frame."""

    sequence: int
    total_packets: int
    payload: bytes
    is_end: bool


def packet_payload_capacity(config: FrameConfig = DEFAULT_FRAME_CONFIG) -> int:
    """Return payload bytes available per frame after the packet header."""
    data_bits = len(data_cells(config))
    return (data_bits // 8) - PACKET_HEADER_BYTES


def encode_packet(packet: Packet, config: FrameConfig = DEFAULT_FRAME_CONFIG) -> list[int]:
    """Encode a packet into frame data bits."""
    capacity = packet_payload_capacity(config)
    if len(packet.payload) > capacity:
        raise ValueError(f"Packet payload has {len(packet.payload)} bytes but capacity is {capacity}")
    if not 0 <= packet.sequence < 65536:
        raise ValueError("sequence must fit in 16 bits")
    if not 1 <= packet.total_packets < 65536:
        raise ValueError("total_packets must fit in 16 bits")
    if packet.sequence >= packet.total_packets:
        raise ValueError("sequence must be lower than total_packets")

    flags = FLAG_END if packet.is_end else 0
    header = (
        PACKET_MAGIC
        + packet.sequence.to_bytes(2, "big")
        + packet.total_packets.to_bytes(2, "big")
        + len(packet.payload).to_bytes(2, "big")
        + bytes([flags, 0])
    )
    return bytes_to_bits(header + packet.payload)


def decode_packet(frame_bits: list[int] | tuple[int, ...]) -> Packet:
    """Decode frame data bits into a packet."""
    if len(frame_bits) < PACKET_HEADER_BYTES * 8:
        raise ValueError("Not enough bits to decode packet header")

    full_bytes = bits_to_bytes(frame_bits[: (len(frame_bits) // 8) * 8])
    header = full_bytes[:PACKET_HEADER_BYTES]
    if header[:2] != PACKET_MAGIC:
        raise ValueError("Frame does not contain a packet magic header")

    sequence = int.from_bytes(header[2:4], "big")
    total_packets = int.from_bytes(header[4:6], "big")
    payload_length = int.from_bytes(header[6:8], "big")
    flags = header[8]
    payload_start = PACKET_HEADER_BYTES
    payload_end = payload_start + payload_length
    if payload_end > len(full_bytes):
        raise ValueError("Packet payload length exceeds available frame data")

    return Packet(
        sequence=sequence,
        total_packets=total_packets,
        payload=full_bytes[payload_start:payload_end],
        is_end=bool(flags & FLAG_END),
    )


def split_payload(payload: bytes, config: FrameConfig = DEFAULT_FRAME_CONFIG) -> list[bytes]:
    """Split a byte payload into packet-sized chunks."""
    capacity = packet_payload_capacity(config)
    if capacity <= 0:
        raise ValueError("Packet payload capacity must be positive")
    return [payload[start : start + capacity] for start in range(0, len(payload), capacity)] or [b""]

