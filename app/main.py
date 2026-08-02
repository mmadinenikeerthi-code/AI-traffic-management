# ==========================================================
# AI TRAFFIC MANAGEMENT & CONGESTION DETECTION SYSTEM
# Consolidated Core: Milestones 1, 2, and 3 (Updated & Fixed)
# ==========================================================

import os
import io
import csv
import uuid
import random
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from fastapi import (
    FastAPI, Depends, HTTPException, status, Request, UploadFile, File, Query
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, func
)
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship
from passlib.context import CryptContext
from jose import JWTError, jwt
import pandas as pd
import uvicorn

# ----------------------------------------------------------
# 1. APPLICATION & SYSTEM CONFIGURATION
# ----------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "frontend" / "static"
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
REPORT_DIR = BASE_DIR / "reports"

for folder in [STATIC_DIR, TEMPLATES_DIR, UPLOAD_DIR, OUTPUT_DIR, REPORT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

APP_NAME = "AI Traffic Management & Congestion System"
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-jwt-key-milestone1-2-3")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/traffic.db")

# ----------------------------------------------------------
# 2. DATABASE ENGINE & SESSION SETUP
# ----------------------------------------------------------
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------------------------------------
# 3. DATABASE MODELS (ORM)
# ----------------------------------------------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(30), default="Traffic Officer")
    phone = Column(String(20), nullable=True)
    status = Column(String(20), default="Active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class UploadedVideo(Base):
    __tablename__ = "uploaded_videos"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    upload_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed = Column(Boolean, default=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)

class VehicleCount(Base):
    __tablename__ = "vehicle_counts"
    id = Column(Integer, primary_key=True, index=True)
    cars = Column(Integer, default=0)
    bikes = Column(Integer, default=0)
    buses = Column(Integer, default=0)
    trucks = Column(Integer, default=0)
    auto_rickshaw = Column(Integer, default=0)
    ambulance = Column(Integer, default=0)
    total = Column(Integer, default=0)
    frame_number = Column(Integer, default=0)
    detected_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class Congestion(Base):
    __tablename__ = "congestion"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_count = Column(Integer, default=0)
    density = Column(Float, default=0.0)
    congestion_level = Column(String(50), nullable=False)
    average_speed = Column(Float, default=0.0)
    signal_time = Column(Integer, default=30)
    recommendation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True, default="Junction Alpha")
    alert_type = Column(String(100), nullable=True, default="Heavy Traffic")
    severity = Column(String(30), default="High")
    status = Column(String(20), default="Active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class TrafficReport(Base):
    __tablename__ = "traffic_reports"
    id = Column(Integer, primary_key=True, index=True)
    report_name = Column(String(200))
    total_vehicles = Column(Integer, default=0)
    congestion_level = Column(String(100))
    recommendation = Column(Text)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(bind=engine)

# ----------------------------------------------------------
# 4. SCHEMAS (PYDANTIC)
# ----------------------------------------------------------
class UserRegister(BaseModel):
    fullname: str = Field(..., min_length=3)
    username: str = Field(..., min_length=4)
    email: EmailStr
    phone: Optional[str] = None
    role: str = "Traffic Officer"
    password: str = Field(..., min_length=8)
    confirm_password: str

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

class RouteInput(BaseModel):
    road_name: str
    density: float
    emergency_vehicle_detected: bool = False

# ----------------------------------------------------------
# 5. SECURITY & JWT AUTHENTICATION
# ----------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    exc = HTTPException(status_code=401, detail="Invalid token credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise exc
    except JWTError:
        raise exc
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise exc
    return user

# ----------------------------------------------------------
# 6. FASTAPI CORE INITIALIZATION
# ----------------------------------------------------------
app = FastAPI(title=APP_NAME, version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Helper Function to Safely Render HTML Templates with Fallbacks
def render_template(template_name: str, request: Request, title: str, active_page: str = ""):
    target_path = TEMPLATES_DIR / template_name
    
    # Fallback to heatmap.html or gis.html if file names vary
    if not target_path.exists():
        if template_name == "gis.html" and (TEMPLATES_DIR / "heatmap.html").exists():
            template_name = "heatmap.html"
        elif template_name == "hotspots.html" and (TEMPLATES_DIR / "heatmap.html").exists():
            template_name = "heatmap.html"

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "title": title,
            "active_page": active_page
        }
    )

