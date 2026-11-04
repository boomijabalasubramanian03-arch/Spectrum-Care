"""
Object detection using YOUR OWN trained model instead of the pretrained
COCO one in detector.py.

This is the inference side only. To get a custom_fruit.pt (or whatever you
name it) file, run the training notebook in training/train_custom_model.ipynb
on Google Scripts/Colab (free GPU), then drop the resulting weights file
into this weights/ folder and point CUSTOM_WEIGHTS_PATH at it.

Requires the `ultralytics` package (pip install ultralytics) — this is a
different, heavier dependency than the OpenCV-only detector.py, since a
YOLOv8 .pt file needs PyTorch to run, unlike the Darknet .weights format.
"""
import os
from dataclasses import dataclass
from typing import List

import numpy as np
from ultralytics import YOLO

_WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "weights")
CUSTOM_WEIGHTS_PATH = os.path.join(_WEIGHTS_DIR, "custom_fruit.pt")

_CONF_THRESHOLD = 0.4
_model = None


def _load_model():
    global _model
    if _model is None:
        if not os.path.exists(CUSTOM_WEIGHTS_PATH):
            raise FileNotFoundError(
                f"No custom model found at {CUSTOM_WEIGHTS_PATH}. "
                "Train one with training/train_custom_model.ipynb and drop "
                "the resulting .pt file there, or keep using detector.py."
            )
        _model = YOLO(CUSTOM_WEIGHTS_PATH)
    return _model


@dataclass
class RawDetection:
    label: str
    confidence: float
    x: int
    y: int
    w: int
    h: int


def detect_objects(image_bgr: np.ndarray) -> List[RawDetection]:
    model = _load_model()
    results = model.predict(image_bgr, conf=_CONF_THRESHOLD, verbose=False)[0]

    detections: List[RawDetection] = []
    for box in results.boxes:
        x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        label = model.names[cls_id]
        detections.append(
            RawDetection(
                label=label, confidence=conf,
                x=int(x1), y=int(y1), w=int(x2 - x1), h=int(y2 - y1),
            )
        )
    return detections
