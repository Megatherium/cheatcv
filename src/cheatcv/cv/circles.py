"""
Color circle detection using HoughCircles.

Detects circular color selectors at top of screen and identifies the leftmost available circle.
Color circles have:
- Circular shape (visible even when deselected)
- Number label inside
- Extra grey outline when selected (raised Y-position)
- Disappear when all regions for that color are filled
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from PIL import Image


class CircleDetector:
    """Detects color selector circles using HoughCircles."""

    def __init__(
        self,
        dp: float = 1.2,
        min_dist: int = 80,
        param1: int = 100,
        param2: int = 30,
        min_radius: int = 15,
        max_radius: int = 40,
        search_top_fraction: float = 0.15,
    ):
        """
        Initialize circle detector with HoughCircles parameters.

        Args:
            dp: Inverse ratio of accumulator resolution (1.2 = fine detection)
            min_dist: Minimum distance between circle centers
            param1: Canny edge detector upper threshold
            param2: Accumulator threshold for circle centers (lower = more circles)
            min_radius: Minimum circle radius in pixels
            max_radius: Maximum circle radius in pixels
            search_top_fraction: Fraction of screen height to search (0.15 = top 15%)
        """
        self.dp = dp
        self.min_dist = min_dist
        self.param1 = param1
        self.param2 = param2
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.search_top_fraction = search_top_fraction

    def detect_circles(
        self,
        img: np.ndarray,
    ) -> List[Tuple[int, int, int]]:
        """
        Detect circles in image using HoughCircles.

        Args:
            img: Input image (BGR or RGB numpy array)

        Returns:
            List of (x, y, radius) tuples sorted by x-coordinate (leftmost first)
        """
        # Convert to grayscale if needed
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        # Limit search to top portion of screen (color circles are at top)
        height = gray.shape[0]
        search_height = int(height * self.search_top_fraction)
        gray_top = gray[:search_height, :]

        # Apply slight blur to reduce noise
        gray_blurred = cv2.GaussianBlur(gray_top, (5, 5), 0)

        # Detect circles
        circles = cv2.HoughCircles(
            gray_blurred,
            cv2.HOUGH_GRADIENT,
            dp=self.dp,
            minDist=self.min_dist,
            param1=self.param1,
            param2=self.param2,
            minRadius=self.min_radius,
            maxRadius=self.max_radius,
        )

        if circles is None:
            return []

        # Convert to list of tuples (x, y, radius)
        circles = np.round(circles[0, :]).astype(int)
        circle_list = [(x, y, r) for x, y, r in circles]

        # Sort by x-coordinate (leftmost first)
        circle_list.sort(key=lambda c: c[0])

        return circle_list

    def get_leftmost_circle(
        self,
        img: np.ndarray,
    ) -> Optional[Tuple[int, int, int]]:
        """
        Detect circles and return the leftmost one.

        Args:
            img: Input image (BGR or RGB numpy array)

        Returns:
            (x, y, radius) tuple of leftmost circle, or None if no circles found
        """
        circles = self.detect_circles(img)
        return circles[0] if circles else None

    def annotate_circles(
        self,
        img: np.ndarray,
        circles: Optional[List[Tuple[int, int, int]]] = None,
        highlight_leftmost: bool = True,
    ) -> np.ndarray:
        """
        Draw detected circles on image for debugging.

        Args:
            img: Input image (BGR or RGB numpy array)
            circles: Optional pre-detected circles. If None, will detect.
            highlight_leftmost: If True, draws leftmost circle in green

        Returns:
            Annotated image copy (BGR format for cv2.imwrite)
        """
        # Create copy to avoid modifying original
        annotated = img.copy()

        # Detect circles if not provided
        if circles is None:
            circles = self.detect_circles(img)

        if not circles:
            # Add "NO CIRCLES DETECTED" text
            cv2.putText(
                annotated,
                "NO CIRCLES DETECTED",
                (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (0, 0, 255),
                3,
            )
            return annotated

        # Draw all circles
        for i, (x, y, r) in enumerate(circles):
            # Leftmost circle in green, others in red
            if i == 0 and highlight_leftmost:
                color = (0, 255, 0)  # Green (BGR)
                thickness = 3
            else:
                color = (0, 0, 255)  # Red (BGR)
                thickness = 2

            # Draw circle outline
            cv2.circle(annotated, (x, y), r, color, thickness)

            # Draw center point
            cv2.circle(annotated, (x, y), 3, color, -1)

            # Add label with coordinates
            label = f"#{i+1} ({x},{y})"
            cv2.putText(
                annotated,
                label,
                (x - 40, y - r - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

        return annotated


def detect_from_file(
    image_path: str,
    output_path: Optional[str] = None,
) -> List[Tuple[int, int, int]]:
    """
    Convenience function to detect circles from image file.

    Args:
        image_path: Path to input image
        output_path: Optional path to save annotated image

    Returns:
        List of detected circles (x, y, radius)
    """
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to load image: {image_path}")

    # Detect circles
    detector = CircleDetector()
    circles = detector.detect_circles(img)

    # Save annotated output if requested
    if output_path:
        annotated = detector.annotate_circles(img, circles)
        cv2.imwrite(output_path, annotated)

    return circles
