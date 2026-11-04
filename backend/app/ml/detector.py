"""
YOLOv8 object detection using Ultralytics.

Uses pretrained COCO weights (yolov8n.pt).
Inference-only; maintains the exact RawDetection interface
so downstream pipeline, color analysis, and frontend require no changes.
Uses class-agnostic NMS to eliminate duplicate cross-class detections (e.g. bottle vs vase).
"""

import os
from dataclasses import dataclass
from typing import List

import cv2
import numpy as np
from ultralytics import YOLO


# --------------------------------------------------
# MODEL PATHS AND CONFIGURATION
# --------------------------------------------------

_WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "weights")
_MODEL_PATH_SMALL = os.path.join(_WEIGHTS_DIR, "yolov8s.pt")
_MODEL_PATH_NANO = os.path.join(_WEIGHTS_DIR, "yolov8n.pt")
_NAMES_PATH = os.path.join(_WEIGHTS_DIR, "coco.names")

_CONF_THRESHOLD = 0.45
_IOU_THRESHOLD = 0.45
_model = None

# Backwards compatibility: load COCO classes if coco.names exists
if os.path.exists(_NAMES_PATH):
    with open(_NAMES_PATH, "r", encoding="utf-8") as file:
        COCO_CLASSES = [line.strip() for line in file if line.strip()]
else:
    COCO_CLASSES = []


def _get_model() -> YOLO:
    """Lazy load YOLOv8 model instance (preferring higher-accuracy yolov8s.pt)."""
    global _model
    if _model is None:
        if os.path.exists(_MODEL_PATH_SMALL):
            target = _MODEL_PATH_SMALL
        elif os.path.exists(_MODEL_PATH_NANO):
            target = _MODEL_PATH_NANO
        else:
            target = "yolov8s.pt"
        _model = YOLO(target)
    return _model


def get_detector_config() -> dict:
    return {
        "model_name": "YOLOv8s" if os.path.exists(_MODEL_PATH_SMALL) else "YOLOv8n",
        "weights_file": os.path.basename(_MODEL_PATH_SMALL if os.path.exists(_MODEL_PATH_SMALL) else _MODEL_PATH_NANO),
        "conf_threshold": _CONF_THRESHOLD,
        "iou_threshold": _IOU_THRESHOLD,
        "classes_count": len(COCO_CLASSES) if COCO_CLASSES else 80,
        "device": "CPU (PyTorch)",
        "custom_weights_available": os.path.exists(os.path.join(_WEIGHTS_DIR, "custom_fruit.pt")),
    }


def update_detector_config(conf: float = None, iou: float = None) -> dict:
    global _CONF_THRESHOLD, _IOU_THRESHOLD
    if conf is not None:
        _CONF_THRESHOLD = round(max(0.1, min(0.9, conf)), 2)
    if iou is not None:
        _IOU_THRESHOLD = round(max(0.1, min(0.9, iou)), 2)
    return get_detector_config()


# --------------------------------------------------
# DETECTION RESULT CONTRACT
# --------------------------------------------------

@dataclass
class RawDetection:
    label: str
    confidence: float
    x: int
    y: int
    w: int
    h: int


# --------------------------------------------------
# DETECT OBJECTS
# --------------------------------------------------

