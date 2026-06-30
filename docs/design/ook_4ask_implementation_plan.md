# OOK and 4-ASK Selectable Modulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add selectable OOK and 4-ASK modulation to every transmitter and receiver path while preserving OOK compatibility.

**Architecture:** Modulation primitives define bits per symbol and Gray-coded grayscale levels. Frame generation, pilot calibration, packet capacity, sequence processing, performance analysis, and CLI entry points receive a modulation name with `ook` as the default. The packet reserved byte carries a modulation ID so mismatched endpoints are rejected.

**Tech Stack:** Python 3.12, OpenCV, NumPy, reedsolo, unittest/pytest.

---

### Task 1: Modulation Primitives and Frame Capacity

**Files:**
- Modify: `common/modulation.py`
- Modify: `common/frame_layout.py`
- Test: `tests/test_part1.py`
- Test: `tests/test_part2.py`

- [ ] **Step 1: Add failing tests for 4-ASK Gray mapping**

Add tests asserting:

```python
bits = [0, 0, 0, 1, 1, 1, 1, 0]
symbols = ask4_modulate(bits)
self.assertEqual(symbols, [16, 96, 176, 245])
self.assertEqual(ask4_demodulate(symbols), bits)
self.assertEqual(bits_per_symbol("ook"), 1)
self.assertEqual(bits_per_symbol("4ask"), 2)
```

- [ ] **Step 2: Run the focused tests and verify failure**

Run:

```powershell
python -m pytest tests/test_part1.py tests/test_part2.py -q
```

Expected: import or assertion failures because 4-ASK APIs do not exist.

- [ ] **Step 3: Implement modulation names and Gray mapping**

Add to `common/modulation.py`:

```python
Modulation = Literal["ook", "4ask"]
MODULATION_CHOICES = ("ook", "4ask")
ASK4_LEVELS = (16, 96, 176, 245)
ASK4_BITS = ((0, 0), (0, 1), (1, 1), (1, 0))

def normalize_modulation(value: str) -> Modulation: ...
def bits_per_symbol(modulation: str) -> int: ...
def modulation_id(modulation: str) -> int: ...
def modulation_from_id(value: int) -> Modulation: ...
def ask4_modulate(bits: Iterable[Bit], levels=ASK4_LEVELS) -> list[int]: ...
def ask4_demodulate(symbols: Iterable[float], reference_levels=ASK4_LEVELS) -> list[Bit]: ...
```

`ask4_demodulate` selects the nearest reference center and expands its Gray
pair. `ask4_modulate` pads one trailing zero only when the input is odd.

- [ ] **Step 4: Make frame capacity and pilots modulation-aware**

Add to `common/frame_layout.py`:

```python
def pilot_cells_with_symbols(config, modulation="ook") -> list[tuple[Cell, int]]:
    symbol_count = 2 if normalize_modulation(modulation) == "ook" else 4
    return [(cell, index % symbol_count) for index, cell in enumerate(pilot_cells(config))]

def data_capacity_bits(config=DEFAULT_FRAME_CONFIG, modulation="ook") -> int:
    return len(data_cells(config)) * bits_per_symbol(modulation)

def require_capacity(bits, config, modulation="ook") -> list[int]:
    ...
```

Keep `pilot_cells_with_bits()` as an OOK compatibility wrapper.

- [ ] **Step 5: Run focused tests**

Run:

```powershell
python -m pytest tests/test_part1.py tests/test_part2.py -q
```

Expected: PASS.

### Task 2: Static Frame Generation and Adaptive 4-ASK Calibration

**Files:**
- Modify: `transmitter/generator.py`
- Modify: `receiver/calibration.py`
- Modify: `receiver/decoder.py`
- Test: `tests/test_part3.py`
- Test: `tests/test_part4.py`
- Test: `tests/test_part7.py`

- [ ] **Step 1: Add failing static 4-ASK tests**

Cover:

```python
generate_static_frame("Hola mundo", output_path=path, modulation="4ask")
result = decode_static_frame(path, modulation="4ask")
self.assertEqual(result.message, "Hola mundo")
```

Also transform pixels with a linear brightness/contrast change and assert
successful 4-ASK decoding from adaptive pilots.

- [ ] **Step 2: Run static tests and verify failure**

Run:

```powershell
python -m pytest tests/test_part3.py tests/test_part4.py tests/test_part7.py -q
```

Expected: failures because generator and decoder do not accept `modulation`.

- [ ] **Step 3: Generate modulation-specific pilots and symbols**

Extend these APIs with `modulation: str = "ook"`:

