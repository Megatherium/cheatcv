#!/usr/bin/env python3
"""Test CV detection on live device capture."""

import sys
from pathlib import Path
import time
import cv2
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cheatcv.adb.device import Device
from cheatcv.cv.circles import CircleDetector
from cheatcv.cv.patterns import PatternDetector


def main():
    print("[LiveTest] Capturing from live device...\n")

    device = Device()
    circle_detector = CircleDetector()
    pattern_detector = PatternDetector()

    # Capture at different scales
    for scale in [1.0, 0.5]:
        print(f"{'='*60}")
        print(f"Testing at scale={scale}")
        print(f"{'='*60}\n")

        # Capture
        print(f"  Capturing screen...")
        start = time.perf_counter()
        img_pil = device.capture_screen_fast(downscale=scale)
        capture_time = (time.perf_counter() - start) * 1000

        # Convert to OpenCV format
        img_np = np.array(img_pil)
        if img_np.shape[2] == 4:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        else:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        print(f"  ✓ Captured in {capture_time:.1f}ms")
        print(f"    Size: {img_bgr.shape[1]}x{img_bgr.shape[0]}")

        # Circle detection
        print(f"\n  Detecting circles...")
        start = time.perf_counter()
        circles = circle_detector.detect_circles(img_bgr)
        circle_time = (time.perf_counter() - start) * 1000

        print(f"  ✓ Found {len(circles)} circles in {circle_time:.1f}ms")
        if circles:
            leftmost = circles[0]
            print(f"    Leftmost: ({leftmost[0]}, {leftmost[1]}), radius={leftmost[2]}")

        # Pattern detection
        print(f"\n  Detecting patterns...")
        start = time.perf_counter()
        patterns = pattern_detector.detect_patterns(img_bgr)
        pattern_time = (time.perf_counter() - start) * 1000

        has_patterns = pattern_detector.has_significant_patterns(img_bgr)
        total_area = sum(r.area for r in patterns)
        largest = max(patterns, key=lambda r: r.area).area if patterns else 0

        print(f"  ✓ Found {len(patterns)} pattern regions in {pattern_time:.1f}ms")
        print(f"    Total area: {total_area}px")
        print(f"    Largest region: {largest}px")
        print(f"    Has significant patterns: {has_patterns}")

        if patterns:
            print(f"    Top 5 regions by area:")
            for i, region in enumerate(patterns[:5], 1):
                print(f"      #{i}: ({region.x}, {region.y}), area={region.area}")

        # Total time
        total_time = capture_time + circle_time + pattern_time
        print(f"\n  TOTAL CYCLE TIME: {total_time:.1f}ms")
        print(f"    Capture:  {capture_time:.1f}ms ({100*capture_time/total_time:.0f}%)")
        print(f"    Circles:  {circle_time:.1f}ms ({100*circle_time/total_time:.0f}%)")
        print(f"    Patterns: {pattern_time:.1f}ms ({100*pattern_time/total_time:.0f}%)")

        # Save annotated output
        debug_dir = Path(__file__).parent.parent / "debug_output"
        if circles:
            annotated_circles = circle_detector.annotate_circles(img_bgr, circles)
            cv2.imwrite(str(debug_dir / f"live_circles_scale{scale}.jpg"), annotated_circles)

        if patterns:
            annotated_patterns = pattern_detector.annotate_patterns(img_bgr, patterns)
            cv2.imwrite(str(debug_dir / f"live_patterns_scale{scale}.jpg"), annotated_patterns)

        print(f"\n  ✓ Saved annotated outputs to debug_output/\n")

    print(f"{'='*60}")
    print("Live detection test complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
