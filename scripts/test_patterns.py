#!/usr/bin/env python3
"""Test checkerboard pattern detection on sample images."""

import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cheatcv.cv.patterns import detect_from_file


def main():
    project_root = Path(__file__).parent.parent
    sample_dir = project_root / "sample" / "base"
    debug_dir = project_root / "debug_output"

    # Test images
    test_cases = [
        ("01-start.jpg", "Fresh canvas - NO patterns expected (no color selected)"),
        ("02-selected.jpg", "Color selected - patterns should be visible (fine/zoomed out)"),
        ("02.1-zoom.jpg", "Zoomed pattern view - should detect (coarse/cropped)"),
        ("03-colored.jpg", "After filling - may have fewer patterns"),
        ("04-color_done.jpg", "Color done - patterns may be gone"),
    ]

    print("[PatternTest] Starting checkerboard pattern detection tests\n")

    for filename, description in test_cases:
        input_path = sample_dir / filename
        if not input_path.exists():
            print(f"[PatternTest] ✗ Skipping {filename} (not found)")
            continue

        output_path = debug_dir / f"patterns_{filename}"

        print(f"[PatternTest] Testing: {filename}")
        print(f"[PatternTest] Description: {description}")

        # Time the detection
        start = time.perf_counter()
        regions = detect_from_file(str(input_path), str(output_path))
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

        print(f"[PatternTest] Detected {len(regions)} pattern regions in {elapsed:.1f}ms")

        if regions:
            # Show top 5 largest regions
            top_regions = regions[:5]
            for i, region in enumerate(top_regions, 1):
                print(f"[PatternTest]   #{i}: area={region.area}, centroid=({region.x},{region.y})")

            total_area = sum(r.area for r in regions)
            print(f"[PatternTest] Total pattern area: {total_area} pixels")
        else:
            print(f"[PatternTest] No patterns detected")

        print(f"[PatternTest] ✓ Annotated output: {output_path}")
        print()

    print("[PatternTest] All tests complete. Check debug_output/ for annotated images.")


if __name__ == "__main__":
    main()
