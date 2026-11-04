"""Profile and CVD settings for the authenticated user."""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _profile(user, db):
    p = db.query(models.Profile).filter(models.Profile.user_id == user.user_id).first()
    if not p:
        p = models.Profile(user_id=user.user_id)
        db.add(p)
        db.commit()
        db.refresh(p)
    return p


@router.get("", response_model=schemas.ProfileOut)
def get_profile(user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return _profile(user, db)


@router.put("", response_model=schemas.ProfileOut)
def update_profile(
    payload: schemas.ProfileUpdateIn,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    p = _profile(user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return p


@router.get("/cvd", response_model=schemas.CVDProfileOut | None)
def get_cvd(user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    p = _profile(user, db)
    return (
        db.query(models.CVDProfile)
        .filter(models.CVDProfile.pro_id == p.pro_id)
        .order_by(models.CVDProfile.diag_on.desc())
        .first()
    )


@router.put("/cvd", response_model=schemas.CVDProfileOut)
def set_cvd(
    payload: schemas.CVDProfileIn,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    p = _profile(user, db)
    cvd = db.query(models.CVDProfile).filter(models.CVDProfile.pro_id == p.pro_id).first()
    if not cvd:
        cvd = models.CVDProfile(pro_id=p.pro_id, type=payload.type)
        db.add(cvd)
    cvd.type = payload.type
    cvd.severity = payload.severity
    cvd.source = "self-selected"
    cvd.diag_on = datetime.utcnow()
    db.commit()
    db.refresh(cvd)
    return cvd
