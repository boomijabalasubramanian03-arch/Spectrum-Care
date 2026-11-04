"""
Colour extraction for detected objects and scenes.

Key features:
1. Object-Adaptive Spatial Sampling:
   - For person detections: Samples torso/clothing region to eliminate background
     trees, foliage, or sky behind the person.
   - For general objects (vehicles, fruits, etc.): Applies an inner-margin crop to
     exclude background tables, roads, and walls overlapping the bounding box edges.
2. Robust K-Means Clustering (k=5):
   - Separates shadows (tires, dark asphalt, tinted glass) and highlights from
     the true painted/pigmented surface color.
3. Chromatic Priority & Bottle Cap / Feature Detection:
   - Vibrant chromatic colors (e.g., Red on a bus, Yellow on a banana, Blue on a water bottle cap)
     take precedence over transparent water refraction, background shadows, or neutral reflections.
"""

import cv2
import numpy as np

from .colors import nearest_color_name, rgb_to_hex

_KMEANS_K = 5
_KMEANS_SEED = 42

_CHROMATIC_NAMES = {
    "Red", "Orange", "Yellow", "Green", "Blue", "Cyan",
    "Purple", "Pink", "Teal", "Gold", "Maroon", "Navy", "Olive"
}


def _detect_traffic_light_signals(crop_bgr: np.ndarray) -> tuple:
    """
    Analyzes the 3 signal lamp zones (Red at top, Yellow at center, Green at bottom)
    of a traffic light fixture in HSV space.
    Returns (signals_list, representative_rgb, representative_name).
    """
    h, w = crop_bgr.shape[:2]
    if h < 18 or w < 8:
        return ([], None, None)
    is_vertical = h >= w
    zones = []
    if is_vertical:
        z_h = h // 3
        zones.append(("Red", crop_bgr[0:z_h, :]))
        zones.append(("Yellow", crop_bgr[z_h:2 * z_h, :]))
        zones.append(("Green", crop_bgr[2 * z_h:, :]))
    else:
        z_w = w // 3
        zones.append(("Red", crop_bgr[:, 0:z_w]))
        zones.append(("Yellow", crop_bgr[:, z_w:2 * z_w]))
        zones.append(("Green", crop_bgr[:, 2 * z_w:]))

    active = []
    active_rgbs = []
    for expected, z in zones:
        zh, zw = z.shape[:2]
        my, mx = max(1, int(zh * 0.12)), max(1, int(zw * 0.12))
        core = z[my:zh - my, mx:zw - mx]
        hsv = cv2.cvtColor(core, cv2.COLOR_BGR2HSV)
        sat, val, hue = hsv[:, :, 1], hsv[:, :, 2], hsv[:, :, 0]
        if expected == "Red":
            mask = ((hue < 14) | (hue > 165)) & (sat > 45) & (val > 45)
        elif expected == "Yellow":
            mask = (hue >= 14) & (hue <= 42) & (sat > 45) & (val > 60)
        elif expected == "Green":
            mask = (hue >= 40) & (hue <= 98) & (sat > 40) & (val > 45)
        ratio = np.sum(mask) / max(1, core.shape[0] * core.shape[1])
        if ratio > 0.08:
            rgb_core = cv2.cvtColor(core, cv2.COLOR_BGR2RGB)
            mean_rgb = np.mean(rgb_core[mask], axis=0).astype(int)
            active.append(expected)
            active_rgbs.append(tuple(mean_rgb))

    if len(active) >= 3:
        return (active, (211, 150, 6), "Red, Yellow & Green")
    elif len(active) == 2:
        return (active, active_rgbs[0], f"{active[0]} & {active[1]}")
    elif len(active) == 1:
        return (active, active_rgbs[0], active[0])
    return ([], None, None)


