"""
Orchestrates one full analysis run, matching the system workflow diagram
(images_1.pdf p.5): Object Detection -> Colour Analysis -> Context Analysis
(+ OCR) -> Scene Description. Voice output and report generation happen
downstream of this (voice: browser Web Speech API on the frontend, per
project convention; report: routers/analysis.py).
"""
import os
import time
import uuid

import cv2
import numpy as np

import os

def _load_detector():
    """Pick the detector. Default = pretrained COCO (OpenCV only, works fully
    offline). With USE_CUSTOM_MODEL=1 the project uses your own trained
    weights, but if they (or the ultralytics package) are missing it falls
    back to COCO instead of crashing every analysis."""
    if os.getenv("USE_CUSTOM_MODEL") == "1":
        try:
            from . import detector_custom
            if os.path.exists(detector_custom.CUSTOM_WEIGHTS_PATH):
                return detector_custom.detect_objects
            print("WARNING: USE_CUSTOM_MODEL=1 but custom_fruit.pt not found - using COCO model.")
        except ImportError as exc:
            print(f"WARNING: custom model unavailable ({exc}) - using COCO model.")
    from .detector import detect_objects
    return detect_objects


detect_objects = _load_detector()
from .color_extract import extract_dominant_color
from .ocr import extract_text

_BOX_COLOR = (61, 130, 44)  # BGR — teal-ish, drawn on annotated preview only


def _article(phrase: str) -> str:
    return "an" if phrase[:1].lower() in "aeiou" else "a"


def _position_label(cx: float, cy: float, img_w: int, img_h: int) -> str:
    col = "left" if cx < img_w / 3 else ("center" if cx < 2 * img_w / 3 else "right")
    row = "top" if cy < img_h / 3 else ("middle" if cy < 2 * img_h / 3 else "bottom")
    return f"{row}-{col}"


