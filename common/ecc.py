"""Error-correction helpers for the optical modem."""

from __future__ import annotations

from dataclasses import dataclass

from reedsolo import RSCodec


@dataclass(frozen=True)
class ReedSolomonDecodeResult:
    """Decoded Reed-Solomon payload and correction metadata."""

    payload: bytes
    corrected_symbols: int


def encode_reed_solomon(payload: bytes, parity_bytes: int) -> bytes:
    """Append Reed-Solomon parity bytes to a payload."""
    _validate_parity_bytes(parity_bytes)
    return bytes(RSCodec(parity_bytes).encode(payload))


def decode_reed_solomon(encoded_payload: bytes, parity_bytes: int) -> ReedSolomonDecodeResult:
    """Correct a Reed-Solomon encoded payload."""
    _validate_parity_bytes(parity_bytes)
    decoded_payload, _, errata_positions = RSCodec(parity_bytes).decode(encoded_payload)
    return ReedSolomonDecodeResult(
        payload=bytes(decoded_payload),
        corrected_symbols=len(errata_positions),
    )


def _validate_parity_bytes(parity_bytes: int) -> None:
    if parity_bytes <= 0:
        raise ValueError("parity_bytes must be positive")
    if parity_bytes > 64:
        raise ValueError("parity_bytes must be 64 or less for this project stage")

