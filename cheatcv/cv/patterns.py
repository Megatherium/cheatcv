"""
Checkerboard pattern detection for fillable regions.

Detects grey checkerboard overlays (RGB 133,133,133 and RGB 209,209,209) that mark
unfilled regions. Pattern density varies with zoom level, so detection uses:
- Grayscale thresholding for grey palette range
- Texture variance (local std dev) to identify checkerboard oscillation
- Morphological operations to clean noise
- Contour filtering by area and hierarchy

Key insight: Pattern is MUCH finer at normal zoom vs. zoomed-in view.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PatternRegion:
    """Detected pattern region with metadata."""
    x: int  # Centroid X
    y: int  # Centroid Y
    area: int  # Contour area in pixels
    contour: np.ndarray  # Original contour points
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)


class PatternDetector:
    """Detects checkerboard patterns marking fillable regions."""

    def __init__(
        self,
        grey_range: Tuple[int, int] = (120, 220),
        min_area: int = 50,
        max_area: Optional[int] = None,
        texture_threshold: float = 15.0,
        morph_kernel_size: int = 3,
    ):
        """
        Initialize pattern detector.

        Args:
            grey_range: Grayscale value range for checkerboard (default: 120-220)
            min_area: Minimum contour area in pixels (filter noise)
            max_area: Maximum contour area (None = no limit)
            texture_threshold: Local std dev threshold for texture variance
            morph_kernel_size: Kernel size for morphological operations
        """
        self.grey_range = grey_range
        self.min_area = min_area
        self.max_area = max_area
        self.texture_threshold = texture_threshold
        self.morph_kernel_size = morph_kernel_size

    def _compute_texture_variance(
        self,
        img_gray: np.ndarray,
        window_size: int = 5,
    ) -> np.ndarray:
        """
        Compute local texture variance (std dev) for checkerboard detection.

        Checkerboard patterns have high local variance due to alternating colors.

        Args:
            img_gray: Grayscale image
            window_size: Window size for local std dev computation

        Returns:
            Variance map (same size as input)
        """
        # Convert to float for computation
        img_float = img_gray.astype(np.float32)

        # Compute local mean and std dev using box filter
        kernel = np.ones((window_size, window_size), np.float32) / (window_size ** 2)

        mean = cv2.filter2D(img_float, -1, kernel)
        mean_sq = cv2.filter2D(img_float ** 2, -1, kernel)

        # Variance = E[X^2] - E[X]^2
        variance = mean_sq - mean ** 2
        variance = np.maximum(variance, 0)  # Avoid negative due to float precision

        # Return std dev (sqrt of variance)
        return np.sqrt(variance)

    def detect_patterns(
        self,
        img: np.ndarray,
        apply_texture_filter: bool = True,
    ) -> List[PatternRegion]:
        """
        Detect checkerboard patterns in image.

        Args:
            img: Input image (BGR or RGB numpy array)
            apply_texture_filter: Use texture variance to validate patterns

        Returns:
            List of detected pattern regions sorted by area (largest first)
        """
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # Threshold to isolate grey checkerboard palette
        mask = cv2.inRange(gray, self.grey_range[0], self.grey_range[1])

        # Optional: Filter by texture variance (high variance = checkerboard oscillation)
        if apply_texture_filter:
            texture = self._compute_texture_variance(gray, window_size=5)
            texture_mask = (texture > self.texture_threshold).astype(np.uint8) * 255

            # Combine grey range + texture variance
            mask = cv2.bitwise_and(mask, texture_mask)

        # Morphological operations to clean noise and connect regions
        kernel = np.ones((self.morph_kernel_size, self.morph_kernel_size), np.uint8)

        # Erode to remove small noise
        mask = cv2.erode(mask, kernel, iterations=1)

        # Dilate to reconnect fragmented regions
        mask = cv2.dilate(mask, kernel, iterations=2)

        # Find contours
        contours, hierarchy = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,  # Only external contours (no nested)
            cv2.CHAIN_APPROX_SIMPLE,
        )

        # Filter contours by area
        regions = []
        for contour in contours:
            area = cv2.contourArea(contour)

            # Skip if too small
            if area < self.min_area:
                continue

            # Skip if too large (if max_area specified)
            if self.max_area and area > self.max_area:
                continue

            # Get centroid
            M = cv2.moments(contour)
            if M["m00"] == 0:
                continue

            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)

            regions.append(PatternRegion(
                x=cx,
                y=cy,
                area=int(area),
                contour=contour,
                bbox=(x, y, w, h),
            ))

        # Sort by area (largest first) for prioritization
        regions.sort(key=lambda r: r.area, reverse=True)

        return regions

    def detect_patterns_robust(
        self,
        img: np.ndarray,
    ) -> List[PatternRegion]:
        """
        Robust multi-threshold pattern detection for zoom-invariance.

        Tries multiple texture thresholds and merges results to handle
        fine patterns at extreme zoom-out.

        Args:
            img: Input image (BGR or RGB numpy array)

        Returns:
            List of detected pattern regions (duplicates merged)
        """
        # Try multiple texture thresholds (from strict to lenient)
        thresholds = [self.texture_threshold, self.texture_threshold * 0.7, self.texture_threshold * 0.4]

        all_regions = []
        seen_centroids = set()

        for threshold in thresholds:
            # Temporarily adjust threshold
            old_threshold = self.texture_threshold
            self.texture_threshold = threshold

            regions = self.detect_patterns(img, apply_texture_filter=True)

            # Add unique regions (avoid duplicates based on centroid proximity)
            for region in regions:
                centroid_key = (region.x // 20, region.y // 20)  # 20px grid for deduplication

                if centroid_key not in seen_centroids:
                    all_regions.append(region)
                    seen_centroids.add(centroid_key)

            # Restore original threshold
            self.texture_threshold = old_threshold

        # Re-sort by area
        all_regions.sort(key=lambda r: r.area, reverse=True)

        return all_regions

    def has_significant_patterns(
        self,
        img: np.ndarray,
        min_total_area: int = 3500,
        min_large_region: int = 1000,
    ) -> bool:
        """
        Check if image contains significant checkerboard patterns.

        Use this as primary "color selected" indicator for state machine.
        More robust than counting regions (handles fragmentation/zoom).

        Uses dual heuristic to handle both large and small fillable regions:
        - Has large region (>1000px) = likely legitimate pattern, not noise
        - OR total area >3500px = substantial coverage

        Args:
            img: Input image (BGR or RGB numpy array)
            min_total_area: Minimum total pattern area to consider "significant"
            min_large_region: Minimum area for a single "large" region

        Returns:
            True if significant patterns detected, False otherwise
        """
        regions = self.detect_patterns(img)

        if not regions:
            return False

        total_area = sum(r.area for r in regions)
        largest_region = max(regions, key=lambda r: r.area).area

        # Dual heuristic: large single region OR substantial total coverage
        return largest_region >= min_large_region or total_area >= min_total_area

    def annotate_patterns(
        self,
        img: np.ndarray,
        regions: Optional[List[PatternRegion]] = None,
    ) -> np.ndarray:
        """
        Draw detected patterns on image for debugging.

        Args:
            img: Input image (BGR or RGB numpy array)
            regions: Optional pre-detected regions. If None, will detect.

        Returns:
            Annotated image copy (BGR format for cv2.imwrite)
        """
        # Create copy
        annotated = img.copy()

        # Detect patterns if not provided
        if regions is None:
            regions = self.detect_patterns(img)

        if not regions:
            # Add "NO PATTERNS DETECTED" text
            cv2.putText(
                annotated,
                "NO PATTERNS DETECTED",
                (50, 200),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (0, 0, 255),
                3,
            )
            return annotated

        # Draw all detected regions
        for i, region in enumerate(regions):
            # Draw contour outline
            cv2.drawContours(annotated, [region.contour], -1, (0, 255, 0), 2)

            # Draw centroid
            cv2.circle(annotated, (region.x, region.y), 5, (255, 0, 0), -1)

            # Draw bounding box
            x, y, w, h = region.bbox
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (255, 255, 0), 2)

            # Add label with area
            label = f"#{i+1} Area:{region.area}"
            cv2.putText(
                annotated,
                label,
                (region.x - 40, region.y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        # Add summary text
        summary = f"Detected {len(regions)} pattern regions"
        cv2.putText(
            annotated,
            summary,
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2,
        )

        return annotated


def detect_from_file(
    image_path: str,
    output_path: Optional[str] = None,
) -> List[PatternRegion]:
    """
    Convenience function to detect patterns from image file.

    Args:
        image_path: Path to input image
        output_path: Optional path to save annotated image

    Returns:
        List of detected pattern regions
    """
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to load image: {image_path}")

    # Detect patterns
    detector = PatternDetector()
    regions = detector.detect_patterns(img)

    # Save annotated output if requested
    if output_path:
        annotated = detector.annotate_patterns(img, regions)
        cv2.imwrite(output_path, annotated)

    return regions
