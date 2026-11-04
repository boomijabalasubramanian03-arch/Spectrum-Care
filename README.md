# Serverless Cloud Assistant for Contextual Color Analysis and Accessibility Support

Built strictly from the ER diagram, functional-module diagram, colour-extraction
flowchart, YOLO flowchart, architecture diagram and workflow diagram supplied
for the project (Mepco Schlenk Engineering College, Mini Project III).

## What's implemented

**Backend (`/backend`)** — FastAPI + SQLAlchemy + OpenCV + a real pretrained YOLO model

*User Control*
- Register / login / logout / session tracking — JWT-based, tested end-to-end

*Ingestion*
- Image Upload — validates JPG/JPEG/PNG and the 10MB limit (SRS 2.5)
- Cloud Storage — local disk under `backend/storage/` standing in for Amazon S3
- Serverless Processing — triggered synchronously in-process, standing in for
  an AWS Lambda invocation (same contract, different deploy target)

*Core AI Engine*
- Object Detection — **real inference**, not a mock: YOLOv4-tiny run through
  OpenCV's DNN module, loaded with weights **pretrained on COCO**
  (`backend/app/ml/weights/`). No training performed or required — this
  matches the SRS exactly ("YOLO Pre-trained Dataset ... COCO dataset
  weights"). Implements every step of the YOLO flowchart in order
  (`app/ml/detector.py`).
- Colour Recognition — OpenCV pipeline implementing the colour-extraction
  flowchart exactly: crop → BGR→HSV → k-means clustering → dominant cluster
  → centroid → nearest-colour lookup (`app/ml/color_extract.py`, `colors.py`)
- OCR — Tesseract via pytesseract (`app/ml/ocr.py`)

*Accessibility*
- Context Analysis — combines object + colour into one label ("Red Apple"),
  exactly the SRS 3.7 transformation
- Scene Description — a full sentence describing everything found, plus any
  OCR text
- Voice Assistance — browser Web Speech API on the frontend (Results page),
  standing in for Amazon Polly since this runs outside AWS

*User Control (continued)*
- History — every analysis a user runs is listed, newest first
- Report — download each analysis as JSON, CSV, or a generated PDF (reportlab)

All 17 ER-diagram entities are modelled in `app/models.py` (User, LoginSession,
Profile, CVDProfile, AccessibilityProfile, AccessPref, Calibration, Analysis,
Detection, DetectionRating, Scene, ColorResult, Report, ColorTransformation,
Feedback, OcrResult, SavedAnalysis) — the ones not yet used by an endpoint
(CVDProfile, Calibration, AccessPref, ColorTransformation, Feedback,
DetectionRating, SavedAnalysis) are ready for the next modules (CVD Assistance,
feedback/rating, bookmarking).

**Frontend (`/frontend`)** — React + Vite
- Login, Register, Dashboard (module checklist), Upload (drag-drop + camera
  capture), Results (annotated image, colour-tagged detection chips, scene
  description, "read aloud" button, report downloads), History
- CVD-safe amber/teal design system (deliberately avoids red/green)

## Quick start
See **RUN.md** - double-click `start.bat` (Windows) or run `./start.sh`. Works offline after the first run. For a developer-style offline launch after dependencies are installed, use `START_OFFLINE.bat`. See **CHANGES.md** for what was fixed.

## Run it locally (developer mode)

### Backend
```
cd backend
pip install -r requirements.txt
# also needs the tesseract-ocr system binary — see requirements-note.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 — the Vite dev server proxies `/api` and `/storage`
to the backend on port 8000.

*Accessibility - CVD Assistance (new)*
- Pick Protanopia / Deuteranopia / Tritanopia + severity on the "My vision" page
  (stored in the CVD_PROFILE entity)
- Every analysis then also produces a simulated "as seen with your CVD" image
  (COLOR_TRANSFORMATION) and warnings when two colours in the scene would look
  almost identical to you, with a suggested high-contrast colour (COLOR_RESULT)

## Model status

The shipped application currently uses the bundled local YOLOv4-tiny COCO weights for general object detection. The optional fruit dataset/training pipeline is **not a completed trained model** because no custom checkpoint is shipped. See `MODEL_AND_DATASET_STATUS.md`.

## Training your own model (optional)

The project ships with a pretrained COCO model (see above). If you want a
model trained on data you actually collected, see `training/TRAINING.md` —
it includes a real, labelled 510-image fruit dataset and a ready-to-run
Google Colab notebook (free GPU). Swapping to it is a one-line environment
variable change; nothing else in the project needs to change.

## Still to build (per the functional-module diagram)

- User Control → Analytics Dashboard (usage stats)
- Calibration flow, detection feedback/rating, bookmarking saved analyses

## Project identity (important)

This project is **not a fruit-detection application**. Its target is the **Serverless Cloud Assistant for Contextual Color Analysis and Accessibility Support** for people with Colour Vision Deficiency (CVD).

The current local AI engine uses a bundled **YOLOv4-tiny model pretrained on COCO** for general object detection, followed by OpenCV colour extraction, contextual labelling, OCR, and CVD assistance. The small `training/dataset` is retained only as an optional future custom-model experiment; it is not the project's core identity and must not be described as a fruit model in the final presentation.

### Cloud implementation status

A deployable AWS serverless scaffold is included under `cloud/`: S3, API Gateway, Lambda, DynamoDB and Amazon Polly. The cloud stack reuses the same `backend/app/ml` inference pipeline. Deployment requires the user's AWS account, AWS CLI/SAM and Docker, so cloud deployment should be treated as the next implementation phase rather than something already completed.


## Windows setup / offline use

See [INSTALL_AND_OFFLINE_GUIDE.md](INSTALL_AND_OFFLINE_GUIDE.md) for the tested Python version, first-time setup, database table creation, offline startup, and troubleshooting. Use Python 3.12.x; do not use Python 3.14 with the currently pinned dependencies.
