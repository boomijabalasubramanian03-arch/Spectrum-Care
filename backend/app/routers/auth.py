"""
Authentication routes — implements the 'User Control > Authentication'
functional module and the USER / LOGIN_SESSION entities from the ER diagram.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user = models.User(
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        last_name=payload.last_name,
        email=payload.email,
        pass_hash=auth.hash_password(payload.password),
        role="user",
        status="active",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    db.refresh(user)

    # Every user gets a bare Profile row created on registration (Owns 1:1).
    profile = models.Profile(user_id=user.user_id)
    db.add(profile)
    db.commit()

    return user


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not auth.verify_password(payload.password, user.pass_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="This account is disabled.")

    user.last_login = datetime.utcnow()

    session = models.LoginSession(user_id=user.user_id, status="active")
    db.add(session)
    db.commit()
    db.refresh(session)

    token = auth.create_access_token({"sub": user.user_id, "sid": session.session_id})

    return schemas.TokenResponse(
        access_token=token,
        session_id=session.session_id,
        user=user,
    )


@router.post("/logout")
def logout(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(models.LoginSession)
        .filter(models.LoginSession.user_id == current_user.user_id, models.LoginSession.status == "active")
        .order_by(models.LoginSession.login_time.desc())
        .first()
    )
    if session:
        session.status = "closed"
        session.logout_time = datetime.utcnow()
        db.commit()
    return {"detail": "Logged out."}


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
