"""
Colour name lookup table -- matches SRS 3.6 examples (Red, Blue, Green,
Yellow, Black, White, Orange, Purple, Brown, Pink) plus enough extra named
colours to make nearest-match meaningful across real photos.

This is the last box in the colour-extraction flowchart:
'Match value against colour name lookup table (nearest colour)'.
"""
import math

# name -> (R, G, B)
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


def nearest_color_name(rgb: tuple) -> str:
    """Euclidean nearest match in RGB space against COLOR_TABLE."""
    r, g, b = rgb
    best_name, best_dist = "Unknown", float("inf")
    for name, (cr, cg, cb) in COLOR_TABLE.items():
        dist = math.sqrt((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2)
        if dist < best_dist:
            best_dist, best_name = dist, name
    return best_name


def rgb_to_hex(rgb: tuple) -> str:
    r, g, b = [max(0, min(255, int(c))) for c in rgb]
    return f"#{r:02x}{g:02x}{b:02x}"
