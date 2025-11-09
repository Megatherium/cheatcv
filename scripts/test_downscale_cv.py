#!/usr/bin/env python3
"""Test if downscaling improves overall CV pipeline performance."""

import sys
from pathlib import Path
import time
import cv2
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cheatcv.cv.circles import CircleDetector
from cheatcv.cv.patterns import PatternDetector


def benchmark_cv_at_scale(img_path, scale_factor):
    """Benchmark CV operations at a given scale."""
    # Load image
    img = cv2.imread(img_path)
    if img is None:
        return None

    # Downscale if needed
    if scale_factor != 1.0:
        new_size = (int(img.shape[1] * scale_factor), int(img.shape[0] * scale_factor))
        img = cv2.resize(img, new_size, interpolation=cv2.INTER_LANCZOS4)

    # Benchmark circle detection
    circle_detector = CircleDetector()
    start = time.perf_counter()
    circles = circle_detector.detect_circles(img)
    circle_time = (time.perf_counter() - start) * 1000

    # Benchmark pattern detection
    pattern_detector = PatternDetector()
    start = time.perf_counter()
    patterns = pattern_detector.detect_patterns(img)
    pattern_time = (time.perf_counter() - start) * 1000

    total_time = circle_time + pattern_time

    return {
        'scale': scale_factor,
        'size': (img.shape[1], img.shape[0]),
        'circle_time': circle_time,
        'pattern_time': pattern_time,
        'total_time': total_time,
        'circles_found': len(circles),
        'patterns_found': len(patterns),
    }


def main():
    # Test on the main sample image
    img_path = "sample/base/02-selected.jpg"

    print("[Downscale Test] Testing CV performance at different resolutions\n")

    scales = [1.0, 0.75, 0.5, 0.25]

    results = []
    for scale in scales:
        print(f"Testing scale={scale}...")
        result = benchmark_cv_at_scale(img_path, scale)
        if result:
            results.append(result)
            print(f"  Size: {result['size']}")
            print(f"  Circle detection: {result['circle_time']:.1f}ms ({result['circles_found']} circles)")
            print(f"  Pattern detection: {result['pattern_time']:.1f}ms ({result['patterns_found']} patterns)")
            print(f"  Total CV time: {result['total_time']:.1f}ms")
            print()

    # Summary
    if results:
        print(f"{'='*70}")
        print(f"{'Scale':<8} {'Resolution':<15} {'CV Time':<10} {'Speedup':<10} {'Detections'}")
        print(f"{'='*70}")

        baseline = results[0]['total_time']
        for r in results:
            speedup = baseline / r['total_time']
            detections = f"C:{r['circles_found']} P:{r['patterns_found']}"
            res_str = f"{r['size'][0]}x{r['size'][1]}"
            print(f"{r['scale']:<8} {res_str:<15} {r['total_time']:<10.1f} {speedup:<10.2f}x {detections}")

        print(f"{'='*70}")

        # Recommendation
        best_scale = None
        for r in results:
            # Want decent speedup (>1.5x) without losing detections
            speedup = baseline / r['total_time']
            if speedup >= 1.5 and r['circles_found'] >= 2 and r['patterns_found'] >= 10:
                if best_scale is None or r['scale'] < best_scale['scale']:
                    best_scale = r

        if best_scale:
            print(f"\nRecommendation: Use scale={best_scale['scale']} ({best_scale['size'][0]}x{best_scale['size'][1]})")
            print(f"  Speedup: {baseline / best_scale['total_time']:.2f}x faster")
            print(f"  CV time: {best_scale['total_time']:.1f}ms (vs {baseline:.1f}ms at full res)")
        else:
            print(f"\nRecommendation: Stick with full resolution (downscaling doesn't help enough)")


if __name__ == "__main__":
    main()
