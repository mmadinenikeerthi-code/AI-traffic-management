# ==========================================================
# app/config.py
# AI Traffic Management & Congestion Detection System
# ==========================================================

import os
from pathlib import Path

# ==========================================================
# PROJECT DIRECTORY
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

# ==========================================================
# APPLICATION
# ==========================================================

APP_NAME = "AI Traffic Management and Congestion Detection System"

VERSION = "1.0.0"

DEBUG = True


HOST = "127.0.0.1"

PORT = 8000

# ==========================================================
# DATABASE
# ==========================================================


# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
DATABASE_URL ="sqlite:///./traffic.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================================
# JWT AUTHENTICATION
# ==========================================================

SECRET_KEY = "ChangeThisToAVeryStrongSecretKey123456789"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ==========================================================
# USER ROLES
# ==========================================================

ADMIN = "Admin"

TRAFFIC_OFFICER = "Traffic Officer"

SUPERVISOR = "Supervisor"

# ==========================================================
# PASSWORD
# ==========================================================

PASSWORD_MIN_LENGTH = 8

# ==========================================================
# UPLOAD FOLDERS
# ==========================================================

UPLOAD_FOLDER = BASE_DIR / "uploads"

OUTPUT_FOLDER = BASE_DIR / "outputs"

REPORT_FOLDER = BASE_DIR / "reports"

MODEL_FOLDER = BASE_DIR / "ai"

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "ai" / "best.pt"

# create folders automatically
UPLOAD_FOLDER.mkdir(exist_ok=True)

OUTPUT_FOLDER.mkdir(exist_ok=True)

REPORT_FOLDER.mkdir(exist_ok=True)

# ==========================================================
# SUPPORTED FILES
# ==========================================================

ALLOWED_VIDEO_EXTENSIONS = [

    ".mp4",

    ".avi",

    ".mov",

    ".mkv"

]

MAX_VIDEO_SIZE = 1024 * 1024 * 500

# ==========================================================
# YOLO SETTINGS
# ==========================================================

CONFIDENCE_THRESHOLD = 0.50

IOU_THRESHOLD = 0.45

SAVE_DETECTION_VIDEO = True

SAVE_IMAGES = True

SHOW_LABELS = True

SHOW_CONFIDENCE = True

# ==========================================================
# VEHICLE CLASSES
# ==========================================================

VEHICLE_CLASSES = {

    0: "person",

    1: "bicycle",

    2: "car",

    3: "motorcycle",

    5: "bus",

    7: "truck"

}

# ==========================================================
# CONGESTION SETTINGS
# ==========================================================

LOW_TRAFFIC = 15

MEDIUM_TRAFFIC = 30

HIGH_TRAFFIC = 50

CRITICAL_TRAFFIC = 75

# ==========================================================
# TRAFFIC SIGNAL TIMING
# ==========================================================

GREEN_SIGNAL_LOW = 30

GREEN_SIGNAL_MEDIUM = 45

GREEN_SIGNAL_HIGH = 60

GREEN_SIGNAL_CRITICAL = 90

# ==========================================================
# DASHBOARD SETTINGS
# ==========================================================

REFRESH_RATE = 5

MAX_RECENT_REPORTS = 20

MAX_ALERTS = 20

# ==========================================================
# REPORT SETTINGS
# ==========================================================

GENERATE_PDF = True

GENERATE_EXCEL = True

SAVE_REPORT_TO_DATABASE = True

# ==========================================================
# EMAIL (Future Extension)
# ==========================================================

EMAIL_ENABLED = False

SMTP_SERVER = ""

SMTP_PORT = 587

EMAIL_USERNAME = ""

EMAIL_PASSWORD = ""

# ==========================================================
# LOGGING
# ==========================================================

LOG_FOLDER = BASE_DIR / "logs"

LOG_FOLDER.mkdir(exist_ok=True)

LOG_FILE = LOG_FOLDER / "traffic_system.log"

# ==========================================================
# ALERT MESSAGES
# ==========================================================

LOW_MESSAGE = "Traffic Flow Normal"

MEDIUM_MESSAGE = "Moderate Traffic"

HIGH_MESSAGE = "Heavy Traffic Detected"

CRITICAL_MESSAGE = "Critical Congestion - Immediate Action Required"

# ==========================================================
# SYSTEM STATUS
# ==========================================================

SYSTEM_STATUS = "ONLINE"

CAMERA_STATUS = "CONNECTED"

AI_ENGINE = "YOLOv8"

# ==========================================================
# COLORS FOR DASHBOARD
# ==========================================================

SUCCESS_COLOR = "#28a745"

WARNING_COLOR = "#ffc107"

DANGER_COLOR = "#dc3545"

PRIMARY_COLOR = "#0d6efd"
# ==========================================================
# RTSP CAMERA SETTINGS
# ==========================================================

RTSP_URL = "rtsp://username:password@camera-ip:554/stream"