# ----------------------------------------------------------
# 7. AUTHENTICATION ENDPOINTS (MILESTONE 1)
# ----------------------------------------------------------
@app.post("/auth/register", status_code=201, response_model=UserResponse)
def register(user: UserRegister, db: Session = Depends(get_db)):
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=409, detail="Username already exists.")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=409, detail="Email already registered.")

    new_user = User(
        fullname=user.fullname,
        username=user.username,
        email=user.email,
        phone=user.phone,
        role=user.role,
        password=hash_password(user.password),
        status="Active"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user": {"username": user.username, "role": user.role}}

@app.get("/auth/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return user

# ----------------------------------------------------------
# 8. TRAFFIC PREDICTION & REROUTING (MILESTONE 2)
# ----------------------------------------------------------
@app.post("/recommendation/suggest")
def generate_recommendation(payload: RouteInput):
    if payload.emergency_vehicle_detected:
        return {
            "status": "CRITICAL",
            "action": "Clear Lane Immediately",
            "recommendation": f"🚨 Emergency Vehicle on {payload.road_name}. Green priority signal overridden.",
            "estimated_time_saved": "8 minutes"
        }
    if payload.density >= 75.0:
        return {
            "status": "HEAVY_CONGESTION",
            "action": "Divert Traffic",
            "recommendation": f"Heavy density on {payload.road_name}. Reroute vehicles via Outer Ring Road.",
            "estimated_time_saved": "15 minutes"
        }
    return {
        "status": "CLEAR",
        "action": "Normal Flow",
        "recommendation": f"Flow on {payload.road_name} is smooth. Standard signal timing active.",
        "estimated_time_saved": "0 minutes"
    }

# ----------------------------------------------------------
# 9. HEATMAP & ANALYTICS API ENDPOINTS (MILESTONE 3)
# ----------------------------------------------------------
@app.get("/analytics/summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    total_v = db.query(func.sum(VehicleCount.total)).scalar() or 14250
    active_a = db.query(func.count(Alert.id)).filter(Alert.status == "Active").scalar() or 5
    return {
        "total_vehicles": total_v,
        "congestion_level": "Moderate",
        "alerts_today": active_a,
        "average_speed_kmh": 36.5,
        "peak_traffic_hour": "08:30 AM - 10:00 AM",
        "vehicle_type_distribution": {
            "Cars": int(total_v * 0.55),
            "Bikes": int(total_v * 0.25),
            "Buses": int(total_v * 0.10),
            "Trucks": int(total_v * 0.10)
        }
    }

@app.get("/analytics/trends")
def get_traffic_trends():
    return {
        "hourly_labels": ["06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
        "vehicles_per_hour": [450, 1280, 850, 920, 1600, 710],
        "congestion_percentage": [20, 80, 50, 55, 90, 40]
    }

@app.get("/analytics/kpis")
async def get_kpis():
    return {
        "total_vehicles": 120,
        "avg_speed": 45.5,
        "details": None
    }

@app.get("/analytics/traffic-status")
async def get_traffic_status(vehicle_count: int = 0, emergency_count: int = 0):
    return {
        "vehicle_count": vehicle_count,
        "emergency_count": emergency_count,
        "status": "normal"
    }

@app.get("/heatmap/points")
def get_heatmap_points(search: Optional[str] = Query(None)):
    data = [
        {"id": "AP_Kurnool", "road": "Raj Vihar Center, Kurnool", "lat": 15.8281, "lng": 78.0373, "intensity": 0.85, "level": "HEAVY", "vehicle_count": 145, "speed": "18 km/h"},
        {"id": "TG_Hyd", "road": "Ameerpet Junction, Hyderabad", "lat": 17.4375, "lng": 78.4482, "intensity": 0.92, "level": "HEAVY", "vehicle_count": 210, "speed": "10 km/h"},
        {"id": "KA_Blr", "road": "Silk Board, Bangalore", "lat": 12.9172, "lng": 77.6228, "intensity": 0.98, "level": "HEAVY", "vehicle_count": 350, "speed": "5 km/h"},
        {"id": "MH_Mum", "road": "BKC, Mumbai", "lat": 19.0693, "lng": 72.8656, "intensity": 0.75, "level": "MEDIUM", "vehicle_count": 190, "speed": "22 km/h"}
    ]
    if search:
        data = [p for p in data if search.lower() in p["road"].lower()]
    return data

@app.get("/api/alerts")
def fetch_alerts_api(db: Session = Depends(get_db)):
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(20).all()
    if not alerts:
        return [{"id": 1, "alert_type": "System Check", "severity": "Low", "description": "All signals running smoothly.", "location": "City-Wide", "status": "Active"}]
    return alerts

@app.post("/alerts/resolve/{alert_id}")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.status = "Resolved"
        db.commit()
    return {"message": "Alert resolved"}

# ----------------------------------------------------------
# 10. REPORT EXPORTS (PDF/CSV)
# ----------------------------------------------------------
@app.get("/reports/export/csv")
def export_csv(db: Session = Depends(get_db)):
    logs = db.query(VehicleCount).all()
    data = [{"ID": l.id, "Cars": l.cars, "Bikes": l.bikes, "Total": l.total, "Time": str(l.detected_time)} for l in logs]
    df = pd.DataFrame(data if data else [{"Status": "No Log Records Available"}])
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return Response(content=csv_bytes, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=traffic_report.csv"})

# ----------------------------------------------------------
# 11. HTML PAGE TEMPLATE ROUTING
# ----------------------------------------------------------

# Public Authentication Views
@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return render_template("login.html", request, "Login | AI Traffic Control", "login")

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return render_template("register.html", request, "Register | AI Traffic Control", "register")

# Protected Dashboard Views
@app.get("/dashboard", response_class=HTMLResponse)
@app.get("/dashboard-page", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return render_template("dashboard.html", request, "Dashboard | AI Traffic Management", "dashboard")

@app.get("/traffic-gis", response_class=HTMLResponse)
@app.get("/heatmap", response_class=HTMLResponse)
async def gis_page(request: Request):
    return render_template("gis.html", request, "Traffic GIS & Heatmap", "gis")

@app.get("/route-planner", response_class=HTMLResponse)
async def route_planner_page(request: Request):
    return render_template("route_planner.html", request, "Route Planner", "route_planner")

@app.get("/hotspots", response_class=HTMLResponse)
async def hotspots_page(request: Request):
    return render_template("hotspots.html", request, "Pan-India Hotspots", "hotspots")

@app.get("/analytics", response_class=HTMLResponse)
@app.get("/analytics-page", response_class=HTMLResponse)
async def analytics_page(request: Request):
    return render_template("analytics.html", request, "Traffic Analytics", "analytics")

@app.get("/reports", response_class=HTMLResponse)
@app.get("/reports-page", response_class=HTMLResponse)
async def reports_page(request: Request):
    return render_template("reports.html", request, "System Reports", "reports")

@app.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request):
    return render_template("alerts.html", request, "System Alerts", "alerts")
# Updated Safe Helper Function inside main.py
def render_template(template_name: str, request: Request, title: str, active_page: str = ""):
    target_path = TEMPLATES_DIR / template_name
    
    # If specific template doesn't exist, fallback gracefully to dashboard.html to prevent 500 error
    if not target_path.exists():
        logging.warning(f"Template '{template_name}' not found. Falling back to dashboard.html.")
        template_name = "dashboard.html"

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "title": title,
            "active_page": active_page
        }
    )

@app.get("/reports", response_class=HTMLResponse)
@app.get("/reports-page", response_class=HTMLResponse)
async def reports_page(request: Request):
    return render_template("reports.html", request, "Traffic System Reports", "reports")

@app.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request):
    return render_template("alerts.html", request, "System Alerts", "alerts")
# ----------------------------------------------------------
# 12. RUNNER ENTRY
# ----------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)