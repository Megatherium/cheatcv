"""Keepalive script for Android device - taps random locations to keep screen active."""

import time
import random
import signal
import sys
import subprocess
import click
from typing import Tuple


class Keepalive:
    def __init__(
        self,
        width: int = 1080,
        height: int = 2400,
        interval: int = 30,
        safe_zone_margin: float = 0.2,
    ):
        """
        Initialize keepalive with screen dimensions and tap parameters.

        Args:
            width: Screen width in pixels
            height: Screen height in pixels
            interval: Seconds between taps
            safe_zone_margin: Fraction of screen to avoid at top/bottom (0.2 = 20%)
        """
        self.width = width
        self.height = height
        self.interval = interval

        # Calculate safe zone boundaries (middle 60%)
        self.y_min = int(height * safe_zone_margin)
        self.y_max = int(height * (1 - safe_zone_margin))

        self.running = True
        self.tap_count = 0

        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, sig, frame):
        """Handle Ctrl+C for graceful shutdown."""
        print(f"\n[Keepalive] Caught interrupt, shutting down gracefully...")
        print(f"[Keepalive] Total taps sent: {self.tap_count}")
        self.running = False
        sys.exit(0)

    def _get_random_tap_coords(self) -> Tuple[int, int]:
        """Generate random coordinates within safe zone."""
        x = random.randint(0, self.width - 1)
        y = random.randint(self.y_min, self.y_max)
        return x, y

    def _send_tap(self, x: int, y: int) -> bool:
        """
        Send tap command via ADB.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if tap succeeded, False otherwise
        """
        try:
            result = subprocess.run(
                ["adb", "shell", "input", "tap", str(x), str(y)],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                return True
            else:
                print(f"[Keepalive] ADB tap failed: {result.stderr.strip()}")
                return False

        except subprocess.TimeoutExpired:
            print(f"[Keepalive] ADB tap timeout")
            return False
        except FileNotFoundError:
            print(f"[Keepalive] ADB not found - ensure adb is in PATH")
            return False
        except Exception as e:
            print(f"[Keepalive] Unexpected error: {e}")
            return False

    def run(self):
        """Main keepalive loop - tap random locations at regular intervals."""
        print(f"[Keepalive] Starting with {self.interval}s interval")
        print(f"[Keepalive] Safe zone: y={self.y_min}-{self.y_max} (middle 60%)")
        print(f"[Keepalive] Press Ctrl+C to stop\n")

        while self.running:
            x, y = self._get_random_tap_coords()

            if self._send_tap(x, y):
                self.tap_count += 1
                print(f"[Keepalive] Tap #{self.tap_count}: ({x}, {y})")
            else:
                print(f"[Keepalive] Failed to send tap, will retry next interval")

            # Wait for next interval
            time.sleep(self.interval)


@click.command()
@click.option('--width', type=int, default=1080, help='Screen width in pixels')
@click.option('--height', type=int, default=2400, help='Screen height in pixels')
@click.option('--interval', type=int, default=30, help='Seconds between taps')
def keepalive(width, height, interval):
    """Keep Android device screen awake by tapping random locations."""
    ka = Keepalive(width=width, height=height, interval=interval)
    ka.run()
