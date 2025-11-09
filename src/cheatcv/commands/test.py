"""Test commands for CheatCV components."""

import sys
import time
import click
from pathlib import Path

from cheatcv.cv.circles import detect_from_file as detect_circles_from_file
from cheatcv.cv.patterns import detect_from_file as detect_patterns_from_file
from cheatcv.adb.device import Device, DeviceError


@click.group()
def test():
    """Run tests on CheatCV components."""
    pass


@test.command()
def circles():
    """Test circle detection on sample images."""
    project_root = Path.cwd()
    sample_dir = project_root / "sample" / "base"
    debug_dir = project_root / "debug_output"

    # Ensure debug directory exists
    debug_dir.mkdir(parents=True, exist_ok=True)

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
        circles_detected = detect_circles_from_file(str(input_path), str(output_path))
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

        print(f"[CircleTest] Detected {len(circles_detected)} circles in {elapsed:.1f}ms")

        if circles_detected:
            leftmost = circles_detected[0]
            print(f"[CircleTest] Leftmost circle: ({leftmost[0]}, {leftmost[1]}), r={leftmost[2]}")
            print(f"[CircleTest] All circles: {circles_detected}")
        else:
            print(f"[CircleTest] No circles detected (may be expected)")

        print(f"[CircleTest] ✓ Annotated output: {output_path}")
        print()

    print("[CircleTest] All tests complete. Check debug_output/ for annotated images.")


@test.command()
def patterns():
    """Test pattern detection on sample images."""
    project_root = Path.cwd()
    sample_dir = project_root / "sample" / "base"
    debug_dir = project_root / "debug_output"

    # Ensure debug directory exists
    debug_dir.mkdir(parents=True, exist_ok=True)

    test_cases = [
        ("02-selected.jpg", "After color selection"),
        ("03-colored.jpg", "After some filling"),
    ]

    print("[PatternTest] Starting pattern detection tests on sample images\n")

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
        patterns_detected = detect_patterns_from_file(str(input_path), str(output_path))
        elapsed = (time.perf_counter() - start) * 1000

        print(f"[PatternTest] Detected {len(patterns_detected)} patterns in {elapsed:.1f}ms")

        if patterns_detected:
            print(f"[PatternTest] Pattern centers: {patterns_detected}")
        else:
            print(f"[PatternTest] No patterns detected")

        print(f"[PatternTest] ✓ Annotated output: {output_path}")
        print()

    print("[PatternTest] All tests complete. Check debug_output/ for annotated images.")


@test.command()
def adb():
    """Test ADB connection and screen capture."""
    print("[ADBTest] Testing ADB connection...\n")

    try:
        device = Device()
        print(f"[ADBTest] ✓ Device connected")

        # Get screen bounds
        width, height = device.get_screen_bounds()
        print(f"[ADBTest] ✓ Screen bounds: {width}x{height}")

        # Test capture
        print(f"[ADBTest] Testing screen capture...")
        start = time.perf_counter()
        img = device.capture_screen()
        elapsed = (time.perf_counter() - start) * 1000

        print(f"[ADBTest] ✓ Capture successful: {img.size}, {img.mode} ({elapsed:.1f}ms)")

    except DeviceError as e:
        print(f"[ADBTest] ✗ Device error: {e}")
        sys.exit(1)


@test.command()
def live():
    """Test live detection on device screen."""
    from cheatcv.cv.circles import detect_circles
    from cheatcv.cv.patterns import detect_patterns
    import cv2
    import numpy as np

    print("[LiveTest] Testing live detection on device...\n")

    try:
        device = Device()
        width, height = device.get_screen_bounds()
        print(f"[LiveTest] Device: {width}x{height}")

        # Capture
        print(f"[LiveTest] Capturing screen...")
        img = device.capture_screen()

        # Convert PIL to OpenCV
        img_array = np.array(img)
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        # Downscale
        downscale = 0.5
        img_small = cv2.resize(img_cv, None, fx=downscale, fy=downscale)

        # Detect circles
        print(f"[LiveTest] Detecting circles...")
        start = time.perf_counter()
        circles = detect_circles(img_small)
        circles_time = (time.perf_counter() - start) * 1000
        print(f"[LiveTest] ✓ Found {len(circles)} circles in {circles_time:.1f}ms")

        # Detect patterns
        print(f"[LiveTest] Detecting patterns...")
        start = time.perf_counter()
        patterns = detect_patterns(img_small)
        patterns_time = (time.perf_counter() - start) * 1000
        print(f"[LiveTest] ✓ Found {len(patterns)} patterns in {patterns_time:.1f}ms")

        print(f"\n[LiveTest] Total CV time: {circles_time + patterns_time:.1f}ms")

    except DeviceError as e:
        print(f"[LiveTest] ✗ Device error: {e}")
        sys.exit(1)
