# CheatCV - Android Game Automation Toolkit

**Status**: Phase 3 Complete - Ready for Live Testing
**Last Updated**: 2025-11-09

Automated coloring game solver using computer vision and ADB. Detects color circles, identifies checkerboard patterns, and fills regions autonomously on Android devices.

---

## Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package
pip install -e .
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
cheatcv hotkey [--debug]

# Hotkeys:
#   F9  - Start/Stop automation toggle
#   ESC - Emergency stop (exit program)
```

**Option B: Standalone Mode**
```bash
cheatcv run [--debug] [--dry-run] [--max-cycles N]

# Flags:
#   --debug       - Verbose logging
#   --dry-run     - Simulate without tapping (CV testing only)
#   --max-cycles  - Maximum automation cycles (default: 500)
```

### 4. Keep Device Awake

```bash
# Start keepalive (random taps every 30s)
cheatcv keepalive [--interval 30] [--width 1080] [--height 2400]

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
cheatcv test circles
cheatcv test patterns

# Test ADB connection
cheatcv test adb

# Test live device detection
cheatcv test live

# Benchmark ADB capture methods
cheatcv benchmark [--iterations N]

# Comprehensive profiling
cheatcv profile [--iterations N] [--scale 0.5]
```

### Validation Results

- ✓ Circle detection: 100% accuracy (detects leftmost, tracks disappearance)
- ✓ Pattern detection: 100% accuracy (dual heuristic: largest ≥1000px OR total ≥3500px)
- ✓ Live device: 2 circles, 12-23 patterns detected correctly
- ✓ Performance: 8.8ms CV processing at 0.5 scale

---

## CLI Reference

CheatCV uses a single entry point with subcommands. Get help for any command with `--help`:

```bash
cheatcv --help                # Show all available commands
cheatcv <command> --help      # Show help for specific command
```

### Main Commands

- **`cheatcv run`** - Run automation on live device
  - `--debug` - Enable debug logging
  - `--dry-run` - Simulate without tapping (CV testing only)
  - `--max-cycles N` - Maximum automation cycles (default: 500)

- **`cheatcv hotkey`** - Run with hotkey control (F9=toggle, ESC=exit)
  - `--debug` - Enable debug logging

- **`cheatcv keepalive`** - Keep device awake with random taps
  - `--interval N` - Seconds between taps (default: 30)
  - `--width N` - Screen width in pixels (default: 1080)
  - `--height N` - Screen height in pixels (default: 2400)

### Testing Commands

- **`cheatcv test circles`** - Test circle detection on sample images
- **`cheatcv test patterns`** - Test pattern detection on sample images
- **`cheatcv test adb`** - Test ADB connection and screen capture
- **`cheatcv test live`** - Test live detection on device screen

### Performance Commands

- **`cheatcv benchmark`** - Benchmark ADB capture methods
  - `--iterations N` - Number of iterations (default: 5)

- **`cheatcv profile`** - Run comprehensive performance profiling
  - `--iterations N` - Number of iterations for capture profiling (default: 10)
  - `--scale F` - Downscale factor for CV (default: 0.5)

---

## Project Structure

```
cheatcv/
├── src/cheatcv/
│   ├── cli.py                 # Main CLI entry point
│   ├── commands/              # Click command modules
│   │   ├── run.py             # Standalone automation runner
│   │   ├── hotkey.py          # Hotkey-controlled runner (F9/ESC)
│   │   ├── keepalive.py       # Keep screen awake (random taps)
│   │   ├── test.py            # Test command group
│   │   ├── benchmark.py       # ADB method comparison
│   │   └── profile.py         # Performance profiling
│   ├── adb/
│   │   └── device.py          # ADB wrapper (capture, tap, swipe)
│   ├── cv/
│   │   ├── circles.py         # Color circle detection (HoughCircles)
│   │   └── patterns.py        # Checkerboard pattern detection
│   └── brain/
│       └── automation.py      # State machine & main logic
│
├── scripts/                   # Legacy scripts (deprecated, use CLI instead)
├── sample/base/               # Reference images (gameplay screenshots)
├── debug_output/              # Annotated detection outputs
├── notes/
│   ├── CHECKPOINT.md          # Current state snapshot
│   └── devlogs/               # Session-by-session logs
├── docs/
│   └── GRIMOIRE.md            # Architecture & design doc
│
├── pyproject.toml             # Dependencies & config
└── README.md                  # This file
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
1. Install the package: `pip install -e .`
2. Start fresh coloring page on device
3. Run `cheatcv hotkey`
4. Press F9 to start automation
5. Monitor state transitions and tap accuracy
6. Measure completion time and success rate

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