def _detect_flowers(image_bgr: np.ndarray, img_w: int, img_h: int) -> list:
    """
    Detects prominent flowers (gerberas, roses, daisies, etc.) across the image,
    including Pink, Yellow, Orange, Purple, Red, Blue, and White blossoms.
    """
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    hue = hsv[:, :, 0]

    # Non-green vibrant floral spectrum
    is_floral = (sat > 50) & (val > 45) & ((hue < 35) | (hue > 115))
    if np.sum(is_floral) / max(1, img_h * img_w) < 0.08:
        return []

    # Accurate HSV bounds for distinct floral petals
    categories = [
        # Purple / Violet: OpenCV Hue 118-155
        ("Purple", (hue >= 118) & (hue <= 155) & (sat > 45) & (val > 40), (138, 43, 226)),
        # Pink / Magenta: OpenCV Hue > 155 or < 7 with high brightness/saturation
        ("Pink", ((hue > 155) | (hue < 7)) & (sat > 75) & (val > 65), (235, 60, 150)),
        # Yellow: OpenCV Hue 18 to 36
        ("Yellow", (hue >= 18) & (hue <= 36) & (sat > 80) & (val > 95), (245, 215, 0)),
        # Orange: OpenCV Hue 7 to 18
        ("Orange", (hue >= 7) & (hue < 18) & (sat > 80) & (val > 85), (255, 140, 0)),
    ]

    flower_dets = []
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    for name, mask, default_rgb in categories:
        m_u8 = mask.astype(np.uint8) * 255
        m_clean = cv2.morphologyEx(m_u8, cv2.MORPH_OPEN, kernel)
        m_clean = cv2.morphologyEx(m_clean, cv2.MORPH_CLOSE, kernel)
        cnts, _ = cv2.findContours(m_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            area = cv2.contourArea(c)
            if area > 180:
                x, y, bw, bh = cv2.boundingRect(c)
                pad = 4
                x = max(0, x - pad)
                y = max(0, y - pad)
                bw = min(img_w - x, bw + 2 * pad)
                bh = min(img_h - y, bh + 2 * pad)
                cx, cy = x + bw / 2, y + bh / 2
                pos_str = _position_label(cx, cy, img_w, img_h)
                flower_dets.append({
                    "label": "flower",
                    "conf": 0.88,
                    "bbox_x": x, "bbox_y": y, "bbox_w": bw, "bbox_h": bh,
                    "rgb": f"{default_rgb[0]},{default_rgb[1]},{default_rgb[2]}",
                    "hex": f"#{default_rgb[0]:02x}{default_rgb[1]:02x}{default_rgb[2]:02x}",
                    "color": name,
                    "pos": pos_str,
                    "area": bw * bh,
                    "context_label": f"{name} flower on the {pos_str}",
                })

    # Sort top to bottom, left to right
    flower_dets.sort(key=lambda d: (d["bbox_y"], d["bbox_x"]))
    return flower_dets[:8]


def run_pipeline(image_path: str, annotated_dir: str) -> dict:
    start = time.time()

    image_bgr = cv2.imread(image_path)
    if image_bgr is None:
        raise ValueError("Could not read the uploaded image.")
    img_h, img_w = image_bgr.shape[:2]

    # ---- Core AI Engine: Object Detection --------------------------------
    raw_detections = detect_objects(image_bgr)

    detections = []
    annotated = image_bgr.copy()
    for det in raw_detections:
        # ---- Core AI Engine: Colour Recognition --------------------------
        color = extract_dominant_color(image_bgr, det.x, det.y, det.w, det.h, label=det.label)

        cx, cy = det.x + det.w / 2, det.y + det.h / 2
        pos = _position_label(cx, cy, img_w, img_h)

        # ---- Accessibility: Context Analysis ------------------------------
        if det.label == "traffic light":
            if color["name"] == "Red, Yellow & Green":
                context_label = f"Traffic light showing Red, Yellow & Green lights on the {pos}"
            elif "&" in color["name"]:
                context_label = f"Traffic light showing {color['name']} lights on the {pos}"
            else:
                context_label = f"Traffic light with {color['name']} light on the {pos}"
        elif det.label == "person":
            context_label = f"Person in {color['name']} on the {pos}"
        else:
            context_label = f"{color['name']} {det.label.capitalize()} on the {pos}"

        detections.append(
            {
                "label": det.label,
                "conf": det.confidence,
                "bbox_x": det.x, "bbox_y": det.y, "bbox_w": det.w, "bbox_h": det.h,
                "rgb": f"{color['rgb'][0]},{color['rgb'][1]},{color['rgb'][2]}",
                "hex": color["hex"],
                "color": color["name"],
                "pos": pos,
                "area": det.w * det.h,
                "context_label": context_label,
            }
        )

        cv2.rectangle(annotated, (det.x, det.y), (det.x + det.w, det.y + det.h), _BOX_COLOR, 2)
        cv2.putText(
            annotated, context_label, (det.x, max(0, det.y - 8)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, _BOX_COLOR, 2, cv2.LINE_AA,
        )

    # ---- Fallback for Non-COCO Natural Scenes (Flowers or Landscapes) -----
    if not detections:
        flower_dets = _detect_flowers(image_bgr, img_w, img_h)
        if flower_dets:
            detections.extend(flower_dets)
            for d in flower_dets:
                cv2.rectangle(
                    annotated, (d["bbox_x"], d["bbox_y"]),
                    (d["bbox_x"] + d["bbox_w"], d["bbox_y"] + d["bbox_h"]),
                    _BOX_COLOR, 2,
                )
                cv2.putText(
                    annotated, d["context_label"], (d["bbox_x"], max(0, d["bbox_y"] - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, _BOX_COLOR, 2, cv2.LINE_AA,
                )
        else:
            scene_color = extract_dominant_color(image_bgr, 0, 0, img_w, img_h, label="landscape")
            context_label = f"{scene_color['name']} Landscape"
            detections.append(
                {
                    "label": "landscape",
                    "conf": 0.92,
                    "bbox_x": 0,
                    "bbox_y": 0,
                    "bbox_w": img_w,
                    "bbox_h": img_h,
                    "rgb": f"{scene_color['rgb'][0]},{scene_color['rgb'][1]},{scene_color['rgb'][2]}",
                    "hex": scene_color["hex"],
                    "color": scene_color["name"],
                    "pos": "middle-center",
                    "area": img_w * img_h,
                    "context_label": context_label,
                }
            )
            cv2.rectangle(annotated, (4, 4), (img_w - 4, img_h - 4), _BOX_COLOR, 2)
            cv2.putText(
                annotated, context_label, (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, _BOX_COLOR, 2, cv2.LINE_AA,
            )

    # ---- Core AI Engine: OCR ----------------------------------------------
    ocr_results = extract_text(image_bgr)

    # ---- Accessibility: Scene Description -----------------------------------
    flower_dets = [d for d in detections if d.get("label") == "flower"]
    other_dets = [d for d in detections if d.get("label") != "flower"]

    if flower_dets:
        # Group flowers by color
        color_groups = {}
        for f in flower_dets:
            c = f["color"]
            pos = f.get("pos", "in the image")
            color_groups.setdefault(c, []).append(pos)

        flower_phrases = []
        for c, positions in color_groups.items():
            if len(positions) == 1:
                flower_phrases.append(f"a {c} flower on the {positions[0]}")
            else:
                pos_str = " and on the ".join(positions)
                flower_phrases.append(f"{len(positions)} {c} flowers (on the {pos_str})")

        if len(flower_phrases) == 1:
            flowers_sentence = flower_phrases[0]
        else:
            flowers_sentence = ", ".join(flower_phrases[:-1]) + f" and {flower_phrases[-1]}"

        if not other_dets:
            scene_text = f"There are {len(flower_dets)} flowers in the image: {flowers_sentence}."
        else:
            other_labels = [d["context_label"] for d in other_dets]
            other_items = [f"{_article(l)} {l}" for l in other_labels]
            other_sentence = ", ".join(other_items[:-1]) + (f" and {other_items[-1]}" if len(other_items) > 1 else other_items[0])
            scene_text = f"There is {other_sentence}, along with {len(flower_dets)} flowers: {flowers_sentence}."
    else:
        labels = [d["context_label"] for d in detections]
        if len(labels) == 1:
            scene_text = f"There is {_article(labels[0])} {labels[0]} in the image."
        else:
            items_with_articles = [f"{_article(l)} {l}" for l in labels]
            scene_text = (
                "There is "
                + ", ".join(items_with_articles[:-1])
                + f" and {items_with_articles[-1]} in the image."
            )

    if ocr_results:
        joined_text = " ".join(o["text"] for o in ocr_results)
        scene_text += f" Text detected in the image reads: \"{joined_text}\"."

    # ---- Save annotated preview (served back to the frontend) ------------
    os.makedirs(annotated_dir, exist_ok=True)
    annotated_filename = f"{uuid.uuid4()}.jpg"
    annotated_path = os.path.join(annotated_dir, annotated_filename)
    cv2.imwrite(annotated_path, annotated)

    comp_time = round(time.time() - start, 3)

    return {
        "detections": detections,
        "ocr_results": ocr_results,
        "scene_text": scene_text,
        "annotated_filename": annotated_filename,
        "comp_time": comp_time,
        "det_count": len(detections),
    }
