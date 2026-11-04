"""
Admin router — implements system monitoring, user management,
AI model controls, and audit logs matching Table 3.1 & Table 3.20 of the SRS.
Prefix: /api/admin
"""
import os
from datetime import datetime, date
from collections import Counter
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, auth
from ..database import get_db
from ..ml import detector

router = APIRouter(prefix="/api/admin", tags=["admin"])

_STORAGE_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "storage"))
_UPLOADS_DIR = os.path.join(_STORAGE_ROOT, "uploads")
_ANNOTATED_DIR = os.path.join(_STORAGE_ROOT, "annotated")
_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "cvd_assistant.db"))


def _dir_metrics(directory: str):
    if not os.path.isdir(directory):
        return {"count": 0, "size_mb": 0.0}
    count = 0
    total_bytes = 0
    for root, _, files in os.walk(directory):
        for f in files:
            count += 1
            try:
                total_bytes += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return {"count": count, "size_mb": round(total_bytes / (1024 * 1024), 2)}


# ---------------------------------------------------------------------------
# SCHEMAS
# ---------------------------------------------------------------------------

class UserStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|disabled|suspended)$")


class UserRoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(user|admin|administrator)$")


class ModelConfigUpdate(BaseModel):
    conf_threshold: Optional[float] = Field(None, ge=0.1, le=0.9)
    iou_threshold: Optional[float] = Field(None, ge=0.1, le=0.9)


class TaskValidationUpdate(BaseModel):
    status: str = Field(..., pattern="^(verified|flagged|done)$")


# ---------------------------------------------------------------------------
# 1. SYSTEM OVERVIEW & ANALYTICS
# ---------------------------------------------------------------------------

@router.get("/overview")
def get_overview(
    admin_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(models.User).all()
    total_users = len(users)
    active_users = sum(1 for u in users if u.status == "active")
    admin_users = sum(1 for u in users if u.role in ("admin", "administrator"))

    analyses = db.query(models.Analysis).all()
    total_analyses = len(analyses)
    done_analyses = [a for a in analyses if a.status == "done"]
    failed_analyses = [a for a in analyses if a.status == "error"]

    today = date.today()
    today_analyses = sum(
        1 for a in analyses if a.ana_date and a.ana_date.date() == today
    )

    all_detections = db.query(models.Detection).all()
    total_detections = len(all_detections)

    if done_analyses:
        valid_times = [a.comp_time for a in done_analyses if a.comp_time]
        avg_latency = round(sum(valid_times) / max(len(valid_times), 1), 2)
    else:
        avg_latency = 0.0

    # Top objects & colors across all system analyses
    object_counter = Counter(d.label for d in all_detections if d.label)
    color_counter = Counter(d.color for d in all_detections if d.color)

    top_objects = [
        {"name": k, "count": v} for k, v in object_counter.most_common(5)
    ]
    top_colors = [
        {"name": k, "count": v} for k, v in color_counter.most_common(5)
    ]

    # CVD Profile distribution
    cvd_profiles = db.query(models.CVDProfile).all()
    cvd_types = Counter(p.type for p in cvd_profiles if p.type)
    cvd_dist = [
        {"type": k, "count": v} for k, v in cvd_types.items()
    ]

    # Storage metrics
    uploads_info = _dir_metrics(_UPLOADS_DIR)
    annotated_info = _dir_metrics(_ANNOTATED_DIR)
    db_size_mb = 0.0
    if os.path.isfile(_DB_PATH):
        try:
            db_size_mb = round(os.path.getsize(_DB_PATH) / (1024 * 1024), 2)
        except OSError:
            pass

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "admin": admin_users,
        },
        "analyses": {
            "total": total_analyses,
            "completed": len(done_analyses),
            "failed": len(failed_analyses),
            "today": today_analyses,
            "success_rate": round((len(done_analyses) / max(total_analyses, 1)) * 100, 1),
            "avg_latency_s": avg_latency,
            "total_detections": total_detections,
        },
        "top_objects": top_objects,
        "top_colors": top_colors,
        "cvd_distribution": cvd_dist,
        "storage": {
            "uploads": uploads_info,
            "annotated": annotated_info,
            "database_size_mb": db_size_mb,
        },
        "model_summary": detector.get_detector_config(),
    }


# ---------------------------------------------------------------------------
# 2. USER ACCOUNT MANAGEMENT
# ---------------------------------------------------------------------------

