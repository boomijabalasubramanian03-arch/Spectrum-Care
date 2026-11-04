"""
Object detection — implements the YOLO detection flowchart (images_1.pdf p.6)
step by step:

  1. Receive image from S3            -> caller passes the loaded image array
  2. Resize image to model input size -> blobFromImage(..., (416, 416), ...)
  3. Normalize pixel values 0-255 -> 0-1 -> blobFromImage(scalefactor=1/255)
  4. Divide into a grid; each cell predicts an object centre -> handled
     internally by the Darknet YOLO graph itself
  5. Run forward pass through YOLO neural network -> net.forward()
  6. Generate candidate boxes with class probabilities per cell -> raw output
  7. Filter out boxes below confidence threshold (~0.5)
  8. Apply Non-Max Suppression (NMS) to remove duplicate overlapping boxes
  9. Output final bounding boxes + object labels + confidence scores

Weights: yolov4-tiny, pretrained on the COCO dataset (SRS 1.3 / 2.4 /
pptx slide 6 "YOLO Pre-trained Dataset ... COCO dataset weights") — no
training performed or required, this is inference-only against a
pretrained model, exactly as the diagrams specify.
"""
import os
from dataclasses import dataclass
from typing import List

import cv2
import numpy as np

_WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "weights")
_CFG_PATH = os.path.join(_WEIGHTS_DIR, "yolov4-tiny.cfg")
_WEIGHTS_PATH = os.path.join(_WEIGHTS_DIR, "yolov4-tiny.weights")
_NAMES_PATH = os.path.join(_WEIGHTS_DIR, "coco.names")

_INPUT_SIZE = (416, 416)
_CONF_THRESHOLD = 0.5
_NMS_THRESHOLD = 0.4

with open(_NAMES_PATH) as f:
    COCO_CLASSES = [line.strip() for line in f if line.strip()]

_net = cv2.dnn.readNetFromDarknet(_CFG_PATH, _WEIGHTS_PATH)
_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
_layer_names = _net.getLayerNames()
_output_layers = [_layer_names[i - 1] for i in _net.getUnconnectedOutLayers().flatten()]


@dataclass
class RawDetection:
    label: str
    confidence: float
    x: int  # top-left, pixel coords in the original image
    y: int
    w: int
    h: int


def detect_objects(image_bgr: np.ndarray) -> List[RawDetection]:
    h_img, w_img = image_bgr.shape[:2]

    # Steps 2-3: resize to model input size, normalize 0-255 -> 0-1
    blob = cv2.dnn.blobFromImage(
        image_bgr, 1 / 255.0, _INPUT_SIZE, swapRB=True, crop=False
    )
    _net.setInput(blob)

    # Step 5: forward pass
    outputs = _net.forward(_output_layers)

    # Steps 6-7: collect candidate boxes, filter by confidence threshold
    boxes, confidences, class_ids = [], [], []
    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = int(np.argmax(scores))
            confidence = float(scores[class_id])
            if confidence < _CONF_THRESHOLD:
                continue
            cx, cy, bw, bh = detection[0:4]
            cx, cy, bw, bh = cx * w_img, cy * h_img, bw * w_img, bh * h_img
            x = int(cx - bw / 2)
            y = int(cy - bh / 2)
            boxes.append([x, y, int(bw), int(bh)])
            confidences.append(confidence)
            class_ids.append(class_id)

    # Step 8: Non-Max Suppression
    results: List[RawDetection] = []
    if boxes:
        indices = cv2.dnn.NMSBoxes(boxes, confidences, _CONF_THRESHOLD, _NMS_THRESHOLD)
        for i in np.array(indices).flatten() if len(indices) else []:
            x, y, w, h = boxes[i]
            x, y = max(0, x), max(0, y)
            w = min(w, w_img - x)
            h = min(h, h_img - y)
            if w <= 0 or h <= 0:
                continue
            results.append(
                RawDetection(
                    label=COCO_CLASSES[class_ids[i]],
                    confidence=confidences[i],
                    x=x, y=y, w=w, h=h,
                )
            )

    # Step 9: final boxes + labels + confidence scores
    return results
