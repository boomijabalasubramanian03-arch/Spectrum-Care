"""
CVD Assistance (SRS 3.8) - supports Protanopia, Deuteranopia, Tritanopia.

1. simulate_cvd_image(): shows how an image looks to a person with the
   chosen CVD type (published Brettel/Vienot-style matrices applied in
   linear RGB). Feeds the COLOR_TRANSFORMATION entity.
2. build_suggestions(): looks at the colours found in a scene, simulates
   them, and flags pairs that would look almost the same to the user.
   For each pair it suggests a high-contrast alternative colour name.
   Feeds the COLOR_RESULT entity (suggested_color, reason, contrast_ratio).
"""
import cv2
import numpy as np

from .colors import COLOR_TABLE, rgb_to_hex

CVD_MATRICES = {
    "Protanopia": np.array([[0.567, 0.433, 0.0],
                            [0.558, 0.442, 0.0],
                            [0.0, 0.242, 0.758]]),
    "Deuteranopia": np.array([[0.625, 0.375, 0.0],
                              [0.700, 0.300, 0.0],
                              [0.0, 0.300, 0.700]]),
    "Tritanopia": np.array([[0.950, 0.050, 0.0],
                            [0.0, 0.433, 0.567],
                            [0.0, 0.475, 0.525]]),
}

SEVERITY_FACTOR = {"mild": 0.35, "moderate": 0.7, "severe": 1.0}

# Two simulated colours with contrast below this are "hard to tell apart".
_CONFUSABLE_CONTRAST = 1.5
_CONFUSABLE_DISTANCE = 60  # RGB distance after simulation


def _matrix(cvd_type: str, severity: str):
    base = CVD_MATRICES[cvd_type]
    f = SEVERITY_FACTOR.get(severity or "severe", 1.0)
    return (1 - f) * np.eye(3) + f * base


def _to_linear(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _to_srgb(c):
    c = np.clip(c, 0, 1)
    out = np.where(c <= 0.0031308, c * 12.92, 1.055 * (c ** (1 / 2.4)) - 0.055)
    return out * 255.0


def simulate_cvd_rgb(rgb, cvd_type, severity="severe"):
    lin = _to_linear(np.array(rgb, dtype=np.float64))
    sim = _matrix(cvd_type, severity) @ lin
    return tuple(int(round(v)) for v in _to_srgb(sim))


def simulate_cvd_image(image_bgr, cvd_type, severity="severe"):
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB).astype(np.float64)
    lin = _to_linear(rgb)
    sim = lin @ _matrix(cvd_type, severity).T
    out = _to_srgb(sim).astype(np.uint8)
    return cv2.cvtColor(out, cv2.COLOR_RGB2BGR)


def _luminance(rgb):
    lin = _to_linear(np.array(rgb, dtype=np.float64))
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast_ratio(rgb1, rgb2):
    """WCAG contrast ratio, 1.0 (identical) to 21.0 (black on white)."""
    l1, l2 = _luminance(rgb1), _luminance(rgb2)
    hi, lo = max(l1, l2), min(l1, l2)
    return round((hi + 0.05) / (lo + 0.05), 2)


def _best_alternative(rgb_a, rgb_b, cvd_type, severity):
    """Pick a named colour that stays clearly different from BOTH colours
    after CVD simulation."""
    sa = np.array(simulate_cvd_rgb(rgb_a, cvd_type, severity))
    sb = np.array(simulate_cvd_rgb(rgb_b, cvd_type, severity))
    best_name, best_score = None, -1.0
    for name, rgb in COLOR_TABLE.items():
        s = np.array(simulate_cvd_rgb(rgb, cvd_type, severity))
        score = min(np.linalg.norm(s - sa), np.linalg.norm(s - sb))
        if score > best_score:
            best_name, best_score = name, score
    return best_name


def build_suggestions(detections, cvd_type, severity="severe"):
    """detections: list of dicts with 'context_label', 'color', 'rgb'
    ('r,g,b' string). Returns list of dicts for COLOR_RESULT rows."""
    items = []
    for d in detections:
        try:
            rgb = tuple(int(v) for v in d["rgb"].split(","))
        except Exception:  # noqa: BLE001
            continue
        items.append((d, rgb, simulate_cvd_rgb(rgb, cvd_type, severity)))

    results, seen = [], set()
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            di, rgb_i, sim_i = items[i]
            dj, rgb_j, sim_j = items[j]
            if di["color"] == dj["color"]:
                continue
            key = tuple(sorted((di["color"], dj["color"])))
            if key in seen:
                continue
            dist = float(np.linalg.norm(np.array(sim_i) - np.array(sim_j)))
            ratio = contrast_ratio(sim_i, sim_j)
            if dist < _CONFUSABLE_DISTANCE and ratio < _CONFUSABLE_CONTRAST * 1.4:
                seen.add(key)
                alt = _best_alternative(rgb_i, rgb_j, cvd_type, severity)
                results.append({
                    "suggested_color": alt,
                    "reason": (
                        f"With {cvd_type}, {di['context_label']} and "
                        f"{dj['context_label']} can look almost the same. "
                        f"Rely on the object names, or use {alt} to tell "
                        f"things apart."
                    ),
                    "contrast_ratio": ratio,
                })

    if not results and len(items) > 0:
        results.append({
            "suggested_color": None,
            "reason": f"No confusable colours found in this scene for {cvd_type}.",
            "contrast_ratio": None,
        })

    # High-priority safety and accessibility advisory for traffic lights under CVD
    has_traffic_light = any(d.get("label") == "traffic light" for d in detections)
    if has_traffic_light:
        results.insert(0, {
            "suggested_color": "Position-based",
            "reason": (
                f"Traffic light guidance ({cvd_type}): Standard vertical traffic lights always place "
                f"RED at the top (Stop), YELLOW in the middle (Caution), and GREEN at the bottom (Go). "
                f"When color shades are hard to distinguish, rely on the lamp position."
            ),
            "contrast_ratio": 7.5,
        })

    return results
