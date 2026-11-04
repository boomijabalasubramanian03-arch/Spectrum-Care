"""
High-Accuracy Custom Model Trainer with Transfer Learning & Data Augmentation.

Key improvements:
1. Starts from `yolov8s.pt` (Small checkpoint - higher capacity than Nano).
2. Uses advanced online data augmentations (Mosaic, Mixup, HSV shifts, rotation, scaling)
   to artificially multiply effective dataset size 5x-10x and prevent overfitting on small datasets.
3. Uses local weights file directly so internet is not required.
4. Copies the resulting `best.pt` directly into `backend/app/ml/weights/custom_model.pt`.
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(HERE, "dataset")
WEIGHTS_DIR = os.path.join(HERE, "..", "backend", "app", "ml", "weights")
BASE_WEIGHTS = os.path.join(WEIGHTS_DIR, "yolov8s.pt")
if not os.path.exists(BASE_WEIGHTS):
    BASE_WEIGHTS = os.path.join(WEIGHTS_DIR, "yolov8n.pt")
OUT = os.path.join(WEIGHTS_DIR, "custom_fruit.pt")

try:
    from ultralytics import YOLO
except ImportError:
    sys.exit("Install ultralytics first: pip install ultralytics")

# Ensure dataset YAML exists with absolute paths
yaml_path = os.path.join(DATASET, "data_local.yaml")
with open(yaml_path, "w", encoding="utf-8") as f:
    f.write(
        f"path: {DATASET.replace(os.sep, '/')}\n"
        f"train: train/images\n"
        f"val: valid/images\n"
        f"nc: 6\n"
        f"names:\n"
        f"  0: Apple\n"
        f"  1: Banana\n"
        f"  2: Grape\n"
        f"  3: Orange\n"
        f"  4: Pineapple\n"
        f"  5: Watermelon\n"
    )

print(f"Loading base transfer-learning checkpoint: {BASE_WEIGHTS}")
model = YOLO(BASE_WEIGHTS)

print("Starting training with advanced data augmentation to multiply dataset diversity...")
results = model.train(
    data=yaml_path,
    epochs=30,             # Sufficient for fine-tuning on pre-trained backbone
    imgsz=640,            # High resolution for fine feature extraction
    batch=8,              # Safe batch size for standard laptops / CPU / GPU
    # Advanced data augmentation for small dataset expansion:
    hsv_h=0.015,          # Hue variation
    hsv_s=0.6,            # Saturation jitter
    hsv_v=0.4,            # Brightness jitter
    degrees=10.0,         # Slight rotation
    translate=0.1,        # Translation
    scale=0.5,            # Multi-scale zooming
    fliplr=0.5,           # Horizontal flip
    mosaic=1.0,           # Mosaic augmentation (combines 4 images into 1)
    mixup=0.15,           # Mixup augmentation (blends 2 images)
    name="custom_detector",
    project=os.path.join(HERE, "runs"),
    exist_ok=True,
    verbose=True,
)

metrics = model.val()
print(f"\nFinal Validation mAP50 = {metrics.box.map50:.3f}")

best = os.path.join(HERE, "runs", "custom_detector", "weights", "best.pt")
if os.path.exists(best):
    shutil.copy(best, OUT)
    print(f"Successfully saved high-accuracy weights -> {os.path.abspath(OUT)}")
    print("To use these weights, start the backend with: set USE_CUSTOM_MODEL=1")
else:
    print(f"Warning: {best} not found.")
