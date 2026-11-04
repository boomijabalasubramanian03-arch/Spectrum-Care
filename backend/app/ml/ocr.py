"""
OCR — implements Module 4 'Cloud-Assisted OCR' (srs.docx 3.10 / pptx slide 11):
scans the image for printed text (labels, signs) using Tesseract OCR.
"""
from typing import List, Dict

import cv2
import numpy as np
import os
import shutil

import pytesseract

# Windows installers rarely add Tesseract to PATH - look in the usual places
# so OCR works without the user editing environment variables.
if shutil.which("tesseract") is None:
    for _p in (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ):
        if os.path.exists(_p):
            pytesseract.pytesseract.tesseract_cmd = _p
            break


def extract_text(image_bgr: np.ndarray) -> List[Dict]:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    try:
        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
    except Exception as exc:  # noqa: BLE001
        # Tesseract missing / misconfigured: skip text reading instead of
        # failing the whole analysis (objects + colours still work).
        print(f"WARNING: OCR skipped ({type(exc).__name__}: {exc})")
        return []

    results = []
    n = len(data.get("text", []))
    for i in range(n):
        text = data["text"][i].strip()
        conf_raw = data["conf"][i]
        try:
            conf = float(conf_raw)
        except (TypeError, ValueError):
            conf = -1.0
        if not text or conf < 40:
            continue
        results.append(
            {
                "text": text,
                "bbox_x": data["left"][i],
                "bbox_y": data["top"][i],
                "bbox_w": data["width"][i],
                "bbox_h": data["height"][i],
                "conf": conf / 100.0,
            }
        )
    return results
