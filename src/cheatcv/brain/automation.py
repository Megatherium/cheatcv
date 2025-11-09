"""
Main automation state machine for CheatCV.

State flow:
1. IDLE - Waiting for hotkey activation
2. COLOR_SELECT - Detect and tap leftmost color circle
3. FILL_LOOP - Detect all patterns, tap all regions (batched), repeat until no patterns
4. NEXT_COLOR - Check if more colors available, loop back to COLOR_SELECT
5. SUCCESS - All colors done, return to IDLE

Key optimization: Batch taps between captures to amortize ~900ms capture cost.
Instead of capture→tap→capture→tap (expensive), we do capture→tap_all→capture (efficient).
"""

import time
import random
import logging
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

from cheatcv.adb.device import Device, DeviceError
from cheatcv.cv.circles import CircleDetector
from cheatcv.cv.patterns import PatternDetector, PatternRegion


class State(Enum):
    """Automation states."""
    IDLE = "idle"
    COLOR_SELECT = "color_select"
    FILL_LOOP = "fill_loop"
    NEXT_COLOR = "next_color"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class AutomationStats:
    """Runtime statistics for automation session."""
    taps_total: int = 0
    captures_total: int = 0
    colors_completed: int = 0
    start_time: float = 0
    state_transitions: List[tuple] = None

    def __post_init__(self):
        if self.state_transitions is None:
            self.state_transitions = []