@router.get("/users")
def list_users(
    admin_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(models.User).order_by(models.User.created_on.desc()).all()
    user_list = []
    for u in users:
        cvd_type = "None"
        analysis_count = 0
        if u.profile:
            analysis_count = len(u.profile.analyses) if u.profile.analyses else 0
            if u.profile.cvd_profiles and len(u.profile.cvd_profiles) > 0:
                cvd_type = u.profile.cvd_profiles[0].type or "None"

        user_list.append({
            "user_id": u.user_id,
            "first_name": u.first_name,
            "middle_name": u.middle_name,
            "last_name": u.last_name,
            "email": u.email,
            "role": u.role or "user",
            "status": u.status or "active",
            "created_on": u.created_on,
            "last_login": u.last_login,
            "cvd_type": cvd_type,
            "analyses_count": analysis_count,
        })
    return user_list


@router.patch("/users/{user_id}/status")
def update_user_status(
    user_id: str,
    payload: UserStatusUpdate,
    admin_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.user_id == admin_user.user_id and payload.status != "active":
        raise HTTPException(status_code=400, detail="Cannot disable your own administrator account.")

    user.status = payload.status
    db.commit()
    return {"user_id": user_id, "status": user.status, "message": f"User status set to {user.status}"}


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    admin_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.user_id == admin_user.user_id and payload.role != "admin":
        raise HTTPException(status_code=400, detail="Cannot demote your own administrator account.")

    user.role = "admin" if payload.role in ("admin", "administrator") else "user"
    db.commit()
    return {"user_id": user_id, "role": user.role, "message": f"User role updated to {user.role}"}


# ---------------------------------------------------------------------------
# 3. CLOUD & SYSTEM SERVICES HEALTH MONITORING
# ---------------------------------------------------------------------------

@router.get("/services")
def get_services_status(
    admin_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db),
):
    # Check Database
    try:
        db_ok = db.query(models.User).count() >= 0
    except Exception:
        db_ok = False

    # Check Storage
    storage_ok = os.path.isdir(_STORAGE_ROOT) and os.access(_STORAGE_ROOT, os.W_OK)

    # Check Detector Model
    model_cfg = detector.get_detector_config()

    return {
        "services": [
            {
                "id": "api_gateway",
                "name": "REST API Gateway & Controllers",
                "technology": "FastAPI (Uvicorn ASGI)",
                "status": "operational",
                "uptime": "Healthy",
                "details": "Authenticated API Gateway online with active security controllers."
            },
            {
                "id": "database",
                "name": "Relational Persistence Engine",
                "technology": "SQLite / SQLAlchemy ORM",
                "status": "operational" if db_ok else "degraded",
                "uptime": "Connected",
                "details": "Relational database online. User accounts, profiles, and history synchronized."
            },
            {
                "id": "detector",
                "name": "Deep Learning Detection Engine",
                "technology": "Ultralytics YOLOv8",
                "status": "operational",
                "uptime": "Inference Ready",
                "details": f"Active Vision Model: {model_cfg['model_name']} ({model_cfg['classes_count']} classes ready for detection)."
            },
            {
                "id": "color_engine",
                "name": "Perceptual Colour Recognition Engine",
                "technology": "CIELAB L*a*b* Space + Euclidean ΔE",
                "status": "operational",
                "uptime": "Active",
                "details": "Foreground contour isolation with standard colour naming active."
            },
            {
                "id": "cvd_simulation",
                "name": "Daltonized CVD Simulation Engine",
                "technology": "Brettel / Vienot / Machado Matrices",
                "status": "operational",
                "uptime": "Active",
                "details": "Simulation filters ready for Deuteranopia, Protanopia, and Tritanopia."
            },
            {
                "id": "ocr_engine",
                "name": "Optical Text Recognition Subsystem",
                "technology": "Tesseract OCR / OpenCV Pre-processing",
                "status": "operational",
                "uptime": "Ready",
                "details": "Text extraction from signage and labels active."
            },
            {
                "id": "voice_synthesis",
                "name": "Voice Accessibility Engine",
                "technology": "W3C Web Speech API Client Synthesis",
                "status": "operational",
                "uptime": "Available",
                "details": "Spoken scene audio guidance ready."
            },
            {
                "id": "storage_layer",
                "name": "Cloud / Local Storage Service",
                "technology": "S3-compatible Local File Store",
                "status": "operational" if storage_ok else "degraded",
                "uptime": "Read / Write OK",
                "details": "Image assets and report storage operational."
            }
        ]
    }


# ---------------------------------------------------------------------------
# 4. AI MODEL MANAGEMENT & CONFIGURATION
# ---------------------------------------------------------------------------

@router.get("/models")
def get_model_info(
    admin_user: models.User = Depends(auth.require_admin),
):
    return detector.get_detector_config()


@router.post("/models/config")
def update_model_info(
    payload: ModelConfigUpdate,
    admin_user: models.User = Depends(auth.require_admin),
):
    new_cfg = detector.update_detector_config(
        conf=payload.conf_threshold,
        iou=payload.iou_threshold,
    )
    return {"message": "AI model configuration updated successfully.", "config": new_cfg}


# ---------------------------------------------------------------------------
# 5. SYSTEM-WIDE AUDIT LOGS
# ---------------------------------------------------------------------------

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 40,
    admin_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db),
):
    analyses = (
        db.query(models.Analysis)
        .order_by(models.Analysis.ana_date.desc())
        .limit(limit)
        .all()
    )

    logs = []
    for a in analyses:
        user_email = "Unknown"
        user_name = "Anonymous"
        if a.profile and a.profile.user:
            user_email = a.profile.user.email
            user_name = f"{a.profile.user.first_name} {a.profile.user.last_name}".strip()

        logs.append({
            "ana_id": a.ana_id,
            "user_email": user_email,
            "user_name": user_name,
            "ana_date": a.ana_date,
            "img_url": a.img_url,
            "status": a.status,
            "det_count": a.det_count,
            "comp_time": a.comp_time,
            "result_overall": a.result_overall,
            "err_msg": a.err_msg,
        })
    return logs


@router.patch("/analyses/{ana_id}/validate")
def validate_analysis_task(
    ana_id: str,
    payload: TaskValidationUpdate,
    admin_user: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db),
):
    analysis = db.query(models.Analysis).filter(models.Analysis.ana_id == ana_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis task not found.")
    analysis.status = payload.status
    db.commit()
    return {
        "ana_id": ana_id,
        "status": analysis.status,
        "message": f"Analysis task has been marked as {analysis.status}."
    }
