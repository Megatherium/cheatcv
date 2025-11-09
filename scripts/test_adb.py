#!/usr/bin/env python3
"""Test script for ADB wrapper - capture live screenshot."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cheatcv.adb.device import Device, DeviceError


def main():
    try:
        print("[Test] Initializing ADB device...")
        device = Device()

        print("[Test] Getting screen bounds...")
        width, height = device.get_screen_bounds()
        print(f"[Test] Screen resolution: {width}x{height}")

        print("[Test] Capturing screen...")
        output_path = Path(__file__).parent.parent / "debug_output" / "live_capture.png"
        img = device.capture_screen(output_path=output_path)

        print(f"[Test] ✓ Screenshot saved: {output_path}")
        print(f"[Test] Image size: {img.size}")
        print(f"[Test] Image mode: {img.mode}")

    except DeviceError as e:
        print(f"[Test] ✗ Device error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[Test] ✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