```python
build_frame_grid(bits, config=DEFAULT_FRAME_CONFIG, modulation="ook")
generate_static_frame(..., modulation="ook")
```

OOK uses existing levels. 4-ASK uses `ASK4_LEVELS`, places each pilot's known
symbol level, and fills unused data cells with symbol zero.

- [ ] **Step 4: Add 4-ASK calibration**

Add:

```python
@dataclass(frozen=True)
class Ask4Calibration:
    levels: tuple[float, float, float, float]
    thresholds: tuple[float, float, float]
    contrast: float
    markers_valid: bool

def estimate_ask4_calibration(grid_levels, config=DEFAULT_FRAME_CONFIG) -> Ask4Calibration:
    ...
```

Average pilots by symbol index, require increasing centers, calculate adjacent
midpoints, and validate markers using the midpoint of the extreme centers.

- [ ] **Step 5: Dispatch decoder by modulation**

Extend:

```python
decode_static_frame(..., modulation="ook")
decode_static_pixels(..., modulation="ook")
decode_data_bits(..., modulation="ook")
```

OOK keeps adaptive threshold behavior. 4-ASK rejects a manual OOK threshold,
uses `estimate_ask4_calibration`, and calls `ask4_demodulate`.

Change `sample_grid_levels` to average the central 60% of normal-sized cells,
falling back to the complete cell for very small test grids.

- [ ] **Step 6: Run static, calibration, and ECC tests**

Run:

```powershell
python -m pytest tests/test_part3.py tests/test_part4.py tests/test_part7.py -q
```

Expected: PASS for OOK and 4-ASK.

### Task 3: Modulation-Aware Packet Protocol

**Files:**
- Modify: `common/packet.py`
- Test: `tests/test_part8.py`

- [ ] **Step 1: Add failing packet tests**

Assert:

```python
self.assertEqual(packet_payload_capacity(modulation="ook"), 56)
self.assertEqual(packet_payload_capacity(modulation="4ask"), 123)
```

Encode a 4-ASK packet, decode it with expected `4ask`, and verify that decoding
with expected `ook` raises `ValueError`.

- [ ] **Step 2: Run packet tests and verify failure**

Run:

```powershell
python -m pytest tests/test_part8.py -q
```

Expected: failures because packet APIs are not modulation-aware.

- [ ] **Step 3: Store modulation ID in the reserved header byte**

Extend:

```python
packet_payload_capacity(config=DEFAULT_FRAME_CONFIG, modulation="ook")
encode_packet(packet, config=DEFAULT_FRAME_CONFIG, modulation="ook")
decode_packet(frame_bits, expected_modulation="ook")
split_payload(payload, config=DEFAULT_FRAME_CONFIG, modulation="ook")
```

Use `data_capacity_bits()` for capacity. Write modulation ID to header byte 9.
Reject unknown or mismatched IDs while retaining zero as OOK compatibility.

- [ ] **Step 4: Run packet tests**

Run:

```powershell
python -m pytest tests/test_part8.py -q
```

Expected: PASS.

### Task 4: Multi-Frame Sequence and Performance Planning

**Files:**
- Modify: `transmitter/sequence.py`
- Modify: `receiver/sequence_decoder.py`
- Modify: `common/performance.py`
- Test: `tests/test_part8.py`
- Test: `tests/test_part9.py`

- [ ] **Step 1: Add failing 500-character sequence tests**

Generate and decode:

```python
generated = generate_frame_sequence(
    "A" * 500,
    output_dir=tmpdir,
    error_correction_bytes=16,
    modulation="4ask",
)
decoded = decode_sequence_folder(
    tmpdir,
    error_correction_bytes=16,
    modulation="4ask",
)
self.assertEqual(len(generated.frame_paths), 5)
self.assertEqual(decoded.message, "A" * 500)
```

Add a performance assertion that OOK needs ten frames and 4-ASK needs five.

- [ ] **Step 2: Run sequence/performance tests and verify failure**

Run:

```powershell
python -m pytest tests/test_part8.py tests/test_part9.py -q
```

Expected: unexpected keyword failures for `modulation`.

- [ ] **Step 3: Propagate modulation through sequence generation**

Extend `generate_frame_sequence()` and `GeneratedSequence` with modulation.
Use modulation-aware splitting, packet encoding, and frame-grid generation.

- [ ] **Step 4: Propagate modulation through sequence decoding**

Extend:

```python
decode_packet_from_pixels(..., modulation="ook")
decode_packet_from_image(..., modulation="ook")
decode_sequence_folder(..., modulation="ook")
decode_video_stream(..., modulation="ook")
```

