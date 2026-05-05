"""Utilities to convert text, bytes, and bit streams."""

from __future__ import annotations


Bit = int


def bytes_to_bits(data: bytes) -> list[Bit]:
    """Convert bytes into a big-endian bit list."""
    bits: list[Bit] = []
    for byte in data:
        bits.extend((byte >> shift) & 1 for shift in range(7, -1, -1))
    return bits


def bits_to_bytes(bits: list[Bit] | tuple[Bit, ...]) -> bytes:
    """Convert a big-endian bit list into bytes.

    The number of bits must be a multiple of 8 so the conversion is exact.
    """
    if len(bits) % 8 != 0:
        raise ValueError("The number of bits must be a multiple of 8")

    output = bytearray()
    for start in range(0, len(bits), 8):
        byte = 0
        for bit in bits[start : start + 8]:
            if bit not in (0, 1):
                raise ValueError(f"Invalid bit value: {bit!r}")
            byte = (byte << 1) | bit
        output.append(byte)
    return bytes(output)


def text_to_bits(text: str, encoding: str = "utf-8") -> list[Bit]:
    """Encode text into bits using the selected character encoding."""
    return bytes_to_bits(text.encode(encoding))


def bits_to_text(bits: list[Bit] | tuple[Bit, ...], encoding: str = "utf-8") -> str:
    """Decode bits back into text using the selected character encoding."""
    return bits_to_bytes(bits).decode(encoding)


def int_to_bits(value: int, width: int) -> list[Bit]:
    """Represent a non-negative integer using exactly width bits."""
    if value < 0:
        raise ValueError("value must be non-negative")
    if width <= 0:
        raise ValueError("width must be positive")
    if value >= (1 << width):
        raise ValueError(f"value {value} does not fit in {width} bits")
    return [(value >> shift) & 1 for shift in range(width - 1, -1, -1)]


def bits_to_int(bits: list[Bit] | tuple[Bit, ...]) -> int:
    """Convert a big-endian bit list into an integer."""
    value = 0
    for bit in bits:
        if bit not in (0, 1):
            raise ValueError(f"Invalid bit value: {bit!r}")
        value = (value << 1) | bit
    return value


def add_length_prefix(payload_bits: list[Bit], width: int = 16) -> list[Bit]:
    """Prefix a payload with its bit length.

    This is useful later so the receiver knows where the message ends.
    """
    return int_to_bits(len(payload_bits), width) + list(payload_bits)


def remove_length_prefix(frame_bits: list[Bit] | tuple[Bit, ...], width: int = 16) -> list[Bit]:
    """Recover a length-prefixed payload."""
    if len(frame_bits) < width:
        raise ValueError("Not enough bits to read the length prefix")
    payload_length = bits_to_int(frame_bits[:width])
    payload_start = width
    payload_end = payload_start + payload_length
    if len(frame_bits) < payload_end:
        raise ValueError("Frame does not contain the complete payload")
    return list(frame_bits[payload_start:payload_end])

