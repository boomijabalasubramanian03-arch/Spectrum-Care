"""
Script & Guide to Download More Datasets for Custom Object Detection.

This utility helps you download larger, annotated YOLOv8 datasets from Roboflow Universe
or open datasets to expand beyond the default 510-image fruit set.

Usage:
    python download_more_data.py

Recommended free datasets on Roboflow Universe:
1. Flowers & Plants Dataset (2,000+ images)
2. Everyday Objects / Accessibility Objects Dataset (5,000+ images)
3. Groceries & Packaged Items Dataset (4,000+ images)
"""

import os
import sys

print("""
======================================================================
  DATASET EXPANSION GUIDE FOR CHROMA CONTEXT
======================================================================

1. WHY PRE-TRAINED COCO (yolov8s.pt) IS THE BEST GENERAL ACCURACY ENGINE:
   - Your project's primary detector (`yolov8s.pt`) was trained on COCO:
     * 118,287 real-world images
     * 1.5 million object instances
     * 80 everyday categories (people, vehicles, fruits, bottles, chairs, etc.)
   - If your goal is everyday accessibility detection, the bundled
     `yolov8s.pt` already gives state-of-the-art accuracy.

2. HOW TO DOWNLOAD THOUSANDS OF EXTRA ANNOTATED IMAGES FROM ROBOFLOW:
   Step 1: Install the roboflow package:
           pip install roboflow

   Step 2: Go to https://universe.roboflow.com and search for your topic
           (e.g., 'flower detection' or 'grocery store items' or 'traffic signs').

   Step 3: Click 'Export Dataset' -> Select Format 'YOLOv8' -> Click 'Get Code Snippet'.

   Step 4: Paste your snippet below and run:
           from roboflow import Roboflow
           rf = Roboflow(api_key="YOUR_FREE_API_KEY")
           project = rf.workspace("...").project("...")
           dataset = project.version(1).download("yolov8")

3. RETRAIN WITH THE EXPANDED DATASET:
   Point DATASET path in `train_local.py` to your new downloaded dataset folder,
   then run:
           python train_local.py
======================================================================
""")
