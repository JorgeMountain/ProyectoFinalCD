# Screen-Camera Optical Modem

Python implementation of an optical modem that transmits text from a screen to a camera using visual frames. The project covers the complete path from bit packing and frame generation to camera capture, perspective correction, Reed-Solomon error correction, multi-frame packet reconstruction, BER measurement, and selectable OOK / 4-ASK modulation.

This was built as a Digital Communications final project, but the repository is organized as a portfolio project: the first screen explains what it does, how it works, how to run it, and where to inspect the technical decisions.

## Highlights

- Screen-to-camera communication using generated PNG frames.
- OOK modulation for robustness and 4-ASK modulation for higher data density.
- Gray-coded 4-ASK levels with pilot-based calibration.
- Reed-Solomon error correction over transmitted payload bytes.
- Multi-frame packet protocol with sequence numbers and payload length.
- Automatic screen detection and perspective correction for real camera input.
- Offline and live-camera receivers.
- BER and throughput analysis tools.
- Unit tests covering the staged transmitter, receiver, ECC, packet, and modulation behavior.

## Current Capability

With the default 1280 x 720 frame and 32 x 18 grid:

| Modulation | Bits per cell | Useful payload per frame | 500-byte message with ECC 16 |
| --- | ---: | ---: | ---: |
| OOK | 1 | 56 bytes | 10 frames |
| 4-ASK | 2 | 123 bytes | 5 frames |

4-ASK improves throughput by encoding two bits per data cell, while OOK remains the simpler and more robust fallback for noisy capture conditions.

## Repository Structure

```text
common/        Shared protocol, ECC, modulation, metrics, frame layout, PNG I/O
transmitter/   Frame and sequence generation
receiver/      Offline, photo, perspective, and live video decoding
tests/         Unit tests for the staged implementation
docs/          Commands, code map, theory notes, defense guide, design notes
data/          Runtime data folder; generated captures and frames are ignored
```

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest tests
```

Generate and decode a 4-ASK sequence offline:

```powershell
python main_tx_sequence.py --message "Hola mundo" --ecc 16 --modulation 4ask
python main_rx_sequence_offline.py --input-dir data/generated/sequence --ecc 16 --modulation 4ask --expected "Hola mundo"
```

Analyze estimated performance for a 500-byte message:

```powershell
python main_analyze_performance.py --ecc 16 --modulation 4ask --duration-ms 150
```

## Live Camera Demo

Find the camera index:

```powershell
python main_rx_video_sequence.py --scan-cameras --scan-max 6 --backend dshow
```

Start the receiver:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 16 --modulation 4ask --preview --max-frames 0 --expected-message "Hola mundo"
```

In a second terminal, show the transmitter:

```powershell
python main_tx_sequence.py --message "Hola mundo" --ecc 16 --modulation 4ask --show --duration-ms 500 --repeat 20
```

Both sides must use the same `--ecc` and `--modulation` values.

## Main Scripts

| Script | Purpose |
| --- | --- |
| `main_tx_static.py` | Generate one static visual frame. |
| `main_rx_offline.py` | Decode one generated frame without camera input. |
| `main_rx_photo.py` | Decode a real photo of the transmitted frame. |
| `main_tx_sequence.py` | Generate and optionally display a multi-frame transmission. |
| `main_rx_sequence_offline.py` | Decode a folder of generated sequence frames. |
| `main_rx_video_sequence.py` | Receive and decode live video from a camera. |
| `main_analyze_performance.py` | Estimate frames, time, throughput, and BER. |

## Documentation

- [Command cookbook](docs/commands_es.md)
- [Code map and modification guide](docs/code_map_es.md)
- [Defense guide](docs/defense_guide_es.md)
- [Theory guide](docs/theory_guide_es.md)
- [Implementation decision record](docs/decision_record_es.pdf)
- [4-ASK design notes](docs/design/ook_4ask_design.md)
- [4-ASK implementation plan](docs/design/ook_4ask_implementation_plan.md)

## Verification

The project is validated with:

```powershell
python -m pytest tests
```

A successful run verifies the transmitter/receiver pipeline, packet reconstruction, ECC flow, BER helpers, and selectable OOK / 4-ASK modulation paths.
