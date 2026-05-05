"""Performance and error metrics for modem experiments."""

from __future__ import annotations

from common.bit_utils import bytes_to_bits


def bit_error_count(expected: bytes, received: bytes) -> int:
    """Count bit errors between two byte strings, including length mismatch."""
    expected_bits = bytes_to_bits(expected)
    received_bits = bytes_to_bits(received)
    common_length = min(len(expected_bits), len(received_bits))
    errors = sum(1 for index in range(common_length) if expected_bits[index] != received_bits[index])
    errors += abs(len(expected_bits) - len(received_bits))
    return errors


def bit_error_rate(expected: bytes, received: bytes) -> float:
    """Compute BER using the longer stream as denominator."""
    total_bits = max(len(expected), len(received)) * 8
    if total_bits == 0:
        return 0.0
    return bit_error_count(expected, received) / total_bits


def text_bit_error_rate(expected: str, received: str, encoding: str = "utf-8") -> float:
    """Compute BER between two text strings."""
    return bit_error_rate(expected.encode(encoding), received.encode(encoding))