def detect_objects(image_bgr: np.ndarray) -> List[RawDetection]:
    """
    Run YOLOv8 inference on a 3-channel BGR image.
    Applies:
    1. Notebook vs. Laptop refinement: Detects handheld spiral/bound notebooks
       (which COCO confuses with laptops due to lack of a notebook class).
    2. Cross-class NMS with preservation of objects held or carried by persons.
    3. Spurious surface suppression: Eliminates hallucinated 'dining table' or 'desk'
       boxes that are largely occupied by or smaller than foreground items.
    """
    if image_bgr is None or image_bgr.size == 0:
        return []

    if image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
        raise ValueError("Expected a valid 3-channel BGR image.")

    image_height, image_width = image_bgr.shape[:2]

    if image_height <= 0 or image_width <= 0:
        return []

    model = _get_model()

    # Step 1: Candidate inference without aggressive premature class suppression
    results = model.predict(
        image_bgr,
        conf=0.35,
        iou=_IOU_THRESHOLD,
        agnostic_nms=False,
        verbose=False,
    )[0]

    if results.boxes is None or len(results.boxes) == 0:
        return []

    candidates = []
    for box in results.boxes:
        x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
        conf = float(box.conf[0])
        class_id = int(box.cls[0])
        label = model.names[class_id] if class_id in model.names else f"class_{class_id}"

        x1_clip = max(0, min(int(round(x1)), image_width))
        y1_clip = max(0, min(int(round(y1)), image_height))
        x2_clip = max(0, min(int(round(x2)), image_width))
        y2_clip = max(0, min(int(round(y2)), image_height))
        cw = x2_clip - x1_clip
        ch = y2_clip - y1_clip
        if cw < 4 or ch < 4:
            continue

        candidates.append({
            "label": label,
            "conf": conf,
            "x1": x1_clip, "y1": y1_clip,
            "x2": x2_clip, "y2": y2_clip,
            "w": cw, "h": ch,
        })

    # Step 2: Refine Laptop -> Notebook when held by a person or competing with book
    for c in candidates:
        if c["label"] == "laptop":
            # Check competing book candidate on same box
            has_competing_book = False
            for b in candidates:
                if b["label"] == "book":
                    ix1, iy1 = max(c["x1"], b["x1"]), max(c["y1"], b["y1"])
                    ix2, iy2 = min(c["x2"], b["x2"]), min(c["y2"], b["y2"])
                    if ix2 > ix1 and iy2 > iy1:
                        iarea = (ix2 - ix1) * (iy2 - iy1)
                        c_area = c["w"] * c["h"]
                        b_area = b["w"] * b["h"]
                        iou = iarea / max(1, c_area + b_area - iarea)
                        if iou > 0.45:
                            has_competing_book = True
                            c["conf"] = max(c["conf"], b["conf"])
                            break

            # Check if held in arms / chest of a person
            inside_person = False
            for p in candidates:
                if p["label"] == "person":
                    if (c["x1"] >= p["x1"] - 12 and c["x2"] <= p["x2"] + 12
                            and c["y1"] >= p["y1"] and c["y2"] <= p["y2"]):
                        inside_person = True
                        break

            if has_competing_book or inside_person:
                c["label"] = "notebook"

    # Step 3: Class-agnostic NMS with held-item protection
    candidates.sort(key=lambda item: item["conf"], reverse=True)
    keep = []
    HELD_ITEMS = {
        "notebook", "book", "laptop", "backpack", "handbag", "tie",
        "cell phone", "cup", "bottle", "apple", "banana", "orange",
    }

    for c in candidates:
        discard = False
        c_area = c["w"] * c["h"]
        for k in keep:
            kx1, ky1, kx2, ky2 = k["x1"], k["y1"], k["x2"], k["y2"]
            k_area = k["w"] * k["h"]
            ix1, iy1 = max(c["x1"], kx1), max(c["y1"], ky1)
            ix2, iy2 = min(c["x2"], kx2), min(c["y2"], ky2)
            if ix2 > ix1 and iy2 > iy1:
                iarea = (ix2 - ix1) * (iy2 - iy1)
                iou = iarea / max(1, c_area + k_area - iarea)

                # Do not suppress items held by a person
                if k["label"] == "person" and c["label"] in HELD_ITEMS:
                    continue
                if c["label"] == "person" and k["label"] in HELD_ITEMS:
                    continue

                if iou > _IOU_THRESHOLD:
                    discard = True
                    break
        if not discard:
            keep.append(c)

    # Step 4: Suppress spurious surface/table detections
    # (Tables smaller than or mostly occupied by foreground items sitting on them)
    surfaces_pruned = []
    for c in keep:
        if c["label"] in ("dining table", "desk"):
            c_area = c["w"] * c["h"]
            is_spurious = False
            for o in keep:
                if o is c:
                    continue
                o_area = o["w"] * o["h"]
                ix1, iy1 = max(c["x1"], o["x1"]), max(c["y1"], o["y1"])
                ix2, iy2 = min(c["x2"], o["x2"]), min(c["y2"], o["y2"])
                if ix2 > ix1 and iy2 > iy1:
                    iarea = (ix2 - ix1) * (iy2 - iy1)
                    # If foreground item covers >= 40% of table, or table is smaller than item
                    if (iarea / c_area > 0.40 or c_area < 1.3 * o_area) and o["conf"] >= c["conf"]:
                        is_spurious = True
                        break
            if is_spurious:
                continue
        surfaces_pruned.append(c)

    # Step 5: Format final RawDetection objects meeting confidence threshold
    detections: List[RawDetection] = [
        RawDetection(
            label=b["label"],
            confidence=b["conf"],
            x=b["x1"],
            y=b["y1"],
            w=b["w"],
            h=b["h"],
        )
        for b in surfaces_pruned
        if b["conf"] >= _CONF_THRESHOLD
    ]

    detections.sort(key=lambda item: item.confidence, reverse=True)
    return detections
