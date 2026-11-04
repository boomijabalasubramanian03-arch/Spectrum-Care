"""
Colour name lookup table and perceptual matching.

Uses standard CIELAB color space (CIE 1976 delta-E) with proper axis scaling
(L: 0-100, a: -128..127, b: -128..127).
Properly balances chromaticity against luminance, ensuring vivid colors
like Blue, Red, Yellow, Cyan, and Pink are never overwhelmed by brightness differences.
"""
import math
from typing import Tuple
import cv2
import numpy as np

# Standard SRS named colors table -> (R, G, B)
COLOR_TABLE = {
    "Red": (220, 20, 60),
    "Orange": (255, 140, 0),
    "Yellow": (255, 215, 0),
    "Green": (34, 139, 34),
    "Blue": (30, 90, 200),
    "Purple": (128, 0, 128),
    "Pink": (255, 105, 180),
    "Brown": (139, 69, 19),
    "Black": (20, 20, 20),
    "White": (245, 245, 245),
    "Gray": (128, 128, 128),
    "Cyan": (0, 180, 190),
    "Maroon": (128, 0, 32),
    "Navy": (20, 30, 90),
    "Olive": (110, 110, 30),
    "Teal": (0, 128, 128),
    "Gold": (212, 175, 55),
    "Beige": (222, 200, 165),
    "Silver": (192, 192, 192),
}


def _rgb_to_standard_lab(rgb: Tuple[int, int, int]) -> np.ndarray:
    """
    Converts RGB to standard CIE-L*a*b* coordinates.
    OpenCV's COLOR_RGB2Lab produces 8-bit values (L: 0..255, a: 0..255, b: 0..255).
    We rescale to standard CIE ranges so L does not artificially dominate a and b.
    """
    r, g, b = [max(0, min(255, int(c))) for c in rgb]
    arr = np.uint8([[[r, g, b]]])
    lab8 = cv2.cvtColor(arr, cv2.COLOR_RGB2Lab)[0][0].astype(np.float32)
    L = lab8[0] * (100.0 / 255.0)
    a = lab8[1] - 128.0
    b = lab8[2] - 128.0
    return np.array([L, a, b], dtype=np.float32)


# Precompute standard CIELAB coordinates for each named color
_COLOR_LAB = {name: _rgb_to_standard_lab(rgb) for name, rgb in COLOR_TABLE.items()}


def nearest_color_name(rgb: Tuple[int, int, int]) -> str:
    """
    Perceptual nearest match in standardized CIELAB color space against COLOR_TABLE.
    """
    r, g, b = [max(0, min(255, int(c))) for c in rgb]

    # Extreme dark / shadow threshold
    if r < 40 and g < 40 and b < 40:
        return "Black"

    # Extreme bright / white threshold
    if r > 242 and g > 242 and b > 242:
        return "White"

    lab = _rgb_to_standard_lab((r, g, b))

    best_name, best_dist = "Unknown", float("inf")
    for name, c_lab in _COLOR_LAB.items():
        dist = float(np.linalg.norm(lab - c_lab))
        if dist < best_dist:
            best_dist, best_name = dist, name

    return best_name


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    r, g, b = [max(0, min(255, int(c))) for c in rgb]
    return f"#{r:02x}{g:02x}{b:02x}"
