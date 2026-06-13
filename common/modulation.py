"""Simple symbol mappings for the first project milestones."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

from common.bit_utils import Bit


Modulation = Literal["ook", "4ask"]
MODULATION_CHOICES: tuple[Modulation, Modulation] = ("ook", "4ask")
ASK4_LEVELS = (16, 96, 176, 245)
ASK4_BITS: tuple[tuple[Bit, Bit], ...] = ((0, 0), (0, 1), (1, 1), (1, 0))
_MODULATION_IDS: dict[Modulation, int] = {"ook": 0, "4ask": 1}


def normalize_modulation(value: str) -> Modulation:
    """Normalize and validate a public modulation name."""
    normalized = value.strip().lower()
    if normalized not in MODULATION_CHOICES:
        raise ValueError(f"Unsupported modulation: {value!r}")
    return normalized  # type: ignore[return-value]


def bits_per_symbol(modulation: str) -> int:
    """Return the number of data bits carried by one visual cell."""
    return 1 if normalize_modulation(modulation) == "ook" else 2


def modulation_id(modulation: str) -> int:
    """Return the packet header identifier for a modulation."""
    return _MODULATION_IDS[normalize_modulation(modulation)]


def modulation_from_id(value: int) -> Modulation:
    """Return the modulation represented by a packet header identifier."""
    for modulation, identifier in _MODULATION_IDS.items():
        if identifier == value:
            return modulation
    raise ValueError(f"Unsupported modulation identifier: {value}")


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


def ask4_modulate(
    bits: Iterable[Bit],
    levels: tuple[int, int, int, int] = ASK4_LEVELS,
) -> list[int]:
    """Map bit pairs to four Gray-coded grayscale levels."""
    bit_list = list(bits)
    for bit in bit_list:
        if bit not in (0, 1):
            raise ValueError(f"Invalid bit value: {bit!r}")
    if len(bit_list) % 2:
        bit_list.append(0)

    pair_to_index = {pair: index for index, pair in enumerate(ASK4_BITS)}
    return [
        levels[pair_to_index[(bit_list[index], bit_list[index + 1])]]
        for index in range(0, len(bit_list), 2)
    ]


def ask4_demodulate(
    symbols: Iterable[float],
    reference_levels: tuple[float, float, float, float] = ASK4_LEVELS,
) -> list[Bit]:
    """Recover Gray-coded bit pairs using the nearest calibrated level."""
    if any(
        reference_levels[index] >= reference_levels[index + 1]
        for index in range(len(reference_levels) - 1)
    ):
        raise ValueError("4-ASK reference levels must be strictly increasing")

    bits: list[Bit] = []
    for symbol in symbols:
        symbol_index = min(
            range(len(reference_levels)),
            key=lambda index: abs(symbol - reference_levels[index]),
        )
        bits.extend(ASK4_BITS[symbol_index])
    return bits


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
