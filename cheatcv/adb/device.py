"""
ADB device wrapper for screen capture and input operations.

Provides abstraction layer for:
- Screen capture (screencap → PIL Image)
- Tap operations with jitter for cloaking
- Device info queries (resolution, bounds)
- Error handling for connection issues
"""

import subprocess
import tempfile
import random
import io
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image


class DeviceError(Exception):
    """Raised when ADB device operations fail."""
    pass


class Device:
    """Wrapper for ADB device operations."""

    def __init__(
        self,
        device_id: Optional[str] = None,
        jitter_range: Tuple[int, int] = (5, 15),
    ):
        """
        Initialize ADB device wrapper.

        Args:
            device_id: Optional specific device ID. If None, uses first available device.
            jitter_range: Min/max pixel offset for tap jitter (default: 5-15px)
        """
        self.device_id = device_id
        self.jitter_range = jitter_range
        self._screen_bounds = None

        # Verify device is connected
        if not self._is_device_connected():
            raise DeviceError("No ADB device connected. Check 'adb devices'.")

    def _is_device_connected(self) -> bool:
        """Check if ADB device is connected and authorized."""
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                return False

            # Parse output for connected devices (skip header line)
            lines = result.stdout.strip().split("\n")[1:]
            devices = [line.split()[0] for line in lines if "\tdevice" in line]

            return len(devices) > 0

        except Exception:
            return False

    def _run_adb_command(
        self,
        args: list[str],
        timeout: int = 10,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """
        Run ADB command with error handling.

        Args:
            args: ADB command arguments (without 'adb' prefix)
            timeout: Command timeout in seconds
            capture_output: Whether to capture stdout/stderr

        Returns:
            CompletedProcess result

        Raises:
            DeviceError: If command fails or times out
        """
        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True if capture_output else False,
                timeout=timeout,
            )

            if result.returncode != 0:
                raise DeviceError(
                    f"ADB command failed: {' '.join(args)}\n"
                    f"Error: {result.stderr if capture_output else 'N/A'}"
                )

            return result

        except subprocess.TimeoutExpired:
            raise DeviceError(f"ADB command timeout: {' '.join(args)}")
        except FileNotFoundError:
            raise DeviceError("ADB not found. Ensure 'adb' is in PATH.")

    def get_screen_bounds(self) -> Tuple[int, int]:
        """
        Get device screen resolution (width, height).

        Returns:
            Tuple of (width, height) in pixels

        Raises:
            DeviceError: If unable to query screen size
        """
        if self._screen_bounds:
            return self._screen_bounds

        try:
            result = self._run_adb_command(["shell", "wm", "size"])
            # Output format: "Physical size: 1080x2400"
            size_str = result.stdout.strip().split(": ")[-1]
            width, height = map(int, size_str.split("x"))

            self._screen_bounds = (width, height)
            return self._screen_bounds

        except Exception as e:
            raise DeviceError(f"Failed to get screen bounds: {e}")

    def capture_screen(self, output_path: Optional[Path] = None) -> Image.Image:
        """
        Capture device screen and return as PIL Image.

        Args:
            output_path: Optional path to save screenshot (for debugging)

        Returns:
            PIL Image of screen

        Raises:
            DeviceError: If screen capture fails
        """
        # Create temp file for screencap (ADB doesn't stream well)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            # Capture screen to device /sdcard/
            device_path = "/sdcard/screencap.png"
            self._run_adb_command(["shell", "screencap", "-p", device_path])

            # Pull to local temp file
            self._run_adb_command(["pull", device_path, str(tmp_path)])

            # Clean up device file
            self._run_adb_command(["shell", "rm", device_path])

            # Load as PIL Image
            img = Image.open(tmp_path)

            # Optionally save to persistent path
            if output_path:
                img.save(output_path)

            return img

        except Exception as e:
            raise DeviceError(f"Screen capture failed: {e}")

        finally:
            # Clean up temp file
            if tmp_path.exists():
                tmp_path.unlink()

    def capture_screen_fast(
        self,
        output_path: Optional[Path] = None,
        downscale: float = 1.0,
    ) -> Image.Image:
        """
        Optimized screen capture using exec-out (streams directly, no file I/O).

        Significantly faster than capture_screen() by avoiding device file creation/deletion.
        Streams PNG data directly from screencap to stdout.

        Args:
            output_path: Optional path to save screenshot (for debugging)
            downscale: Scaling factor (0.5 = half resolution, faster transfer). Default: 1.0 (full res)

        Returns:
            PIL Image of screen (downscaled if requested)

        Raises:
            DeviceError: If screen capture fails
        """
        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend(["exec-out", "screencap", "-p"])

        try:
            # Execute and capture binary PNG output
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=5,
            )

            if result.returncode != 0:
                raise DeviceError(f"Screencap exec-out failed: {result.stderr.decode()}")

            # Load PNG data directly from stdout into PIL Image
            img = Image.open(io.BytesIO(result.stdout))

            # Downscale if requested (reduces data for CV processing)
            if downscale != 1.0 and 0 < downscale < 1.0:
                new_size = (int(img.width * downscale), int(img.height * downscale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Optionally save to persistent path
            if output_path:
                img.save(output_path)

            return img

        except subprocess.TimeoutExpired:
            raise DeviceError("Screen capture timeout")
        except Exception as e:
            raise DeviceError(f"Fast screen capture failed: {e}")

    def tap(
        self,
        x: int,
        y: int,
        jitter: bool = True,
    ) -> None:
        """
        Send tap input to device.

        Args:
            x: X coordinate
            y: Y coordinate
            jitter: Apply random offset for human-like cloaking

        Raises:
            DeviceError: If tap fails
        """
        # Apply jitter if enabled
        if jitter:
            jitter_x = random.randint(-self.jitter_range[1], self.jitter_range[1])
            jitter_y = random.randint(-self.jitter_range[1], self.jitter_range[1])

            # Ensure we stay within a reasonable range (avoid negatives)
            x = max(0, x + jitter_x)
            y = max(0, y + jitter_y)

        try:
            self._run_adb_command(["shell", "input", "tap", str(x), str(y)])
        except Exception as e:
            raise DeviceError(f"Tap failed at ({x}, {y}): {e}")

    def swipe(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_ms: int = 300,
    ) -> None:
        """
        Send swipe gesture to device.

        Args:
            x1: Start X coordinate
            y1: Start Y coordinate
            x2: End X coordinate
            y2: End Y coordinate
            duration_ms: Swipe duration in milliseconds

        Raises:
            DeviceError: If swipe fails
        """
        try:
            self._run_adb_command([
                "shell",
                "input",
                "swipe",
                str(x1),
                str(y1),
                str(x2),
                str(y2),
                str(duration_ms),
            ])
        except Exception as e:
            raise DeviceError(f"Swipe failed ({x1},{y1})→({x2},{y2}): {e}")