class CheatCVAutomation:
    """Main automation controller."""

    def __init__(
        self,
        device: Optional[Device] = None,
        downscale: float = 0.5,
        tap_delay_range: tuple = (500, 1500),
        max_fill_iterations: int = 50,
        debug: bool = False,
    ):
        """
        Initialize automation controller.

        Args:
            device: ADB device instance (creates new if None)
            downscale: Image downscaling factor for CV (0.5 = half res, 5x faster)
            tap_delay_range: Random delay range between taps in ms (min, max)
            max_fill_iterations: Max iterations per color to prevent infinite loops
            debug: Enable debug mode (step-by-step, visual feedback)
        """
        self.device = device or Device()
        self.downscale = downscale
        self.tap_delay_range = tap_delay_range
        self.max_fill_iterations = max_fill_iterations
        self.debug = debug

        # CV detectors
        self.circle_detector = CircleDetector()
        self.pattern_detector = PatternDetector()

        # State
        self.state = State.IDLE
        self.running = False
        self.stats = AutomationStats()

        # Logging
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)

    def _capture_and_convert(self) -> np.ndarray:
        """Capture screen and convert to OpenCV format (BGR)."""
        # Use fast exec-out method with downscaling
        img_pil = self.device.capture_screen_fast(downscale=self.downscale)

        # Convert PIL (RGBA) → numpy → BGR for OpenCV
        img_np = np.array(img_pil)

        # Handle RGBA → BGR conversion
        if img_np.shape[2] == 4:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        else:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        self.stats.captures_total += 1
        return img_bgr

    def _tap_with_delay(self, x: int, y: int, jitter: bool = True):
        """Tap and apply random delay for cloaking."""
        # Scale coordinates if downscaled (tap coords must be full-res)
        if self.downscale != 1.0:
            x = int(x / self.downscale)
            y = int(y / self.downscale)

        self.device.tap(x, y, jitter=jitter)
        self.stats.taps_total += 1

        # Random delay (cloaking)
        delay_ms = random.randint(
            self.tap_delay_range[0], self.tap_delay_range[1])
        time.sleep(delay_ms / 1000.0)

    def _transition_state(self, new_state: State, reason: str = ""):
        """Transition to new state with logging."""
        old_state = self.state
        self.state = new_state

        timestamp = time.time()
        self.stats.state_transitions.append(
            (timestamp, old_state, new_state, reason))

        self.logger.info(f"State: {old_state.value} → {new_state.value} ({reason})")

    def state_color_select(self, img: np.ndarray) -> State:
        """
        Select leftmost color circle.

        Returns next state.
        """
        circles = self.circle_detector.detect_circles(img)

        if not circles:
            self.logger.warning("No circles detected - may be done or error")
            return State.SUCCESS

        # Tap leftmost circle
        leftmost = circles[0]
        x, y = leftmost[0], leftmost[1]

        self.logger.info(f"Tapping leftmost circle at ({x}, {y})")
        self._tap_with_delay(x, y)

        # Brief wait for UI animation (circle raises, patterns appear)
        time.sleep(0.5)

        return State.FILL_LOOP

    def state_fill_loop(self, img: np.ndarray) -> State:
        """
        Fill all detected patterns in current capture (batched taps).

        Returns next state.
        """
        # Check if patterns present (color is selected)
        if not self.pattern_detector.has_significant_patterns(img):
            self.logger.info("No significant patterns - color may be complete")
            self.stats.colors_completed += 1
            return State.NEXT_COLOR

        # Detect all pattern regions
        regions = self.pattern_detector.detect_patterns(img)

        if not regions:
            self.logger.warning(
                "Patterns detected by heuristic but regions empty - retry")
            return State.FILL_LOOP

        # Sort by area (largest first - prioritize big regions)
        regions.sort(key=lambda r: r.area, reverse=True)

        self.logger.info(
            f"Detected {len(regions)} pattern regions, tapping all...")

        # Tap ALL regions in this batch (amortize capture cost)
        for i, region in enumerate(regions, 1):
            x, y = region.x, region.y
            self.logger.debug(
                f"  Tap {i}/{len(regions)}: ({x}, {y}), area={region.area}")
            self._tap_with_delay(x, y)

        # After tapping all, loop back to capture + recheck
        return State.FILL_LOOP

    def state_next_color(self, img: np.ndarray) -> State:
        """
        Check if more colors available.

        Returns next state.
        """
        circles = self.circle_detector.detect_circles(img)

        if not circles:
            self.logger.info("No more circles - all colors complete!")
            return State.SUCCESS

        self.logger.info(
            f"{len(circles)} circles remaining, selecting next color")
        return State.COLOR_SELECT

    def run_cycle(self) -> State:
        """
        Run one automation cycle (capture + state logic).

        Returns new state.
        """
        try:
            # Capture screen
            img = self._capture_and_convert()

            # Execute state logic
            if self.state == State.COLOR_SELECT:
                return self.state_color_select(img)

            elif self.state == State.FILL_LOOP:
                return self.state_fill_loop(img)

            elif self.state == State.NEXT_COLOR:
                return self.state_next_color(img)

            elif self.state == State.SUCCESS:
                self.logger.info("Automation complete!")
                return State.IDLE

            elif self.state == State.IDLE:
                # Waiting for activation
                return State.IDLE

            else:
                self.logger.error(f"Unknown state: {self.state}")
                return State.ERROR

        except DeviceError as e:
            self.logger.error(f"Device error: {e}")
            return State.ERROR

        except Exception as e:
            self.logger.error(f"Unexpected error in cycle: {e}")
            return State.ERROR

    def start(self):
        """Start automation from IDLE."""
        self.logger.info("Starting automation...")
        self.running = True
        self.stats = AutomationStats(start_time=time.time())
        self._transition_state(State.COLOR_SELECT, "Automation started")

    def stop(self):
        """Stop automation and return to IDLE."""
        self.logger.info("Stopping automation...")
        self.running = False
        self._transition_state(State.IDLE, "Stopped by user")

    def run_until_complete(self, max_cycles: int = 500):
        """
        Run automation loop until complete or max cycles reached.

        Args:
            max_cycles: Safety limit to prevent infinite loops

        Returns:
            Final state
        """
        self.start()

        cycle_count = 0

        while self.running and cycle_count < max_cycles:
            cycle_count += 1
            self.logger.debug(f"--- Cycle {cycle_count} ---")

            next_state = self.run_cycle()
            self._transition_state(next_state, f"Cycle {cycle_count} complete")

            if self.state in (State.SUCCESS, State.ERROR, State.IDLE):
                break

            # Safety check: prevent infinite fill loops
            fill_iterations = sum(
                1 for _, _, s, _ in self.stats.state_transitions if s == State.FILL_LOOP)
            if fill_iterations > self.max_fill_iterations:
                self.logger.error(
                    f"Max fill iterations ({self.max_fill_iterations}) exceeded - stopping")
                self._transition_state(State.ERROR, "Max iterations exceeded")
                break

        elapsed = time.time() - self.stats.start_time

        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Automation finished after {cycle_count} cycles ({elapsed:.1f}s)")
        self.logger.info(f"  Taps: {self.stats.taps_total}")
        self.logger.info(f"  Captures: {self.stats.captures_total}")
        self.logger.info(f"  Colors completed: {self.stats.colors_completed}")
        self.logger.info(f"  Final state: {self.state.value}")
        self.logger.info(f"{'='*60}\n")

        return self.state
