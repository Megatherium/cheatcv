#!/usr/bin/env python3
"""Test circle detection on sample images."""

import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cheatcv.cv.circles import detect_from_file


def main():
    project_root = Path(__file__).parent.parent
    sample_dir = project_root / "sample" / "base"
    debug_dir = project_root / "debug_output"

    # Test images
    test_cases = [
        ("01-start.jpg", "Fresh canvas - should have multiple circles"),
        ("02-selected.jpg", "Color selected - should have circles"),
        ("03-colored.jpg", "After filling - may have fewer circles"),
        ("04-color_done.jpg", "Color done - circle should be gone"),
    ]

    print("[CircleTest] Starting circle detection tests on sample images\n")

    for filename, description in test_cases:
        input_path = sample_dir / filename
        if not input_path.exists():
            print(f"[CircleTest] ✗ Skipping {filename} (not found)")
            continue

        output_path = debug_dir / f"circles_{filename}"

        print(f"[CircleTest] Testing: {filename}")
        print(f"[CircleTest] Description: {description}")

        # Time the detection
        start = time.perf_counter()
        circles = detect_from_file(str(input_path), str(output_path))
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

        print(f"[CircleTest] Detected {len(circles)} circles in {elapsed:.1f}ms")

        if circles:
            leftmost = circles[0]
            print(f"[CircleTest] Leftmost circle: ({leftmost[0]}, {leftmost[1]}), r={leftmost[2]}")
            print(f"[CircleTest] All circles: {circles}")
        else:
            print(f"[CircleTest] No circles detected (may be expected)")

        print(f"[CircleTest] ✓ Annotated output: {output_path}")
        print()

    print("[CircleTest] All tests complete. Check debug_output/ for annotated images.")


if __name__ == "__main__":
    main()
