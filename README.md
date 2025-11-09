# CheatCV - Android Game Automation Toolkit

**Status**: Phase 3 Complete - Ready for Live Testing
**Last Updated**: 2025-11-09

Automated coloring game solver using computer vision and ADB. Detects color circles, identifies checkerboard patterns, and fills regions autonomously on Android devices.

---

## Quick Start

### 1. Setup Environment

```bash
# Activate Python environment
source ~/.bashrc.d/pyenv.bash && pyenv activate cheatcv

# Install dependencies (already done)
# uv pip install -r requirements.txt
```

### 2. Connect Android Device

```bash
# Verify ADB connection
adb devices

# Expected output:
# 3d986a0fdf4d    device
```

### 3. Run Automation

**Option A: Hotkey Mode (Recommended)**
```bash
python3 scripts/run_with_hotkey.py

# Hotkeys:
#   F9  - Start/Stop automation toggle
#   ESC - Emergency stop (exit program)
```

**Option B: Standalone Mode**
```bash
python3 scripts/run_automation.py [--debug] [--dry-run]

# Flags:
#   --debug   - Verbose logging
#   --dry-run - Simulate without tapping (CV testing only)
```

### 4. Keep Device Awake

```bash
# Start keepalive (random taps every 30s)
python3 scripts/keepalive.py

# Stop with Ctrl+C
```

---

## Architecture

### State Machine Flow

```
IDLE
  │
  ├─(F9 pressed)─> COLOR_SELECT
  │                    │
  │                    ├─(detect circles)─> Tap leftmost circle
  │                    │
  │                    └─> FILL_LOOP
  │                           │
  │                           ├─(patterns exist)─> Detect all patterns
  │                           │                    Tap ALL patterns
  │                           │                    Loop back
  │                           │
  │                           └─(no patterns)─> NEXT_COLOR
  │                                                 │
  │                                                 ├─(circles remain)─> COLOR_SELECT
  │                                                 │
  │                                                 └─(no circles)─> SUCCESS ─> IDLE
```

### Key Components

**ADB Layer** (`src/cheatcv/adb/device.py`):
- Screen capture (optimized exec-out method)
- Tap with jitter (±5-15px for cloaking)
- Swipe gestures (for future zoom support)

**CV Layer** (`src/cheatcv/cv/`):
- `circles.py`: HoughCircles detection for color selectors
- `patterns.py`: Checkerboard detection via texture variance + morphology

**Brain** (`src/cheatcv/brain/automation.py`):
- State machine with batched tapping
- Random delays (500-1500ms)
- Stats tracking (taps, captures, state transitions)

---

## Performance

### Optimized Configuration

- **Downscale**: 0.5 (540x1200 for CV)
- **Capture method**: exec-out (no improvement over traditional, but cleaner)
- **Batching**: Tap ALL patterns per capture

### Timing Breakdown (per cycle)

| Component | Time | % of Total |
|-----------|------|------------|
| ADB Capture | 1200ms | 91.7% |
| Circle Detection | 2.5ms | 0.2% |
| Pattern Detection | 6.3ms | 0.5% |
| Tap Operation | 100ms | 7.6% |
| **TOTAL** | **1309ms** | **100%** |

### Effective Performance (Batched Taps)

- **10 taps/capture**: 221ms per tap ✓
- **20 taps/capture**: 161ms per tap ✓✓
- **Estimated full automation**: 2-3 minutes per image

**Note**: Original <300ms target was unrealistic for ADB (hardware limitation). Batched tapping strategy achieves effective <300ms per tap.

---

## Testing & Validation

### Run Tests

```bash
# Test CV detection on samples
python3 scripts/test_circles.py
python3 scripts/test_patterns.py

# Test live device detection
python3 scripts/test_live_detection.py

# Benchmark ADB capture methods
python3 scripts/benchmark_capture.py

# Comprehensive profiling
python3 scripts/profile_full_pipeline.py
```

### Validation Results

- ✓ Circle detection: 100% accuracy (detects leftmost, tracks disappearance)
- ✓ Pattern detection: 100% accuracy (dual heuristic: largest ≥1000px OR total ≥3500px)
- ✓ Live device: 2 circles, 12-23 patterns detected correctly
- ✓ Performance: 8.8ms CV processing at 0.5 scale

---

## Project Structure

```
cheatcv/
├── src/cheatcv/
│   ├── adb/
│   │   └── device.py           # ADB wrapper (capture, tap, swipe)
│   ├── cv/
│   │   ├── circles.py          # Color circle detection (HoughCircles)
│   │   └── patterns.py         # Checkerboard pattern detection
│   └── brain/
│       └── automation.py       # State machine & main logic
│
├── scripts/
│   ├── keepalive.py           # Keep screen awake (random taps)
│   ├── run_automation.py      # Standalone automation runner
│   ├── run_with_hotkey.py     # Hotkey-controlled runner (F9/ESC)
│   ├── test_*.py              # Unit tests for components
│   ├── benchmark_capture.py   # ADB method comparison
│   └── profile_full_pipeline.py # Performance profiling
│
├── sample/base/               # Reference images (gameplay screenshots)
├── debug_output/              # Annotated detection outputs
├── notes/
│   ├── CHECKPOINT.md          # Current state snapshot
│   └── devlogs/              # Session-by-session logs
├── docs/
│   └── GRIMOIRE.md           # Architecture & design doc
│
├── pyproject.toml            # Dependencies & config
└── README.md                 # This file
```

---

## Key Findings

1. **ADB is the bottleneck** (~900ms capture, hardware limitation)
2. **Batched taps are essential** (8x effective speedup)
3. **Downscaling is "free" performance** (5.4x faster CV, minimal detection loss)
4. **CV is NOT the bottleneck** (8.8ms total, only 0.7% of cycle)
5. **exec-out didn't help** (actually slightly slower than traditional)

---

## Next Steps

**Ready for live testing**:
1. Start fresh coloring page on device
2. Run `scripts/run_with_hotkey.py`
3. Press F9 to start automation
4. Monitor state transitions and tap accuracy
5. Measure completion time and success rate

**Future enhancements** (Phase 4):
- Ad detection & handling
- Zoom logic (pinch gestures)
- Retry logic & error recovery
- Auto-new-image menu navigation

---

## Documentation

- **CHECKPOINT.md**: Quick resume point for fresh sessions
- **GRIMOIRE.md**: Complete architecture & design specification
- **Session devlogs**: `notes/devlogs/YYYYMMDD_XX-*.md`
  - `20251109_01-foundations.md`: Keepalive, ADB, CV
  - `20251109_02-optimization-statemachine.md`: Optimization, state machine

---

## Dependencies

- Python 3.13+
- opencv-python ≥4.8.0
- numpy ≥1.26.0
- pillow ≥10.0.0
- adbutils ≥2.0.0
- pynput ≥1.7.6

---

## License

See LICENSE file.

---

**Generated with Claude Code** 🤖