def extract_dominant_color(
    image_bgr: np.ndarray,
    x: int,
    y: int,
    w: int,
    h: int,
    label: str = ""
) -> dict:
    # Step 1: Crop to bounding box
    crop = image_bgr[y:y + h, x:x + w]
    if crop.size == 0:
        return {"rgb": (0, 0, 0), "hex": "#000000", "name": "Unknown"}

    ch, cw = crop.shape[:2]
    lbl = (label or "").lower()

    # Special handling for traffic lights: inspect the signal lamp zones
    if lbl == "traffic light":
        signals, rep_rgb, sig_name = _detect_traffic_light_signals(crop)
        if sig_name:
            hex_val = rgb_to_hex(rep_rgb)
            return {
                "rgb": rep_rgb,
                "hex": hex_val,
                "name": sig_name,
                "signals": signals,
            }

    # Step 2: Intelligent region sampling to avoid background contamination
    if lbl == "person" and ch >= 30 and cw >= 30:
        # Focus on the torso / upper body clothing
        sample = crop[int(ch * 0.35):int(ch * 0.85), int(cw * 0.20):int(cw * 0.80)]
        if sample.size == 0:
            sample = crop
    elif lbl in ("landscape", "scene"):
        sample = crop
    elif lbl in ("bottle", "cup"):
        # For bottles, do not crop top/bottom because the cap sits at the very top
        mx = int(cw * 0.08)
        sample = crop[:, mx:cw - mx] if (cw > 20 and mx > 0) else crop
    elif lbl in ("notebook", "book"):
        mx = int(cw * 0.15)
        my = int(ch * 0.15)
        sample = crop[my:ch - my, mx:cw - mx] if (ch > 20 and cw > 20) else crop
    else:
        # Inward margin for objects to remove background table/road/wall
        my = int(ch * 0.12)
        mx = int(cw * 0.12)
        if ch > 24 and cw > 24 and my > 0 and mx > 0:
            sample = crop[my:ch - my, mx:cw - mx]
        else:
            sample = crop

    # Step 3: Convert to HSV for robust saturation/value separation
    hsv = cv2.cvtColor(sample, cv2.COLOR_BGR2HSV)
    pixels = hsv.reshape((-1, 3)).astype(np.float32)

    cv2.setRNGSeed(_KMEANS_SEED)
    k = min(_KMEANS_K, max(1, len(pixels)))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 25, 1.0)
    _, labels_km, centers = cv2.kmeans(
        pixels, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS
    )

    counts = np.bincount(labels_km.flatten(), minlength=k)
    total_px = max(1, len(pixels))

    # Step 4: Map clusters to RGB and identify color properties
    clusters = []
    has_vivid_blue = False

    for i in range(k):
        c_hsv = centers[i]
        hsv_mat = c_hsv.astype(np.uint8).reshape(1, 1, 3)
        bgr_mat = cv2.cvtColor(hsv_mat, cv2.COLOR_HSV2BGR)[0][0]
        r, g, b = int(bgr_mat[2]), int(bgr_mat[1]), int(bgr_mat[0])
        rgb = (r, g, b)

        name = nearest_color_name(rgb)
        frac = counts[i] / total_px
        sat = float(c_hsv[1])
        val = float(c_hsv[2])

        is_shadow = (val < 45) or (r < 45 and g < 45 and b < 45)
        is_chromatic = (name in _CHROMATIC_NAMES) and (not is_shadow) and (sat >= 35) and (val >= 50)

        # For persons, background foliage can be Olive/Green; don't let it override clothing
        if lbl == "person" and name in ("Olive", "Green") and frac < 0.40:
            is_chromatic = False

        if name == "Blue" and sat > 100:
            has_vivid_blue = True

        clusters.append({
            "idx": i,
            "name": name,
            "rgb": rgb,
            "count": int(counts[i]),
            "frac": frac,
            "sat": sat,
            "val": val,
            "is_shadow": is_shadow,
            "is_chromatic": is_chromatic,
        })

    # For bottles: transparent plastic refracts green trees/table producing Teal/Green;
    # if a real Blue cap exists, suppress the refractive Teal/Green
    if lbl in ("bottle", "cup") and has_vivid_blue:
        for cl in clusters:
            if cl["name"] in ("Teal", "Green", "Olive") and cl["sat"] < 170:
                cl["is_chromatic"] = False

    # Step 5: Selection logic
    # Bottle caps and small painted features can be 5% of object area
    min_chromatic_frac = 0.05 if lbl in ("bottle", "cup") else 0.13

    chromatics = [
        cl for cl in clusters
        if cl["is_chromatic"] and cl["frac"] >= min_chromatic_frac
    ]

    if chromatics:
        # Score by coverage weighted by brightness and saturation
        chromatics.sort(
            key=lambda cl: (cl["frac"] ** 0.5) * ((cl["sat"] / 255.0) ** 1.5) * (cl["val"] / 255.0),
            reverse=True,
        )
        winner = chromatics[0]
    else:
        # Priority B: Non-shadow clean cluster (e.g. White shirt, Silver bottle, Beige sweater)
        non_shadows = [cl for cl in clusters if not cl["is_shadow"]]
        if non_shadows:
            non_shadows.sort(key=lambda cl: cl["count"], reverse=True)
            winner = non_shadows[0]
        else:
            clusters.sort(key=lambda cl: cl["count"], reverse=True)
            winner = clusters[0]

    final_name = winner["name"]
    # Natural language adjustments for human-readable accessibility:
    if final_name == "Gold":
        final_name = "Yellow"
    elif lbl == "person" and final_name in ("Silver", "Gray") and winner["rgb"][0] > 180:
        final_name = "Beige" if winner["rgb"][0] > winner["rgb"][2] + 12 else "White"

    return {
        "rgb": winner["rgb"],
        "hex": rgb_to_hex(winner["rgb"]),
        "name": final_name,
    }
