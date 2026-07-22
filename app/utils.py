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

def generate_filename(filename: str):

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

def generate_report_name():

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"Traffic_Report_{timestamp}"


# ==========================================================
# CONGESTION LEVEL
# ==========================================================

def congestion_level(total_vehicle):

    if total_vehicle <= config.LOW_TRAFFIC:

        return (
            "LOW",
            config.GREEN_SIGNAL_LOW,
            config.LOW_MESSAGE
        )

    elif total_vehicle <= config.MEDIUM_TRAFFIC:

        return (
            "MEDIUM",
            config.GREEN_SIGNAL_MEDIUM,
            config.MEDIUM_MESSAGE
        )

    elif total_vehicle <= config.HIGH_TRAFFIC:

        return (
            "HIGH",
            config.GREEN_SIGNAL_HIGH,
            config.HIGH_MESSAGE
        )

    else:

        return (
            "CRITICAL",
            config.GREEN_SIGNAL_CRITICAL,
            config.CRITICAL_MESSAGE
        )


# ==========================================================
# DENSITY
# ==========================================================

def density_percentage(total_vehicle):

    max_vehicle = 100

    density = (total_vehicle / max_vehicle) * 100

    if density > 100:

        density = 100

    return round(density, 2)


# ==========================================================
# AVERAGE SPEED
# ==========================================================

def average_speed(level):

    if level == "LOW":
        return 60

    elif level == "MEDIUM":
        return 40

    elif level == "HIGH":
        return 20

    return 10


# ==========================================================
# SIGNAL TIME
# ==========================================================

def signal_time(level):

    if level == "LOW":
        return config.GREEN_SIGNAL_LOW

    elif level == "MEDIUM":
        return config.GREEN_SIGNAL_MEDIUM

    elif level == "HIGH":
        return config.GREEN_SIGNAL_HIGH

    return config.GREEN_SIGNAL_CRITICAL


# ==========================================================
# AI RECOMMENDATION
# ==========================================================

def recommendation(level):

    if level == "LOW":

        return "Traffic flow is normal."

    elif level == "MEDIUM":

        return (
            "Increase monitoring and prepare "
            "traffic diversion if required."
        )

    elif level == "HIGH":

        return (
            "Extend green signal duration and "
            "deploy traffic officers."
        )

    return (
        "Critical congestion detected. "
        "Immediate diversion and emergency "
        "traffic management required."
    )


# ==========================================================
# VEHICLE SUMMARY
# ==========================================================

def total_vehicle_count(

        cars,

        bikes,

        buses,

        trucks,

        auto,

        ambulance):

    return (
        cars +
        bikes +
        buses +
        trucks +
        auto +
        ambulance
    )


# ==========================================================
# DASHBOARD DATA
# ==========================================================

def dashboard_summary(

        cars,

        bikes,

        buses,

        trucks,

        auto,

        ambulance):

    total = total_vehicle_count(

        cars,

        bikes,

        buses,

        trucks,

        auto,

        ambulance

    )

    level, signal, message = congestion_level(total)

    density = density_percentage(total)

    speed = average_speed(level)

    return {

        "cars": cars,

        "bikes": bikes,

        "buses": buses,

        "trucks": trucks,

        "auto_rickshaw": auto,

        "ambulance": ambulance,

        "total": total,

        "density": density,

        "congestion": level,

        "signal_time": signal,

        "average_speed": speed,

        "recommendation": recommendation(level),

        "message": message

    }


# ==========================================================
# LOGGER
# ==========================================================

def write_log(user, action):

    logger.info(

        f"{user} : {action}"

    )


# ==========================================================
# FORMAT DATE
# ==========================================================

def format_date():

    return datetime.now().strftime(

        "%d-%m-%Y %H:%M:%S"

    )


# ==========================================================
# SYSTEM STATUS
# ==========================================================

def system_status():

    return {

        "application": config.APP_NAME,

        "version": config.VERSION,

        "status": config.SYSTEM_STATUS,

        "camera": config.CAMERA_STATUS,

        "ai_engine": config.AI_ENGINE

    }