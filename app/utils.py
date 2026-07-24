# ==========================================================
# app/utils.py
# AI Traffic Management & Congestion Detection System
# ==========================================================

import os
import uuid
import shutil
import logging
from datetime import datetime
from pathlib import Path

from app import config

# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    filename=config.LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# ==========================================================
# FILE VALIDATION
# ==========================================================

def allowed_video(filename: str) -> bool:
    extension = Path(filename).suffix.lower()
    return extension in config.ALLOWED_VIDEO_EXTENSIONS


# ==========================================================
# UNIQUE FILE NAME
# ==========================================================

def generate_filename(filename: str) -> str:
    extension = Path(filename).suffix
    unique_name = f"{uuid.uuid4().hex}{extension}"
    return unique_name


# ==========================================================
# SAVE VIDEO
# ==========================================================

def save_uploaded_video(file):
    filename = generate_filename(file.filename)
    filepath = config.UPLOAD_FOLDER / filename

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return filename, str(filepath)


# ==========================================================
# CURRENT DATE
# ==========================================================

def current_datetime():
    return datetime.now()


# ==========================================================
# REPORT NAME
# ==========================================================

def generate_report_name() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"Traffic_Report_{timestamp}"


# ==========================================================
# CONGESTION LEVEL & AI METRICS
# ==========================================================

def get_congestion_metrics(total_vehicle: int, ambulance_count: int = 0) -> dict:
    has_emergency = ambulance_count > 0

    if total_vehicle <= getattr(config, 'LOW_TRAFFIC', 15):
        level = "LOW"
        signal = getattr(config, 'GREEN_SIGNAL_LOW', 30)
        message = getattr(config, 'LOW_MESSAGE', "Normal traffic conditions.")
        speed = 60
        advice = "Traffic flow is normal."
        suggested_route = "Main Highway"
        estimated_delay = 0

    elif total_vehicle <= getattr(config, 'MEDIUM_TRAFFIC', 30):
        level = "MEDIUM"
        signal = getattr(config, 'GREEN_SIGNAL_MEDIUM', 60)
        message = getattr(config, 'MEDIUM_MESSAGE', "Moderate traffic flow detected.")
        speed = 40
        advice = "Increase monitoring and prepare traffic diversion if required."
        suggested_route = "Main Highway (Slow Traffic)"
        estimated_delay = 5

    elif total_vehicle <= getattr(config, 'HIGH_TRAFFIC', 50):
        level = "HIGH"
        signal = getattr(config, 'GREEN_SIGNAL_HIGH', 90)
        message = getattr(config, 'HIGH_MESSAGE', "Heavy traffic detected.")
        speed = 20
        advice = "Extend green signal duration and deploy traffic officers."
        suggested_route = "Alternate Route A"
        estimated_delay = 15

    else:
        level = "CRITICAL"
        signal = getattr(config, 'GREEN_SIGNAL_CRITICAL', 120)
        message = getattr(config, 'CRITICAL_MESSAGE', "Critical congestion detected.")
        speed = 10
        advice = "Critical congestion detected. Immediate diversion required."
        suggested_route = "Alternate Route B (Ring Road)"
        estimated_delay = 30

    if has_emergency:
        signal = max(signal, 90)
        advice = "🚨 EMERGENCY PRIORITY: Emergency Vehicle Detected! Clearing Route..."
        message = "Emergency vehicle detected. Green signal extended."

    max_capacity = 100
    density = round(min(100.0, (total_vehicle / max_capacity) * 100), 2)

    return {
        "congestion_level": level,
        "signal_time": signal,
        "density": density,
        "average_speed": speed,
        "message": message,
        "recommendation": advice,
        "suggested_route": suggested_route,
        "estimated_delay": estimated_delay,
        "has_emergency": has_emergency
    }


def congestion_level(total_vehicle: int):
    metrics = get_congestion_metrics(total_vehicle)
    return (
        metrics["congestion_level"],
        metrics["signal_time"],
        metrics["message"]
    )


def density_percentage(total_vehicle: int) -> float:
    max_vehicle = 100
    density = (total_vehicle / max_vehicle) * 100
    return round(min(100.0, density), 2)


def average_speed(level: str) -> int:
    speeds = {
        "LOW": 60,
        "MEDIUM": 40,
        "HIGH": 20,
        "CRITICAL": 10
    }
    return speeds.get(level, 30)


def signal_time(level: str) -> int:
    timings = {
        "LOW": getattr(config, 'GREEN_SIGNAL_LOW', 30),
        "MEDIUM": getattr(config, 'GREEN_SIGNAL_MEDIUM', 60),
        "HIGH": getattr(config, 'GREEN_SIGNAL_HIGH', 90),
        "CRITICAL": getattr(config, 'GREEN_SIGNAL_CRITICAL', 120)
    }
    return timings.get(level, 30)


def recommendation(level: str) -> str:
    metrics = get_congestion_metrics(
        total_vehicle=5 if level == "LOW" else 20 if level == "MEDIUM" else 40 if level == "HIGH" else 60
    )
    return metrics["recommendation"]


# ==========================================================
# VEHICLE SUMMARY
# ==========================================================

def total_vehicle_count(cars, bikes, buses, trucks, auto, ambulance) -> int:
    return cars + bikes + buses + trucks + auto + ambulance


# ==========================================================
# DASHBOARD DATA
# ==========================================================

def dashboard_summary(cars, bikes, buses, trucks, auto, ambulance) -> dict:
    total = total_vehicle_count(cars, bikes, buses, trucks, auto, ambulance)
    metrics = get_congestion_metrics(total, ambulance_count=ambulance)

    return {
        "cars": cars,
        "bikes": bikes,
        "buses": buses,
        "trucks": trucks,
        "auto_rickshaw": auto,
        "ambulance": ambulance,
        "total": total,
        "density": metrics["density"],
        "congestion": metrics["congestion_level"],
        "signal_time": metrics["signal_time"],
        "average_speed": metrics["average_speed"],
        "recommendation": metrics["recommendation"],
        "message": metrics["message"],
        "suggested_route": metrics["suggested_route"],
        "estimated_delay": metrics["estimated_delay"],
        "has_emergency": metrics["has_emergency"]
    }


# ==========================================================
# LOGGER
# ==========================================================

def write_log(user: str, action: str):
    logger.info(f"{user} : {action}")


# ==========================================================
# FORMAT DATE
# ==========================================================

def format_date() -> str:
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")


# ==========================================================
# SYSTEM STATUS
# ==========================================================

def system_status() -> dict:
    return {
        "application": config.APP_NAME,
        "version": config.VERSION,
        "status": config.SYSTEM_STATUS,
        "camera": config.CAMERA_STATUS,
        "ai_engine": config.AI_ENGINE
    }