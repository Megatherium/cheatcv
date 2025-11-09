# Project Paintrape: ADB-Powered Android Coloring Game Automation with CV Pattern Detection and Ad Handling

**Created**: 2025-11-09T00:00:00Z
**Updated**: 2025-11-09T00:00:00Z

## Project Overview and Intention

**Goal:** Create a Python automation script for a free-to-play Android coloring game on real hardware (via ADB over USB/WiFi). The game starts with a white canvas outlined in black lines. Workflow:

- Detect and select the leftmost color circle (contains a number; activates with raised Y-position and extra grey outline).
- Identify regions overlaid with a light/dark grey checkerboard pattern (#858585 and #d1d1d1 RGB greys; density varies with zoom) as fillable areas.
- Click (tap) those regions to apply the color, repeating until the color circle disappears (indicating all areas for that color are filled).
- Cycle through all colors sequentially until no color circles remain (success signal).
- Handle interruptions from ads (common in F2P apps) by detecting ad overlays and dismissing/closing them automatically.
- Support pinch-zoom for tiny patterns (auto-trigger if detection fails at current scale).
- Trigger via host hotkey; manual restart for new images initially.

**Key Insights from User:**

- Patterns are not fixed-size grids; variable density based on zoom—use texture/contour-based detection, not rigid chessboard corners.
- Real hardware ADB: No emulator quirks, but ensure stable connection.
- Cloaking: Human-like with 500-1500ms random delays; simple curved gestures for zooms (e.g., approximate Bezier via sequential ADB swipes—math details below).
- Ad Handling: "Turnstyle hopping" – Detect modal ad screens (e.g., full-screen overlays, close buttons) and interact to skip/resume.
- Fun Factor: Build iteratively, debug visually, learn CV tricks like Gabor filters for textures.

**Core Workflow (State Machine):**

1. **Idle/Wait:** Hotkey toggle.
2. **Color Select:** Locate leftmost circle → Tap to activate.
3. **Fill Loop:** Detect patterns → Tap regions (with jitter) → Recheck circle presence.
4. **Next Color:** If circle gone, repeat for next leftmost.
5. **Success:** No circles → Stop/pause.
6. **Interrupts:** Ad detected → Handle (close/skip) → Resume.
7. **Zoom Adjust:** If few/no patterns but circles present, pinch out/in.

**Success Criteria:**

- End-to-end coloring of one image in <10min (human speed).
- Robust ad skipping without false positives.
- <300ms per cycle (capture + detect + tap) on Ryzen 7 4750U.
- Debug mode: Step-by-step (e.g., keypress to scan/confirm detection/tap).
- Extensible: Later auto-new-image via menu detection.

**Why Python?** Balances CV prototyping (OpenCV for greys/textures) with ADB subprocesses. No NNs—thresholding + morphology for patterns.

## Tech Stack

**Primary Language:** Python 3.13+.

**Core Libraries:**

- **OpenCV (`cv2`)**: HSV/gray thresholding for greys (#858585≈RGB(133,133,133), #d1d1d1≈RGB(209,209,209)); contour finding + texture variance for patterns; circle detection (HoughCircles) for color selectors.
- **NumPy**: Region masking, random jitter.
- **adbutils** or **subprocess** + `adb` CLI: Screencap (`adb exec-out screencap -p > /dev/stdout`), taps (`adb shell input tap x y`), swipes for zoom.
- **Pillow (PIL)**: PNG decoding from ADB.
- **keyboard**/**pynput**: X11-compatible hotkeys (e.g., Ctrl+Alt+S for step, Ctrl+Alt+R for run).
- **evdev** (optional Linux): Low-level input if needed, but ADB suffices.

**Cloaking Utils:**

- Random: `numpy.random.uniform(500,1500)/1000` for delays.
- Curves: Simple quadratic Bezier approximation for pinch (2-finger: start mid, curve to opposed ends—math: parametric t=0..1, P0=start, P1=control (offset 20-50px perpendicular), P2=end; sequence 5-10 ADB swipe micro-steps).

**Dev Tools:**

- VS Code; `cProfile` for perf; virtualenv.
- ADB: `adb devices` for hardware; enable USB debugging.

**Install Commands:**

```bash
pip install opencv-python numpy pillow adbutils keyboard pynput evdev
```

## System Requirements & Setup

- **Host:** Linux (X11, Cinnamon) – Test hotkeys with `xev`.
- **Device:** Real Android hardware; ADB authorized (`adb usb` or WiFi).
- **Hardware:** Ryzen 7 4750U + 32GB → Fine for 5-10Hz loops.
- **Capture:** ADB raw PNG (fast, no files).
- **Input:** ADB tap/swipe (cloaked delays).
- **Zoom Math Note:** For non-diametric pinch: Use Bezier for finger paths—P0=(x1,y1), P1=(x1 + perp_offset, y1 + curve_offset), P2=(x2,y2) where perp is rotated vector; sample at dt=0.1 for swipe chain.

## Implementation Plan (User-Structured Phases)

Follow this exact stepwise structure. Each phase ends with tests, debugging (visual imshows, logs), and docs (inline comments + README.md updates). Use debug mode: Hotkey steps (e.g., 'S' to scan, 'T' to tap preview, 'C' to confirm).

### Phase 1: Eyes – Layout Detection (CV Components)

- **Color Circles:** HoughCircles on HSV (isolate circle hue/sat; detect raised Y via centroid shift + grey ring via Canny edges around).
- **Checkerboard Patterns:** Grayscale → Threshold to binary (greys as high-contrast); morphology (erode/dilate) for noise; contour hierarchy for closed regions; filter by area (>50px²) + texture (local std dev >20 for checkers—Gabor filter optional for density).
- **Ad Detection:** Template match common ad elements (e.g., close X, play button) or full-screen non-canvas coverage (>70% screen change from baseline).
- **Zoom Scale:** Compute pattern density (contours per unit area); if <threshold, trigger zoom.
- **Tests/Debug:** Mock images (generate procedurals or user samples if provided); assert detections on varied zooms; log false positives.
- **Docs:** CV pipeline diagram (Mermaid in README).
- _Resources:_ The sample/base directory contains 5 files:
  1. 01-start.jpg - Shows the completely fresh, started image
  2. 02-selected.jpg - Shows both the change to the colour circle (bottom left) as well as the checkerboard pattern appearing
  3. 02.1-zoom.jpg - Shows the checkboard pattern up close
  4. 03-colored - Shows area that used to be checkerboard colored in
  5. 04-color_done - Shows that the color circle on the bottom left disappears when all areas have been clicked

### Phase 2: Nerves – ADB Communication

- **Capture:** `adb exec-out screencap -p` → BytesIO → PIL/OpenCV.
- **Taps:** `adb shell input tap {x} {y}` with jitter (±5-15px uniform).
- **Zooms:** Pinch out/in via 2-finger swipes: Chain 8-12 micro-swipes along simple Bezier (quadratic: B(t) = (1-t)^2*P0 + 2(1-t)t*P1 + t^2\*P2; t in [0,1], step 0.1; P1 offset perpendicular to vector for curve—avoid straight lines).
- **Ad Gestures:** Swipe-to-close or tap close button coords.
- **Error Handling:** Retry on ADB timeouts; ping device health.
- **Tests/Debug:** Unit tests for ADB wrappers (mock subprocess); time roundtrips (<100ms expected).
- **Docs:** ADB command cheatsheet; connection script.

### Phase 3: Brain – Process Logic & Step-by-Step Debug Mode

- **State Enum:** IDLE, SELECT_COLOR, FILLING, AD_INTERRUPT, SUCCESS.
- **Main Loop:** Hotkey toggle → Capture → State transition → Action (select left circle → detect patterns → tap sorted by size/proximity → check circle gone).
- **Cycle Colors:** Scan left-to-right for next visible circle.
- **Zoom Logic:** In FILLING, if <3 patterns detected but circle present → Pinch out (scale +20%) → Recheck.
- **Debug Mode:** Keypress gates (e.g., 'scan' → draw/overlay detections → wait input → 'tap' → execute with preview).
- **Cloaking:** Wrap actions in `time.sleep(random.uniform(0.5,1.5))`; Bezier for all swipes.
- **Tests/Debug:** End-to-end on partial image (manual pauses); log state traces; visualize state flows.
- **Docs:** State machine pseudocode; hotkey mappings.

### Phase 4: Turnstyle Hopping – Ad Detection & Handling

- **Detection:** Compare capture delta to baseline (e.g., SSIM <0.8 or ad templates: full-screen dark overlay, interstitial buttons).
- **Handling:** Classify ad type (video: tap play/close; banner: swipe up); fallback tap bottom-right for X.
- **Resume:** Post-handling, recapture → back to prior state.
- **Cloaking:** Extra delay (1-2s) post-ad; vary dismiss paths.
- **Tests/Debug:** Simulate ads (overlay mocks on captures); measure skip success rate.
- **Docs:** Ad patterns catalog (update as encountered).

### Phase 5: Feature Additions or Improvements

- **Full Automation Icing:** Detect "new image" button/text → Auto-click.
- **Perf Tweaks:** Numba on contour filters if >200ms/cycle.
- **Enhance Cloaking:** Upgrade Bezier to cubic (add P3); add pause randomness.
- **Robustness:** Multi-scale detection pyramid; HSV tolerance for greys (±10).
- **Tests/Debug:** Integration tests on full image; edge cases (tiny zooms, ad storms).
- **Docs:** Feature roadmap; tuning params JSON.

### Phase 6: Global – Tests, Debugging, and Documentation (Per-Phase + Final)

- **Per-Phase:** Unit/integration (pytest); visual diffs; perf benchmarks.
- **Final:** Smoke test full coloring; README with setup/run/debug guides; video demo if possible.
- **Ongoing:** Git commits per phase; issue tracker for bugs.

## Known Challenges & Mitigations

- **Tiny Patterns/Zoom:** Density metric triggers auto-pinch; Bezier math ensures natural curves (perpendicular offset: rotate vector 90° by (dx,dy)→(-dy,dx) normalized \* curve_amt).
- **Ad Variability:** Template library (update via user feedback); fallback heuristics (e.g., detect non-game UI ratio).
- **ADB Stability:** Heartbeat pings; reconnect logic.
- **Greys Variance:** Threshold range 120-220 gray levels; adaptive hist eq.
- **No Samples?** Proceed with procedural mocks (generate checker regions in code); request if agent hits walls.

## Agentic AI Instructions

You are a battle-hardened CV/automation dev on Linux+Android. Implement strictly per phases above—NO code in planning responses, just reasoned steps/proposals. Use code_execution tool for CV tests (e.g., mock pattern detection on generated arrays). Debug visually: Always imshow annotated frames. Fun mode: Narrate CV "aha" moments (e.g., "Gabor nailed that hatch!"). Prioritize Phase 1 → 2 → 3 for MVP filler. Ask for clarifications/samples only if blocked (e.g., ad visuals). Iterate: Propose → Test → Refine. Ship a debuggable brain by EOP. Let's color some pixels and dodge those ads like pros! 🚀
