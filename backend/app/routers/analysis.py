"""
Analysis routes — implements:
  - Ingestion > Image Upload / Cloud Storage / Serverless Processing
  - Core AI Engine > Object Detection / Colour Recognition / OCR
  - Accessibility > Context Analysis / Scene Description
  - User Control > History & Report

Storage stands in for S3 (local disk under backend/storage/); "Serverless
Processing" is triggered synchronously in-process rather than via a real
AWS Lambda invocation — same contract, different deployment target.
"""
import csv
import io
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

from .. import models, schemas, auth
from ..database import get_db
from ..ml.pipeline import run_pipeline
from ..ml import cvd as cvd_ml
import cv2

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

_STORAGE_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "storage")
_STORAGE_ROOT = os.path.abspath(_STORAGE_ROOT)
_UPLOADS_DIR = os.path.join(_STORAGE_ROOT, "uploads")
_ANNOTATED_DIR = os.path.join(_STORAGE_ROOT, "annotated")
os.makedirs(_UPLOADS_DIR, exist_ok=True)
os.makedirs(_ANNOTATED_DIR, exist_ok=True)

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB, per SRS 2.5 Design Constraints


def _get_or_create_profile(user: models.User, db: Session) -> models.Profile:
    profile = db.query(models.Profile).filter(models.Profile.user_id == user.user_id).first()
    if not profile:
        profile = models.Profile(user_id=user.user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.post("/upload", response_model=schemas.AnalysisOut)
async def upload_and_analyze(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    # ---- Ingestion > Image Upload: validation ------------------------------
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only JPG, JPEG and PNG images are supported.")

    contents = await file.read()
    if len(contents) > _MAX_BYTES:
        raise HTTPException(status_code=400, detail="Image exceeds the 10MB size limit.")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Make sure the bytes really are a decodable image (a renamed .txt or a
    # HEIC photo would otherwise crash later with a confusing 500).
    import numpy as np
    if cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR) is None:
        raise HTTPException(
            status_code=400,
            detail="That file couldn't be read as an image. Please use a valid JPG or PNG.",
        )

    profile = _get_or_create_profile(current_user, db)

    # ---- Ingestion > Cloud Storage (S3 stand-in) ---------------------------
    stored_filename = f"{uuid.uuid4()}{ext}"
    stored_path = os.path.join(_UPLOADS_DIR, stored_filename)
    with open(stored_path, "wb") as f:
        f.write(contents)

    analysis = models.Analysis(
        pro_id=profile.pro_id,
        img_url=f"/storage/uploads/{stored_filename}",
        status="processing",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # ---- Ingestion > Serverless Processing (triggered here) ---------------
    try:
        result = run_pipeline(stored_path, _ANNOTATED_DIR)
    except Exception as exc:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        analysis.status = "error"
        exc = Exception(f"{type(exc).__name__}: {exc}")
        analysis.err_msg = str(exc)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    # ---- Persist Detection rows (Core AI Engine output) --------------------
    for det in result["detections"]:
        db.add(models.Detection(
            ana_id=analysis.ana_id,
            label=det["label"],
            bbox_x=det["bbox_x"], bbox_y=det["bbox_y"],
            bbox_w=det["bbox_w"], bbox_h=det["bbox_h"],
            conf=det["conf"],
            rgb=det["rgb"], color=det["color"], hex=det["hex"],
            pos=det["pos"], area=det["area"],
        ))

    # ---- Persist Scene row (Accessibility > Scene Description) -------------
    scene = models.Scene(
        ana_id=analysis.ana_id,
        type="auto",
        desc=result["scene_text"],
        text=result["scene_text"],
    )
    db.add(scene)

    # ---- Persist OCR rows ---------------------------------------------------
    for ocr in result["ocr_results"]:
        db.add(models.OcrResult(
            ana_id=analysis.ana_id,
            text=ocr["text"],
            bbox_x=ocr["bbox_x"], bbox_y=ocr["bbox_y"],
            bbox_w=ocr["bbox_w"], bbox_h=ocr["bbox_h"],
            conf=ocr["conf"],
        ))

    # ---- Accessibility > CVD Assistance (only if the user set a CVD type) ----
    annotated_final = f"{analysis.ana_id}.jpg"
    os.replace(
        os.path.join(_ANNOTATED_DIR, result["annotated_filename"]),
        os.path.join(_ANNOTATED_DIR, annotated_final),
    )
    cvd_profile = (
        db.query(models.CVDProfile).filter(models.CVDProfile.pro_id == profile.pro_id).first()
    )
    if cvd_profile:
        sev = cvd_profile.severity or "severe"
        img = cv2.imread(os.path.join(_ANNOTATED_DIR, annotated_final))
        sim = cvd_ml.simulate_cvd_image(img, cvd_profile.type, sev)
        sim_name = f"{analysis.ana_id}_cvd.jpg"
        cv2.imwrite(os.path.join(_ANNOTATED_DIR, sim_name), sim)
        db.add(models.ColorTransformation(
            ana_id=analysis.ana_id,
            filter=cvd_profile.type,
            intensity=cvd_ml.SEVERITY_FACTOR.get(sev, 1.0),
            img_clr=f"/storage/annotated/{sim_name}",
        ))
        db.flush()
        for sug in cvd_ml.build_suggestions(result["detections"], cvd_profile.type, sev):
            db.add(models.ColorResult(
                sce_id=scene.sce_id,
                suggested_color=sug["suggested_color"],
                reason=sug["reason"],
                contrast_ratio=sug["contrast_ratio"],
                applied_on=datetime.utcnow(),
            ))

    analysis.status = "done"
    analysis.det_count = result["det_count"]
    analysis.comp_time = result["comp_time"]
    analysis.result_overall = result["scene_text"]
    db.commit()
    db.refresh(analysis)

    return _to_analysis_out(analysis)


def _to_analysis_out(analysis: models.Analysis, annotated_filename: str | None = None) -> schemas.AnalysisOut:
    out = schemas.AnalysisOut.model_validate(analysis)
    ann = f"{analysis.ana_id}.jpg"
    if os.path.exists(os.path.join(_ANNOTATED_DIR, ann)):
        out.annotated_url = f"/storage/annotated/{ann}"
    if analysis.transformations:
        t = analysis.transformations[-1]
        out.cvd_type = t.filter
        out.cvd_url = t.img_clr
    out.color_results = [
        schemas.ColorResultOut.model_validate(cr)
        for sc in analysis.scenes for cr in sc.color_results
    ]
    return out


@router.get("/stats", response_model=schemas.StatsOut)
def stats(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(current_user, db)
    analyses = (
        db.query(models.Analysis).filter(models.Analysis.pro_id == profile.pro_id).all()
    )
    done = [a for a in analyses if a.status == "done"]
    all_detections = [d for a in done for d in a.detections]

    from collections import Counter
    label_counts = Counter(d.label for d in all_detections)
    color_counts = Counter(d.color for d in all_detections if d.color)
    top_object = label_counts.most_common(1)[0][0] if label_counts else None
    top_color = color_counts.most_common(1)[0][0] if color_counts else None
    avg_time = (
        round(sum(a.comp_time or 0 for a in done) / len(done), 2) if done else None
    )

    recent = sorted(analyses, key=lambda a: a.ana_date, reverse=True)[:5]

    return schemas.StatsOut(
        total_analyses=len(analyses),
        total_objects=len(all_detections),
        top_object=top_object,
        top_color=top_color,
        avg_processing_time=avg_time,
        recent=recent,
    )


@router.get("/history", response_model=list[schemas.AnalysisSummaryOut])
def history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(current_user, db)
    analyses = (
        db.query(models.Analysis)
        .filter(models.Analysis.pro_id == profile.pro_id)
        .order_by(models.Analysis.ana_date.desc())
        .all()
    )
    return analyses


@router.get("/{ana_id}", response_model=schemas.AnalysisOut)
def get_analysis(
    ana_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(current_user, db)
    analysis = (
        db.query(models.Analysis)
        .filter(models.Analysis.ana_id == ana_id, models.Analysis.pro_id == profile.pro_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return _to_analysis_out(analysis)


@router.get("/{ana_id}/report")
def get_report(
    ana_id: str,
    fmt: str = Query("json", pattern="^(json|csv|pdf)$"),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(current_user, db)
    analysis = (
        db.query(models.Analysis)
        .filter(models.Analysis.ana_id == ana_id, models.Analysis.pro_id == profile.pro_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    db.add(models.Report(ana_id=analysis.ana_id, fmt=fmt.upper(), type="on-demand"))
    db.commit()

    if fmt == "json":
        payload = _to_analysis_out(analysis).model_dump_json(indent=2)
        return StreamingResponse(
            io.BytesIO(payload.encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=report-{ana_id}.json"},
        )

    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["label", "color", "hex", "confidence", "position"])
        for d in analysis.detections:
            writer.writerow([d.label, d.color, d.hex, f"{d.conf:.2f}", d.pos])
        writer.writerow([])
        writer.writerow(["scene_description", analysis.result_overall or ""])
        return StreamingResponse(
            io.BytesIO(buf.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=report-{ana_id}.csv"},
        )

    # fmt == "pdf"
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 60

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Contextual Colour Analysis Report")
    y -= 30
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Analysis ID: {analysis.ana_id}")
    y -= 16
    c.drawString(50, y, f"Date: {analysis.ana_date}")
    y -= 30

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Detected objects")
    y -= 20
    c.setFont("Helvetica", 10)
    for d in analysis.detections:
        c.drawString(60, y, f"- {d.color} {d.label}  (confidence {d.conf:.2f}, {d.pos})")
        y -= 16
        if y < 80:
            c.showPage()
            y = height - 60

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Scene description")
    y -= 20
    c.setFont("Helvetica", 10)
    for line in simpleSplit(analysis.result_overall or "", "Helvetica", 10, width - 120):
        c.setFont("Helvetica", 10)
        c.drawString(60, y, line)
        y -= 16
        if y < 80:
            c.showPage()
            y = height - 60

    c.save()
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report-{ana_id}.pdf"},
    )
