"""Comprehensive performance profiling of full pipeline."""

import sys
import time
import cProfile
import pstats
import io
import click

from cheatcv.adb.device import Device
from cheatcv.cv.circles import CircleDetector
from cheatcv.cv.patterns import PatternDetector
import cv2
import numpy as np


def profile_capture_methods(device, iterations=10):
    """Profile both capture methods."""
    print(f"\n{'='*70}")
    print("PROFILING: ADB Screen Capture Methods")
    print(f"{'='*70}\n")

    # Traditional method
    print(f"Testing capture_screen() (traditional file I/O) - {iterations} iterations...")
    times_traditional = []
    for i in range(iterations):
        start = time.perf_counter()
        img = device.capture_screen()
        elapsed = (time.perf_counter() - start) * 1000
        times_traditional.append(elapsed)

    avg_traditional = sum(times_traditional) / len(times_traditional)
    min_traditional = min(times_traditional)
    max_traditional = max(times_traditional)

    print(f"  Average: {avg_traditional:.1f}ms")
    print(f"  Min:     {min_traditional:.1f}ms")
    print(f"  Max:     {max_traditional:.1f}ms")

    # Fast method (exec-out)
    print(f"\nTesting capture_screen_fast() (exec-out streaming) - {iterations} iterations...")
    times_fast = []
    for i in range(iterations):
        start = time.perf_counter()
        img = device.capture_screen_fast()
        elapsed = (time.perf_counter() - start) * 1000
        times_fast.append(elapsed)

    avg_fast = sum(times_fast) / len(times_fast)
    min_fast = min(times_fast)
    max_fast = max(times_fast)

    print(f"  Average: {avg_fast:.1f}ms")
    print(f"  Min:     {min_fast:.1f}ms")
    print(f"  Max:     {max_fast:.1f}ms")

    print(f"\nSpeedup: {avg_traditional / avg_fast:.2f}x faster with exec-out")

    return {
        'traditional': {'avg': avg_traditional, 'min': min_traditional, 'max': max_traditional},
        'fast': {'avg': avg_fast, 'min': min_fast, 'max': max_fast},
    }


def profile_cv_pipeline(device, scale=0.5):
    """Profile CV detection pipeline."""
    print(f"\n{'='*70}")
    print(f"PROFILING: CV Pipeline at scale={scale}")
    print(f"{'='*70}\n")

    # Capture
    print("Capturing screen...")
    img_pil = device.capture_screen_fast(downscale=scale)
    img_np = np.array(img_pil)
    if img_np.shape[2] == 4:
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
    else:
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    print(f"  Image size: {img_bgr.shape[1]}x{img_bgr.shape[0]}")

    # Profile circle detection
    circle_detector = CircleDetector()

    profiler = cProfile.Profile()
    profiler.enable()

    circles = circle_detector.detect_circles(img_bgr)

    profiler.disable()

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(10)  # Top 10 functions

    print(f"\nCircle Detection - Top 10 functions:")
    print(s.getvalue())

    # Profile pattern detection
    pattern_detector = PatternDetector()

    profiler = cProfile.Profile()
    profiler.enable()

    patterns = pattern_detector.detect_patterns(img_bgr)

    profiler.disable()

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(10)

    print(f"\nPattern Detection - Top 10 functions:")
    print(s.getvalue())

    return {
        'circles_found': len(circles),
        'patterns_found': len(patterns),
    }


def profile_full_cycle(device, scale=0.5):
    """Profile one complete automation cycle."""
    print(f"\n{'='*70}")
    print("PROFILING: Full Automation Cycle")
    print(f"{'='*70}\n")

    circle_detector = CircleDetector()
    pattern_detector = PatternDetector()

    # Full cycle timing
    start_total = time.perf_counter()

    # Capture
    start = time.perf_counter()
    img_pil = device.capture_screen_fast(downscale=scale)
    img_np = np.array(img_pil)
    if img_np.shape[2] == 4:
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
    else:
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    capture_time = (time.perf_counter() - start) * 1000

    # Circle detection
    start = time.perf_counter()
    circles = circle_detector.detect_circles(img_bgr)
    circle_time = (time.perf_counter() - start) * 1000

    # Pattern detection
    start = time.perf_counter()
    patterns = pattern_detector.detect_patterns(img_bgr)
    pattern_time = (time.perf_counter() - start) * 1000

    # Simulated tap (just timing, no actual tap)
    start = time.perf_counter()
    time.sleep(0.1)  # Simulate tap delay
    tap_time = (time.perf_counter() - start) * 1000

    total_time = (time.perf_counter() - start_total) * 1000

    print(f"Full Cycle Breakdown:")
    print(f"  Capture:  {capture_time:7.1f}ms ({100*capture_time/total_time:5.1f}%)")
    print(f"  Circles:  {circle_time:7.1f}ms ({100*circle_time/total_time:5.1f}%)")
    print(f"  Patterns: {pattern_time:7.1f}ms ({100*pattern_time/total_time:5.1f}%)")
    print(f"  Tap:      {tap_time:7.1f}ms ({100*tap_time/total_time:5.1f}%)")
    print(f"  {'='*40}")
    print(f"  TOTAL:    {total_time:7.1f}ms")

    return {
        'capture_ms': capture_time,
        'circle_ms': circle_time,
        'pattern_ms': pattern_time,
        'tap_ms': tap_time,
        'total_ms': total_time,
    }


@click.command()
@click.option('--iterations', type=int, default=10, help='Number of iterations for capture profiling')
@click.option('--scale', type=float, default=0.5, help='Downscale factor for CV')
def profile(iterations, scale):
    """Run comprehensive performance profiling."""
    print("\n" + "="*70)
    print("CheatCV Performance Profiling Suite")
    print("="*70)

    try:
        device = Device()

        # 1. Profile capture methods
        capture_stats = profile_capture_methods(device, iterations=iterations)

        # 2. Profile CV pipeline
        cv_stats = profile_cv_pipeline(device, scale=scale)

        # 3. Profile full cycle
        cycle_stats = profile_full_cycle(device, scale=scale)

        # Summary report
        print(f"\n{'='*70}")
        print("PERFORMANCE SUMMARY REPORT")
        print(f"{'='*70}")

        print(f"\nOptimal Configuration:")
        print(f"  Capture method: exec-out (capture_screen_fast)")
        print(f"  Downscale:      {scale}")
        print(f"  Average cycle:  {cycle_stats['total_ms']:.0f}ms")

        print(f"\nExpected Automation Performance:")
        if cycle_stats['total_ms'] < 300:
            print(f"  ✓ MEETS <300ms target!")
        else:
            over = cycle_stats['total_ms'] - 300
            print(f"  ✗ Over target by {over:.0f}ms")

        # Batched taps efficiency
        print(f"\nBatched Taps Strategy:")
        print(f"  If we tap 10 patterns per capture:")
        print(f"    Effective time/tap: {(cycle_stats['capture_ms'] + cycle_stats['circle_ms'] + cycle_stats['pattern_ms']) / 10 + cycle_stats['tap_ms']:.0f}ms")
        print(f"  If we tap 20 patterns per capture:")
        print(f"    Effective time/tap: {(cycle_stats['capture_ms'] + cycle_stats['circle_ms'] + cycle_stats['pattern_ms']) / 20 + cycle_stats['tap_ms']:.0f}ms")

        print(f"\n{'='*70}\n")

    except Exception as e:
        print(f"\n✗ Profiling error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