Pass the selected mode to data demodulation and packet-header validation.
Preserve reception timing and ECC retry behavior.

- [ ] **Step 5: Make performance planning modulation-aware**

Extend `plan_transmission()` and `longest_message_bytes_for_goal()` with
`modulation="ook"` and calculate capacity using that mode.

- [ ] **Step 6: Run sequence/performance tests**

Run:

```powershell
python -m pytest tests/test_part8.py tests/test_part9.py -q
```

Expected: PASS, including five 4-ASK frames for 500 characters with ECC 16.

### Task 5: Photo Path, CLI Commands, and Documentation

**Files:**
- Modify: `receiver/photo_decoder.py`
- Modify: `main_tx_static.py`
- Modify: `main_rx_offline.py`
- Modify: `main_rx_photo.py`
- Modify: `main_tx_sequence.py`
- Modify: `main_rx_sequence_offline.py`
- Modify: `main_rx_video_sequence.py`
- Modify: `main_analyze_performance.py`
- Modify: `README.md`
- Test: `tests/test_part5.py`
- Test: `tests/test_part6.py`

- [ ] **Step 1: Add failing photo and perspective tests**

Generate 4-ASK frames and verify:

```python
decode_photo_frame(frame, modulation="4ask")
decode_photo_frame(warped_photo, auto_perspective=True, modulation="4ask")
```

- [ ] **Step 2: Run photo tests and verify failure**

Run:

```powershell
python -m pytest tests/test_part5.py tests/test_part6.py -q
```

Expected: unexpected keyword failures.

- [ ] **Step 3: Propagate modulation through photo decoding**

Extend `decode_photo_frame(..., modulation="ook")` and pass it to
`decode_static_pixels`.

- [ ] **Step 4: Add CLI choices**

Every relevant parser receives:

```python
parser.add_argument(
    "--modulation",
    choices=MODULATION_CHOICES,
    default="ook",
    help="Esquema de modulacion visual.",
)
```

Pass the value through all calls. Print the selected modulation and print
either the OOK threshold or calibrated 4-ASK levels.

- [ ] **Step 5: Document commands**

Add README examples for:

```powershell
python main_tx_sequence.py --message-file mensaje_500.txt --modulation 4ask --ecc 16 --show --windowed --window-width 900 --window-height 506 --window-x 20 --window-y 100 --duration-ms 400 --repeat 10
python main_rx_video_sequence.py --camera 2 --backend dshow --modulation 4ask --ecc 16 --preview --preview-window "980,20,900,500" --max-frames 0
```

- [ ] **Step 6: Run photo tests and CLI help checks**

Run:

```powershell
python -m pytest tests/test_part5.py tests/test_part6.py -q
python main_tx_sequence.py --help
python main_rx_video_sequence.py --help
```

Expected: tests pass and both help outputs list `--modulation {ook,4ask}`.

### Task 6: Simulated Video and Full Verification

**Files:**
- Modify: `tests/test_part8.py`

- [ ] **Step 1: Add an actual-frame simulated video test**

Generate a short 4-ASK sequence, load each PNG as BGR frames, patch
`_open_capture` with a capture object that returns those frames, and call:

```python
result = decode_video_stream(
    auto_perspective=False,
    error_correction_bytes=16,
    modulation="4ask",
    max_frames=len(frames),
)
```

Assert exact message recovery and non-negative reception time.

- [ ] **Step 2: Run the simulated video test**

Run:

```powershell
python -m pytest tests/test_part8.py -q
```

Expected: PASS.

- [ ] **Step 3: Run complete verification**

Run:

```powershell
python -m pytest tests
python -m compileall common transmitter receiver main_*.py
git diff --check
```

Expected: all tests pass, compilation succeeds, and diff check has no errors.

- [ ] **Step 4: Run offline 500-character smoke test**

Run:

```powershell
$message = "A" * 500
python main_tx_sequence.py --message $message --modulation 4ask --ecc 16
python main_rx_sequence_offline.py --modulation 4ask --ecc 16 --expected $message
```

Expected:

```text
Frames generados: 5
Paquetes recibidos: 5/5
BER: 0
```

- [ ] **Step 5: Commit implementation**

Stage only the OOK/4-ASK implementation, tests, plan, and README. Do not stage
`mensaje_500.txt` unless explicitly requested.

```powershell
git add common transmitter receiver tests main_*.py README.md docs/superpowers/plans/2026-06-13-ook-4ask-implementation.md
git commit -m "feat: add selectable 4-ASK optical modulation"
```
