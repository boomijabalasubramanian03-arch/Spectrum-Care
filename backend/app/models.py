"""
Database models — one class per entity box in the ER diagram (images_1.pdf p.1/p.2).
Only fields that appear on the diagram are included. Relationships follow the
diamonds (Owns, Has, Performs, Uploads, Contains, OccursIn, Generates,
AppliesTransform, Receives, Includes, SavedIn, RatedBy, Produces, IdentifiedBy,
Bookmarks/Saved By/Saved For, BasedOn, UsesSettings).
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship

from .database import Base


def gen_id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# USER CONTROL — USER, LOGIN_SESSION
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=gen_id)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    pass_hash = Column(String, nullable=False)
    role = Column(String, default="user")  # user | administrator
    created_on = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    status = Column(String, default="active")

    profile = relationship("Profile", back_populates="user", uselist=False)
    sessions = relationship("LoginSession", back_populates="user")


class LoginSession(Base):
    __tablename__ = "login_sessions"

    session_id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    login_time = Column(DateTime, default=datetime.utcnow)
    logout_time = Column(DateTime, nullable=True)
    device = Column(String, nullable=True)
    ip_addr = Column(String, nullable=True)
    status = Column(String, default="active")

    user = relationship("User", back_populates="sessions")


# ---------------------------------------------------------------------------
# PROFILE + CVD_PROFILE + ACCESSIBILITY_PROFILE + ACCESS_PREF + CALIBRATION
# ---------------------------------------------------------------------------

class Profile(Base):
    __tablename__ = "profiles"

    pro_id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    dob = Column(DateTime, nullable=True)
    gender = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    street = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    acc_mode = Column(String, nullable=True)  # accessibility mode toggle

    user = relationship("User", back_populates="profile")
    cvd_profiles = relationship("CVDProfile", back_populates="profile")
    accessibility_profile = relationship(
        "AccessibilityProfile", back_populates="profile", uselist=False
    )
    calibrations = relationship("Calibration", back_populates="profile")
    analyses = relationship("Analysis", back_populates="profile")


class CVDProfile(Base):
    __tablename__ = "cvd_profiles"

    cvd_id = Column(String, primary_key=True, default=gen_id)
    pro_id = Column(String, ForeignKey("profiles.pro_id"), nullable=False)
    type = Column(String, nullable=False)  # Protanopia | Deuteranopia | Tritanopia
    severity = Column(String, nullable=True)
    diag_on = Column(DateTime, nullable=True)
    source = Column(String, nullable=True)
    calib_on = Column(DateTime, nullable=True)
    conf_level = Column(Float, nullable=True)

    profile = relationship("Profile", back_populates="cvd_profiles")


class AccessibilityProfile(Base):
    __tablename__ = "accessibility_profiles"

    acc_id = Column(String, primary_key=True, default=gen_id)
    pro_id = Column(String, ForeignKey("profiles.pro_id"), nullable=False)
    font_size = Column(String, nullable=True)
    contrast_pref = Column(String, nullable=True)
    audio_pref = Column(Boolean, default=True)
    voice_pref = Column(String, nullable=True)
    color_pref = Column(String, nullable=True)
    lang = Column(String, default="en")

    profile = relationship("Profile", back_populates="accessibility_profile")
    prefs = relationship("AccessPref", back_populates="accessibility_profile")
    analyses = relationship("Analysis", back_populates="accessibility_profile")


class AccessPref(Base):
    __tablename__ = "access_prefs"

    pref_id = Column(String, primary_key=True, default=gen_id)
    acc_id = Column(String, ForeignKey("accessibility_profiles.acc_id"), nullable=False)
    name = Column(String, nullable=False)
    value = Column(String, nullable=False)
    type = Column(String, nullable=True)

    accessibility_profile = relationship("AccessibilityProfile", back_populates="prefs")


class Calibration(Base):
    __tablename__ = "calibrations"

    cal_id = Column(String, primary_key=True, default=gen_id)
    pro_id = Column(String, ForeignKey("profiles.pro_id"), nullable=False)
    cal_type = Column(String, nullable=True)
    cal_date = Column(DateTime, default=datetime.utcnow)
    result = Column(String, nullable=True)
    acc = Column(Float, nullable=True)
    device = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    profile = relationship("Profile", back_populates="calibrations")
    analyses = relationship("Analysis", back_populates="calibration")


# ---------------------------------------------------------------------------
# ANALYSIS + DETECTION + DETECTION_RATING + SCENE + COLOR_RESULT
# ---------------------------------------------------------------------------

class Analysis(Base):
    __tablename__ = "analyses"

    ana_id = Column(String, primary_key=True, default=gen_id)
    pro_id = Column(String, ForeignKey("profiles.pro_id"), nullable=False)
    cal_id = Column(String, ForeignKey("calibrations.cal_id"), nullable=True)
    acc_id = Column(String, ForeignKey("accessibility_profiles.acc_id"), nullable=True)
    ana_date = Column(DateTime, default=datetime.utcnow)
    img_url = Column(String, nullable=False)
    upl_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="processing")  # processing | done | error
    mode = Column(String, nullable=True)
    err_msg = Column(Text, nullable=True)
    result_overall = Column(Text, nullable=True)
    comp_time = Column(Float, nullable=True)
    det_count = Column(Integer, default=0)

    profile = relationship("Profile", back_populates="analyses")
    calibration = relationship("Calibration", back_populates="analyses")
    accessibility_profile = relationship("AccessibilityProfile", back_populates="analyses")
    detections = relationship("Detection", back_populates="analysis")
    scenes = relationship("Scene", back_populates="analysis")
    reports = relationship("Report", back_populates="analysis")
    transformations = relationship("ColorTransformation", back_populates="analysis")
    feedbacks = relationship("Feedback", back_populates="analysis")
    ocr_results = relationship("OcrResult", back_populates="analysis")
    saved_by = relationship("SavedAnalysis", back_populates="analysis")


class Detection(Base):
    __tablename__ = "detections"

    det_no = Column(String, primary_key=True, default=gen_id)
    ana_id = Column(String, ForeignKey("analyses.ana_id"), nullable=False)
    label = Column(String, nullable=False)
    bbox_x = Column(Float, nullable=False)
    bbox_y = Column(Float, nullable=False)
    bbox_w = Column(Float, nullable=False)
    bbox_h = Column(Float, nullable=False)
    conf = Column(Float, nullable=False)
    rgb = Column(String, nullable=True)
    color = Column(String, nullable=True)
    hex = Column(String, nullable=True)
    pos = Column(String, nullable=True)
    area = Column(Float, nullable=True)

    analysis = relationship("Analysis", back_populates="detections")
    ratings = relationship("DetectionRating", back_populates="detection")


class DetectionRating(Base):
    __tablename__ = "detection_ratings"

    dr_id = Column(String, primary_key=True, default=gen_id)
    det_no = Column(String, ForeignKey("detections.det_no"), nullable=False)
    pro_id = Column(String, ForeignKey("profiles.pro_id"), nullable=False)
    rating = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    dr_on = Column(DateTime, default=datetime.utcnow)

    detection = relationship("Detection", back_populates="ratings")


class Scene(Base):
    __tablename__ = "scenes"

    sce_id = Column(String, primary_key=True, default=gen_id)
    ana_id = Column(String, ForeignKey("analyses.ana_id"), nullable=False)
    type = Column(String, nullable=True)
    desc = Column(Text, nullable=True)
    text = Column(Text, nullable=True)
    audio_url = Column(String, nullable=True)
    gen_on = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("Analysis", back_populates="scenes")
    color_results = relationship("ColorResult", back_populates="scene")
    ocr_results = relationship("OcrResult", back_populates="scene")


class ColorResult(Base):
    __tablename__ = "color_results"

    cr_id = Column(String, primary_key=True, default=gen_id)
    sce_id = Column(String, ForeignKey("scenes.sce_id"), nullable=False)
    fb_id = Column(String, ForeignKey("feedbacks.fb_id"), nullable=True)
    suggested_color = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    contrast_ratio = Column(Float, nullable=True)
    applied_on = Column(DateTime, nullable=True)

    scene = relationship("Scene", back_populates="color_results")


# ---------------------------------------------------------------------------
# REPORT + COLOR_TRANSFORMATION + FEEDBACK + OCR_RESULT + SAVED_ANALYSIS
# ---------------------------------------------------------------------------

class Report(Base):
    __tablename__ = "reports"

    rpt_id = Column(String, primary_key=True, default=gen_id)
    ana_id = Column(String, ForeignKey("analyses.ana_id"), nullable=False)
    fmt = Column(String, nullable=False)  # PDF | CSV | JSON
    url = Column(String, nullable=True)
    type = Column(String, nullable=True)
    gen_on = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("Analysis", back_populates="reports")


class ColorTransformation(Base):
    __tablename__ = "color_transformations"

    trans_id = Column(String, primary_key=True, default=gen_id)
    ana_id = Column(String, ForeignKey("analyses.ana_id"), nullable=False)
    filter = Column(String, nullable=True)
    intensity = Column(Float, nullable=True)
    img_clr = Column(String, nullable=True)

    analysis = relationship("Analysis", back_populates="transformations")


class Feedback(Base):
    __tablename__ = "feedbacks"

    fb_id = Column(String, primary_key=True, default=gen_id)
    ana_id = Column(String, ForeignKey("analyses.ana_id"), nullable=False)
    det_no = Column(String, ForeignKey("detections.det_no"), nullable=True)
    new_label = Column(String, nullable=True)
    rating = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    fb_on = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("Analysis", back_populates="feedbacks")


class OcrResult(Base):
    __tablename__ = "ocr_results"

    ocr_id = Column(String, primary_key=True, default=gen_id)
    sce_id = Column(String, ForeignKey("scenes.sce_id"), nullable=True)
    ana_id = Column(String, ForeignKey("analyses.ana_id"), nullable=False)
    text = Column(Text, nullable=True)
    bbox_x = Column(Float, nullable=True)
    bbox_y = Column(Float, nullable=True)
    bbox_w = Column(Float, nullable=True)
    bbox_h = Column(Float, nullable=True)
    conf = Column(Float, nullable=True)
    lang = Column(String, default="en")

    scene = relationship("Scene", back_populates="ocr_results")
    analysis = relationship("Analysis", back_populates="ocr_results")


class SavedAnalysis(Base):
    __tablename__ = "saved_analyses"

    sav_id = Column(String, primary_key=True, default=gen_id)
    pro_id = Column(String, ForeignKey("profiles.pro_id"), nullable=False)
    ana_id = Column(String, ForeignKey("analyses.ana_id"), nullable=False)
    saved_on = Column(DateTime, default=datetime.utcnow)
    note = Column(Text, nullable=True)
    category = Column(String, nullable=True)

    analysis = relationship("Analysis", back_populates="saved_by")
