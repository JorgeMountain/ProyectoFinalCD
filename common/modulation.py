"""Simple symbol mappings for the first project milestones."""

from __future__ import annotations

from collections.abc import Iterable

from common.bit_utils import Bit


def ook_modulate(bits: Iterable[Bit], zero_level: int = 0, one_level: int = 255) -> list[int]:
    """Map bits to On-Off Keying grayscale levels."""
    symbols: list[int] = []
    for bit in bits:
        if bit == 0:
            symbols.append(zero_level)
        elif bit == 1:
            symbols.append(one_level)
        else:
            raise ValueError(f"Invalid bit value: {bit!r}")
    return symbols


def ook_demodulate(symbols: Iterable[float], threshold: float = 127.5) -> list[Bit]:
    """Recover bits from OOK grayscale levels using a fixed threshold."""
    return [1 if symbol >= threshold else 0 for symbol in symbols]


def bpsk_modulate(bits: Iterable[Bit]) -> list[int]:
    """Map bits to BPSK symbols: 0 -> -1, 1 -> +1."""
    symbols: list[int] = []
    for bit in bits:
        if bit == 0:
            symbols.append(-1)
        elif bit == 1:
            symbols.append(1)
        else:
            raise ValueError(f"Invalid bit value: {bit!r}")
    return symbols


def bpsk_demodulate(symbols: Iterable[float]) -> list[Bit]:
    """Recover bits from BPSK symbols using zero as the decision boundary."""
    return [1 if symbol >= 0 else 0 for symbol in symbols]


def manchester_encode(bits: Iterable[Bit]) -> list[Bit]:
    """Encode bits with Manchester chips.

    Convention used here:
    - 0 -> 10
    - 1 -> 01
    """
    chips: list[Bit] = []
    for bit in bits:
        if bit == 0:
            chips.extend([1, 0])
        elif bit == 1:
            chips.extend([0, 1])
        else:
            raise ValueError(f"Invalid bit value: {bit!r}")
    return chips


def manchester_decode(chips: list[Bit] | tuple[Bit, ...], strict: bool = True) -> list[Bit]:
    """Decode Manchester chips back into bits."""
    if len(chips) % 2 != 0:
        raise ValueError("Manchester chip stream length must be even")

    bits: list[Bit] = []
    for start in range(0, len(chips), 2):
        pair = tuple(chips[start : start + 2])
        if pair == (1, 0):
            bits.append(0)
        elif pair == (0, 1):
            bits.append(1)
        elif strict:
            raise ValueError(f"Invalid Manchester pair: {pair!r}")
        else:
            # Fallback for noisy pairs: choose by the second chip.
            bits.append(1 if pair[1] >= pair[0] else 0)
    return bits

