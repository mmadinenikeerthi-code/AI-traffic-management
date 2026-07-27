from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# --- USER SCHEMAS ---

class UserRegister(BaseModel):
    fullname: str = Field(..., min_length=3, max_length=100)
    username: str = Field(..., min_length=4, max_length=50)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=8)
    confirm_password: str
    role: Optional[str] = "Traffic Officer"


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    fullname: str
    username: str
    email: str
    phone: Optional[str]
    role: str
    status: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    fullname: str = Field(..., min_length=3, max_length=100)
    username: str = Field(..., min_length=4, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: Optional[str] = "Traffic Officer"


class UserOut(UserResponse):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str


# --- VIDEO & DETECTION SCHEMAS ---

class VideoUploadResponse(BaseModel):
    id: int
    filename: str
    upload_time: datetime
    processed: bool

    class Config:
        from_attributes = True


class DetectionResult(BaseModel):
    vehicle_name: str
    confidence: float
    xmin: int
    ymin: int
    xmax: int
    ymax: int


class DetectionResponse(BaseModel):
    filename: str
    processing_time: float
    total_objects: int
    detections: List[DetectionResult]


class VehicleCountResponse(BaseModel):
    cars: int
    bikes: int
    buses: int
    trucks: int
    auto_rickshaw: int
    ambulance: int
    total: int
    frame_number: int
    detected_time: datetime

    class Config:
        from_attributes = True


# --- CONGESTION & AI SCHEMAS ---

class CongestionResponse(BaseModel):
    vehicle_count: int
    density: float
    congestion_level: str
    average_speed: float
    signal_time: int
    recommendation: str
    created_at: datetime

    class Config:
        from_attributes = True


class AIConfiguration(BaseModel):
    confidence_threshold: float = 0.50
    iou_threshold: float = 0.45
    save_video: bool = True
    save_report: bool = True


# --- ALERT & ACCIDENT SCHEMAS ---

class AlertCreate(BaseModel):
    location: str = "Junction A"
    alert_type: str
    severity: str
    message: str


class AccidentCreate(BaseModel):
    location: str = "Junction B"
    severity: str = "High"
    message: Optional[str] = "Accident reported via system endpoint"


class AlertResponse(BaseModel):
    id: int
    location: str
    alert_type: str
    severity: str
    message: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- TRAFFIC HISTORY SCHEMAS ---

class TrafficHistoryCreate(BaseModel):
    location: str = "Junction A"
    vehicle_count: int
    density: str
    signal_time: int


class TrafficHistoryResponse(BaseModel):
    id: int
    location: str
    vehicle_count: int
    density: str
    signal_time: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- REPORT & DASHBOARD SCHEMAS ---

class ReportResponse(BaseModel):
    id: int
    report_name: str
    total_vehicles: int
    cars: int
    bikes: int
    buses: int
    trucks: int
    auto_rickshaw: int
    ambulance: int
    congestion_level: str
    recommendation: str
    generated_at: datetime
    remarks: Optional[str] = None

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    total_users: int
    total_uploaded_videos: int
    total_processed_videos: int
    total_reports: int
    total_alerts: int
    total_vehicles: int
    congestion_level: str
    density: float
    average_speed: float
    signal_time: int


class LogResponse(BaseModel):
    username: str
    action: str
    ip_address: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str


class UpdateProfile(BaseModel):
    fullname: str
    email: EmailStr
    phone: Optional[str]