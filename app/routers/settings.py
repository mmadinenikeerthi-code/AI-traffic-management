# ==========================================================
# app/routers/settings.py
# APPLICATION SETTINGS
# ==========================================================

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app import auth, models


router = APIRouter()


# ==========================================================
# SETTINGS STORAGE
# ==========================================================

APP_SETTINGS = {
    "project": "AI Traffic Management & Congestion Detection System",
    "version": "1.0.0",

    "theme": "Dark",
    "language": "English",

    "map_provider": "OpenStreetMap",

    "traffic_refresh": 5,

    "heatmap_enabled": True,
    "markers_enabled": True,

    "notifications": True,
    "email_alerts": False,
    "sms_alerts": False,

    "ai_prediction": True,
    "live_detection": True,
    "analytics": True,
    "gps_tracking": True,
    "weather_overlay": True,

    "system_status": "Running"
}


# ==========================================================
# PYDANTIC MODELS
# ==========================================================

class SettingsUpdate(BaseModel):

    theme: Optional[str] = None
    language: Optional[str] = None
    map_provider: Optional[str] = None

    traffic_refresh: Optional[int] = None

    heatmap_enabled: Optional[bool] = None
    markers_enabled: Optional[bool] = None

    notifications: Optional[bool] = None
    email_alerts: Optional[bool] = None
    sms_alerts: Optional[bool] = None

    ai_prediction: Optional[bool] = None
    live_detection: Optional[bool] = None
    analytics: Optional[bool] = None
    gps_tracking: Optional[bool] = None
    weather_overlay: Optional[bool] = None


class NotificationUpdate(BaseModel):

    notifications: Optional[bool] = None
    email_alerts: Optional[bool] = None
    sms_alerts: Optional[bool] = None


class AppearanceUpdate(BaseModel):

    theme: Optional[str] = None
    language: Optional[str] = None


# ==========================================================
# GET ALL SETTINGS
# GET /settings/settings/
# ==========================================================

@router.get("/settings/")
def get_settings(
    current_user: models.User = Depends(auth.get_current_user)
):
    return APP_SETTINGS


# ==========================================================
# UPDATE SETTINGS
# PUT /settings/settings/
# ==========================================================

@router.put("/settings/")
def update_settings(
    settings: SettingsUpdate,
    current_user: models.User = Depends(auth.get_current_user)
):

    update_data = settings.model_dump(
        exclude_unset=True
    )

    APP_SETTINGS.update(update_data)

    return {
        "message": "Settings updated successfully.",
        "settings": APP_SETTINGS
    }


# ==========================================================
# SYSTEM INFORMATION
# GET /settings/settings/system
# ==========================================================

@router.get("/settings/system")
def system_information(
    current_user: models.User = Depends(auth.get_current_user)
):

    return {
        "project": APP_SETTINGS["project"],
        "version": APP_SETTINGS["version"],
        "system_status": APP_SETTINGS["system_status"],
        "ai_engine": "YOLOv8",
        "map_provider": APP_SETTINGS["map_provider"],
        "live_detection": APP_SETTINGS["live_detection"],
        "analytics": APP_SETTINGS["analytics"],
        "gps_tracking": APP_SETTINGS["gps_tracking"]
    }


# ==========================================================
# NOTIFICATION SETTINGS
# GET /settings/settings/notifications
# ==========================================================

@router.get("/settings/notifications")
def get_notifications(
    current_user: models.User = Depends(auth.get_current_user)
):

    return {
        "notifications": APP_SETTINGS["notifications"],
        "email_alerts": APP_SETTINGS["email_alerts"],
        "sms_alerts": APP_SETTINGS["sms_alerts"]
    }


# ==========================================================
# UPDATE NOTIFICATION SETTINGS
# PUT /settings/settings/notifications
# ==========================================================

@router.put("/settings/notifications")
def update_notifications(
    settings: NotificationUpdate,
    current_user: models.User = Depends(auth.get_current_user)
):

    update_data = settings.model_dump(
        exclude_unset=True
    )

    APP_SETTINGS.update(update_data)

    return {
        "message": "Notification settings updated successfully.",
        "notifications": {
            "notifications": APP_SETTINGS["notifications"],
            "email_alerts": APP_SETTINGS["email_alerts"],
            "sms_alerts": APP_SETTINGS["sms_alerts"]
        }
    }


# ==========================================================
# APPEARANCE
# GET /settings/settings/appearance
# ==========================================================

@router.get("/settings/appearance")
def get_appearance(
    current_user: models.User = Depends(auth.get_current_user)
):

    return {
        "theme": APP_SETTINGS["theme"],
        "language": APP_SETTINGS["language"]
    }


# ==========================================================
# UPDATE APPEARANCE
# PUT /settings/settings/appearance
# ==========================================================

@router.put("/settings/appearance")
def update_appearance(
    settings: AppearanceUpdate,
    current_user: models.User = Depends(auth.get_current_user)
):

    update_data = settings.model_dump(
        exclude_unset=True
    )

    APP_SETTINGS.update(update_data)

    return {
        "message": "Appearance updated successfully.",
        "appearance": {
            "theme": APP_SETTINGS["theme"],
            "language": APP_SETTINGS["language"]
        }
    }


# ==========================================================
# ABOUT
# GET /settings/settings/about
# ==========================================================

@router.get("/settings/about")
def about(
    current_user: models.User = Depends(auth.get_current_user)
):

    return {
        "project": APP_SETTINGS["project"],
        "version": APP_SETTINGS["version"],
        "description": (
            "AI based traffic management and "
            "congestion detection system."
        ),
        "map_provider": APP_SETTINGS["map_provider"],
        "ai_engine": "YOLOv8",
        "status": APP_SETTINGS["system_status"]
    }