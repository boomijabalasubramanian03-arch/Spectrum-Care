from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator


# ---- Auth: Register -------------------------------------------------------

class RegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=1)
    middle_name: Optional[str] = None
    last_name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)  # bcrypt limit

    @field_validator("first_name", "last_name")
    @classmethod
    def _strip_required(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v

    @field_validator("middle_name")
    @classmethod
    def _strip_optional(cls, v):
        v = (v or "").strip()
        return v or None

    @field_validator("email")
    @classmethod
    def _lower_email(cls, v: str) -> str:
        return v.strip().lower()


class UserOut(BaseModel):
    user_id: str
    first_name: str
    middle_name: Optional[str]
    last_name: str
    email: EmailStr
    role: str
    created_on: datetime
    last_login: Optional[datetime]
    status: str

    class Config:
        from_attributes = True


# ---- Auth: Login ------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=200)

    @field_validator("email")
    @classmethod
    def _lower_email(cls, v: str) -> str:
        return v.strip().lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    session_id: str
    user: UserOut


# ---- Profile: patient details + accessibility -----------------------------

class ProfileUpdateIn(BaseModel):
    dob: Optional[datetime] = None
    gender: Optional[str] = Field(default=None, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=30)
    street: Optional[str] = Field(default=None, max_length=200)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    pincode: Optional[str] = Field(default=None, max_length=20)


class ProfileOut(BaseModel):
    pro_id: str
    dob: Optional[datetime]
    gender: Optional[str]
    phone: Optional[str]
    street: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    acc_mode: Optional[str]

    class Config:
        from_attributes = True


# ---- Analysis: Ingestion + Core AI Engine + Accessibility -----------------

class DetectionOut(BaseModel):
    det_no: str
    label: str
    conf: float
    bbox_x: float
    bbox_y: float
    bbox_w: float
    bbox_h: float
    rgb: Optional[str]
    color: Optional[str]
    hex: Optional[str]
    pos: Optional[str]
    area: Optional[float]

    class Config:
        from_attributes = True


class OcrResultOut(BaseModel):
    ocr_id: str
    text: Optional[str]
    bbox_x: Optional[float]
    bbox_y: Optional[float]
    bbox_w: Optional[float]
    bbox_h: Optional[float]
    conf: Optional[float]

    class Config:
        from_attributes = True


class SceneOut(BaseModel):
    sce_id: str
    desc: Optional[str]
    text: Optional[str]

    class Config:
        from_attributes = True


class CVDProfileIn(BaseModel):
    type: Literal["Protanopia", "Deuteranopia", "Tritanopia"]
    severity: Literal["mild", "moderate", "severe"] = "severe"


class CVDProfileOut(BaseModel):
    cvd_id: str
    type: str
    severity: Optional[str]

    class Config:
        from_attributes = True


class ColorResultOut(BaseModel):
    cr_id: str
    suggested_color: Optional[str]
    reason: Optional[str]
    contrast_ratio: Optional[float]

    class Config:
        from_attributes = True


class AnalysisOut(BaseModel):
    ana_id: str
    ana_date: datetime
    img_url: str
    status: str
    err_msg: Optional[str] = None
    comp_time: Optional[float]
    det_count: int
    detections: list[DetectionOut] = []
    scenes: list[SceneOut] = []
    ocr_results: list[OcrResultOut] = []
    annotated_url: Optional[str] = None
    cvd_type: Optional[str] = None
    cvd_url: Optional[str] = None
    color_results: list[ColorResultOut] = []

    class Config:
        from_attributes = True


class AnalysisSummaryOut(BaseModel):
    err_msg: Optional[str] = None
    ana_id: str
    ana_date: datetime
    img_url: str
    status: str
    det_count: int

    class Config:
        from_attributes = True


class StatsOut(BaseModel):
    total_analyses: int
    total_objects: int
    top_object: Optional[str] = None
    top_color: Optional[str] = None
    avg_processing_time: Optional[float] = None
    recent: list[AnalysisSummaryOut] = []
