"""Core OpenCV utility functions."""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple


def load_image(image_path: str) -> Optional[np.ndarray]:
    """
    Load an image from file.

    Args:
        image_path: Path to the image file

    Returns:
        Image array or None if failed
    """
    if not Path(image_path).exists():
        return None

    img = cv2.imread(image_path)
    return img


def save_image(image: np.ndarray, output_path: str) -> bool:
    """
    Save an image to file.

    Args:
        image: Image array
        output_path: Path to save the image

    Returns:
        True if successful, False otherwise
    """
    try:
        cv2.imwrite(output_path, image)
        return True
    except Exception:
        return False


def get_image_info(image_path: str) -> Optional[dict]:
    """
    Get information about an image.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary with image info or None if failed
    """
    img = load_image(image_path)
    if img is None:
        return None

    height, width = img.shape[:2]
    channels = img.shape[2] if len(img.shape) > 2 else 1

    return {
        'path': image_path,
        'width': width,
        'height': height,
        'channels': channels,
        'dtype': str(img.dtype),
        'size_bytes': img.nbytes
    }


def resize_image(image: np.ndarray, width: int, height: int) -> np.ndarray:
    """
    Resize an image to specific dimensions.

    Args:
        image: Input image
        width: Target width
        height: Target height

    Returns:
        Resized image
    """
    return cv2.resize(image, (width, height))


def convert_colorspace(image: np.ndarray, conversion: str) -> Optional[np.ndarray]:
    """
    Convert image between color spaces.

    Args:
        image: Input image
        conversion: Conversion type (e.g., 'bgr2gray', 'bgr2hsv', 'bgr2rgb')

    Returns:
        Converted image or None if conversion failed
    """
    conversion_map = {
        'bgr2gray': cv2.COLOR_BGR2GRAY,
        'gray2bgr': cv2.COLOR_GRAY2BGR,
        'bgr2hsv': cv2.COLOR_BGR2HSV,
        'hsv2bgr': cv2.COLOR_HSV2BGR,
        'bgr2rgb': cv2.COLOR_BGR2RGB,
        'rgb2bgr': cv2.COLOR_RGB2BGR,
    }

    code = conversion_map.get(conversion.lower())
    if code is None:
        return None

    return cv2.cvtColor(image, code)


def detect_edges(image: np.ndarray, threshold1: int = 100, threshold2: int = 200) -> np.ndarray:
    """
    Detect edges in an image using Canny edge detection.

    Args:
        image: Input image
        threshold1: First threshold for hysteresis
        threshold2: Second threshold for hysteresis

    Returns:
        Edge-detected image
    """
    if len(image.shape) > 2:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    edges = cv2.Canny(gray, threshold1, threshold2)
    return edges


def detect_faces(image: np.ndarray) -> list:
    """
    Detect faces in an image using Haar Cascade.

    Args:
        image: Input image

    Returns:
        List of detected face rectangles (x, y, w, h)
    """
    # Use pre-trained Haar Cascade
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )

    if len(image.shape) > 2:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    return faces.tolist() if len(faces) > 0 else []


def draw_rectangles(image: np.ndarray, rectangles: list, color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
    """
    Draw rectangles on an image.

    Args:
        image: Input image
        rectangles: List of rectangles [(x, y, w, h), ...]
        color: Rectangle color (B, G, R)
        thickness: Line thickness

    Returns:
        Image with rectangles drawn
    """
    output = image.copy()
    for (x, y, w, h) in rectangles:
        cv2.rectangle(output, (x, y), (x + w, y + h), color, thickness)
    return output
