"""Small grayscale PNG writer using only Python's standard library."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def write_grayscale_png(path: str | Path, pixels: list[list[int]]) -> None:
    """Write an 8-bit grayscale PNG image.

    pixels must be a rectangular list of rows with values in [0, 255].
    """
    if not pixels:
        raise ValueError("pixels cannot be empty")

    height = len(pixels)
    width = len(pixels[0])
    if width == 0:
        raise ValueError("pixel rows cannot be empty")

    raw_rows = bytearray()
    for row in pixels:
        if len(row) != width:
            raise ValueError("all pixel rows must have the same width")
        raw_rows.append(0)  # PNG filter type 0: none.
        for value in row:
            if not 0 <= value <= 255:
                raise ValueError(f"invalid grayscale value: {value!r}")
            raw_rows.append(value)

    image_header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    compressed = zlib.compress(bytes(raw_rows), level=9)

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(
        PNG_SIGNATURE
        + _chunk(b"IHDR", image_header)
        + _chunk(b"IDAT", compressed)
        + _chunk(b"IEND", b"")
    )

