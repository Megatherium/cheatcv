#!/usr/bin/env python3
"""
Benchmark ADB screen capture methods.

Compares:
- capture_screen() - Traditional method (file I/O on device)
- capture_screen_fast() - Optimized exec-out method (streams directly)
"""

import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cheatcv.adb.device import Device, DeviceError


def benchmark_method(device, method_name, iterations=5):
    """Run benchmark for a capture method."""
    method = getattr(device, method_name)

    times = []
    print(f"\n[Benchmark] Testing {method_name}() with {iterations} iterations...")

    for i in range(iterations):
        start = time.perf_counter()
        try:
            img = method()
            elapsed = (time.perf_counter() - start) * 1000  # ms
            times.append(elapsed)
            print(f"  Iteration {i+1}: {elapsed:.1f}ms (size: {img.size}, mode: {img.mode})")
        except Exception as e:
            print(f"  Iteration {i+1}: FAILED - {e}")
            return None

    if times:
        avg = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"\n[Benchmark] {method_name} Results:")
        print(f"  Average: {avg:.1f}ms")
        print(f"  Min:     {min_time:.1f}ms")
        print(f"  Max:     {max_time:.1f}ms")

        return avg

    return None


def main():
    print("[Benchmark] Initializing ADB device...")

    try:
        device = Device()
        width, height = device.get_screen_bounds()
        print(f"[Benchmark] Device: {width}x{height}")

        # Benchmark traditional method
        traditional_avg = benchmark_method(device, "capture_screen", iterations=5)

        # Benchmark optimized method
        fast_avg = benchmark_method(device, "capture_screen_fast", iterations=5)

        # Compare
        if traditional_avg and fast_avg:
            speedup = traditional_avg / fast_avg
            savings = traditional_avg - fast_avg

            print(f"\n{'='*60}")
            print(f"[Benchmark] COMPARISON:")
            print(f"  Traditional (file I/O):  {traditional_avg:.1f}ms")
            print(f"  Optimized (exec-out):    {fast_avg:.1f}ms")
            print(f"  Speedup:                 {speedup:.2f}x faster")
            print(f"  Time saved per capture:  {savings:.1f}ms")
            print(f"{'='*60}")

            # Calculate impact on cycle time
            print(f"\n[Benchmark] Impact on <300ms cycle target:")

            cycle_cv = 90  # ms (circle + pattern detection)
            cycle_tap = 100  # ms (tap operation)

            traditional_cycle = traditional_avg + cycle_cv + cycle_tap
            fast_cycle = fast_avg + cycle_cv + cycle_tap

            print(f"  Traditional total cycle: {traditional_cycle:.0f}ms")
            print(f"  Optimized total cycle:   {fast_cycle:.0f}ms")

            if fast_cycle < 300:
                print(f"  ✓ HITS TARGET (<300ms)!")
            else:
                print(f"  ✗ Still over target by {fast_cycle - 300:.0f}ms")

    except DeviceError as e:
        print(f"[Benchmark] Device error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
