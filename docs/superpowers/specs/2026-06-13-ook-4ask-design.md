# OOK and 4-ASK Selectable Modulation Design

## Objective

Add 4-ASK grayscale modulation as a second end-to-end modulation mode while
preserving the existing OOK behavior. A transmission uses exactly one mode,
selected independently in transmitter and receiver commands.

The implementation must support:

- Static PNG generation and offline decoding.
- Photo decoding with crop and perspective correction.
- Multi-frame sequence generation and offline decoding.
- Continuous camera reception.
- Reed-Solomon error correction and performance analysis.

## Command Interface

All relevant entry points receive:

```text
--modulation {ook,4ask}
```

The default is `ook`, so existing commands continue to work unchanged.
Transmitter and receiver must use the same value.

Examples:

```powershell
python main_tx_sequence.py --message "Hola" --modulation 4ask --ecc 16
python main_rx_sequence_offline.py --modulation 4ask --ecc 16
python main_rx_video_sequence.py --camera 2 --backend dshow --modulation 4ask --ecc 16
```

## Symbol Mapping

### OOK

OOK remains unchanged:

| Bits | Grayscale level |
|------|-----------------|
| `0`  | 0               |
| `1`  | 255             |

OOK transports one bit per data cell.

### 4-ASK

4-ASK uses four nominal grayscale levels and Gray mapping:

| Bits | Symbol index | Nominal level |
|------|--------------|---------------|
| `00` | 0            | 16            |
| `01` | 1            | 96            |
| `11` | 2            | 176           |
| `10` | 3            | 245           |

Gray mapping limits an adjacent-level decision error to one bit. Packet and
length-prefixed streams are byte aligned, so they always contain an even
number of bits. Generic 4-ASK modulation pads a final odd bit with zero.

4-ASK transports two bits per data cell.

## Frame Layout and Pilots

Finder markers and data-cell positions remain unchanged.

OOK pilots retain alternating black and white references. For 4-ASK, the eight
existing pilot cells cycle through symbol indices `0, 1, 2, 3`, giving two
known samples for every nominal level without reducing the current data area.

The default frame contains 532 data cells:

- OOK: 532 transport bits, 56 packet payload bytes after the 10-byte header.
- 4-ASK: 1064 transport bits, 123 packet payload bytes after the header.

Unused OOK cells keep the current neutral level. Unused 4-ASK cells use symbol
zero so that extra decoded bits do not affect the length-prefixed or
packet-length-delimited payload.

## Calibration and Detection

OOK continues to estimate one adaptive threshold from black and white pilots.

4-ASK calibration:

1. Sample the known pilot cells from the rectified image.
2. Average the two samples associated with each symbol index.
3. Require strictly increasing calibrated centers.
4. Classify every data-cell intensity using the closest calibrated center.
5. Validate finder markers using the midpoint between the lowest and highest
   calibrated levels.

Sampling uses the central region of each macropixel to reduce contamination
from perspective interpolation and neighboring cells.

The decoder exposes either `OokCalibration` or `Ask4Calibration`. CLI output
prints the OOK threshold or the four calibrated 4-ASK levels as appropriate.

## Packet Protocol

The existing final reserved header byte identifies the modulation:

| Value | Modulation |
|-------|------------|
| 0     | OOK        |
| 1     | 4-ASK      |

Existing OOK frames remain compatible because the reserved byte is currently
zero. Packet encoding and decoding receive the expected modulation. A decoded
header whose modulation identifier differs from the receiver setting is
rejected before its payload is stored.

Packet capacity and payload splitting are modulation-aware. Reed-Solomon is
still applied to the complete message before packet splitting.

## Component Boundaries

### `common/modulation.py`

Owns modulation names, validation, bits-per-symbol values, nominal levels,
OOK mapping, and 4-ASK Gray mapping.

### `common/frame_layout.py`

Owns modulation-aware bit capacity and known pilot symbol assignments.

### `transmitter/generator.py`

Places modulation-specific pilots and data symbols in the common frame.

### `receiver/calibration.py`

Estimates OOK or 4-ASK decision parameters from known pilots.

### `receiver/decoder.py`

Samples the rectified grid and dispatches to the selected demodulator.

### `common/packet.py`

Calculates modulation-aware packet capacity and validates the modulation ID in
the packet header.

### Sequence and CLI modules

Propagate the selected modulation through generation, decoding, video capture,
and performance planning.

## Error Handling

- Reject unsupported modulation names.
- Reject decreasing or collapsed 4-ASK calibration centers.
- Reject packet headers with a mismatched modulation ID.
- Preserve the current behavior of waiting for another packet copy when
  Reed-Solomon cannot correct a complete camera sequence.
- Keep OOK as the default in every public API and CLI.

## Verification

Automated tests must prove:

- OOK behavior remains unchanged.
- 4-ASK modulates and demodulates Gray-coded symbols.
- 4-ASK survives linear brightness and contrast changes using pilots.
- Static, photo, perspective, sequence, ECC, and simulated video paths decode
  4-ASK correctly.
- A 500-character message with ECC 16 needs five 4-ASK frames rather than ten
  OOK frames under the default frame configuration.
- Packet decoding rejects transmitter/receiver modulation mismatch.
- All existing tests continue to pass.

Physical validation uses the existing phone-camera setup. The first robust
trial keeps `--duration-ms 400 --repeat 10`; later trials reduce duration only
after BER and packet completion are confirmed.

## Non-Goals

- OOK and 4-ASK are not mixed inside one frame or transmission.
- CSK/RGB and rolling-shutter multiplexing are not part of this implementation.
- No automatic modulation detection is added; both endpoints are configured
  explicitly.
