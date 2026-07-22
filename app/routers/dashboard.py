# ==========================================================
# app/routers/dashboard.py
# Part 1
# Dashboard APIs
# ==========================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models
from app import auth
from app.database import get_db
from app.utils import dashboard_summary

router = APIRouter()

# ==========================================================
# DASHBOARD SUMMARY
# ==========================================================

@router.get("/")
def dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):

    latest = db.query(models.VehicleCount).order_by(
        models.VehicleCount.detected_time.desc()
    ).first()

    if latest:

        data = dashboard_summary(

            latest.cars,

            latest.bikes,

            latest.buses,

            latest.trucks,

            latest.auto_rickshaw,

            latest.ambulance

        )

    else:

        data = dashboard_summary(

            0,

            0,

            0,

            0,

            0,

            0

        )

    return {

        "application": "AI Traffic Management & Congestion Detection",

        "logged_user": current_user.username,

        "role": current_user.role,

        "dashboard": data

    }


# ==========================================================
# TOTAL VEHICLES
# ==========================================================

@router.get("/vehicle-count")
def total_vehicle_count(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.officer_required)

):

    vehicles = db.query(models.VehicleCount).all()

    cars = sum(v.cars for v in vehicles)

    bikes = sum(v.bikes for v in vehicles)

    buses = sum(v.buses for v in vehicles)

    trucks = sum(v.trucks for v in vehicles)

    auto = sum(v.auto_rickshaw for v in vehicles)

    ambulance = sum(v.ambulance for v in vehicles)

    total = (

        cars +

        bikes +

        buses +

        trucks +

        auto +

        ambulance

    )

    return {

        "cars": cars,

        "bikes": bikes,

        "buses": buses,

        "trucks": trucks,

        "auto_rickshaw": auto,

        "ambulance": ambulance,

        "total": total

    }


# ==========================================================
# TOTAL USERS
# ==========================================================

@router.get("/users")
def users(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.admin_required)

):

    total = db.query(models.User).count()

    admins = db.query(models.User).filter(

        models.User.role == "Admin"

    ).count()

    supervisors = db.query(models.User).filter(

        models.User.role == "Supervisor"

    ).count()

    officers = db.query(models.User).filter(

        models.User.role == "Traffic Officer"

    ).count()

    return {

        "total_users": total,

        "admins": admins,

        "supervisors": supervisors,

        "traffic_officers": officers

    }


# ==========================================================
# TOTAL REPORTS
# ==========================================================

@router.get("/reports")
def reports(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.officer_required)

):

    total_reports = db.query(

        models.TrafficReport

    ).count()

    return {

        "total_reports": total_reports

    }


# ==========================================================
# TOTAL ALERTS
# ==========================================================

@router.get("/alerts")
def alerts(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.officer_required)

):

    total_alerts = db.query(

        models.Alert

    ).count()

    return {

        "total_alerts": total_alerts

    }
# ==========================================================
# WEEKLY VEHICLE STATISTICS
# ==========================================================

@router.get("/weekly")
def weekly_statistics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):

    records = db.query(models.VehicleCount).order_by(
        models.VehicleCount.detected_time.desc()
    ).limit(7).all()

    data = []

    for record in records:

        data.append({

            "date": record.detected_time.strftime("%d-%m-%Y"),

            "cars": record.cars,

            "bikes": record.bikes,

            "buses": record.buses,

            "trucks": record.trucks,

            "auto_rickshaw": record.auto_rickshaw,

            "ambulance": record.ambulance,

            "total": record.total

        })

    return data


# ==========================================================
# CONGESTION HISTORY
# ==========================================================

@router.get("/congestion-history")
def congestion_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):

    history = db.query(models.Congestion).order_by(
        models.Congestion.created_at.desc()
    ).limit(20).all()

    return history


# ==========================================================
# RECENT REPORTS
# ==========================================================

@router.get("/recent-reports")
def recent_reports(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):

    reports = db.query(models.TrafficReport).order_by(
        models.TrafficReport.generated_at.desc()
    ).limit(10).all()

    return reports


# ==========================================================
# RECENT VIDEOS
# ==========================================================

@router.get("/recent-videos")
def recent_videos(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):

    videos = db.query(models.UploadedVideo).order_by(
        models.UploadedVideo.upload_time.desc()
    ).limit(10).all()

    return videos


# ==========================================================
# TRAFFIC SIGNAL RECOMMENDATION
# ==========================================================

@router.get("/signal")
def signal_recommendation(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):

    latest = db.query(models.Congestion).order_by(
        models.Congestion.created_at.desc()
    ).first()

    if latest is None:

        return {

            "signal_time": 30,

            "recommendation": "No traffic data available."

        }

    return {

        "congestion_level": latest.congestion_level,

        "signal_time": latest.signal_time,

        "recommendation": latest.recommendation

    }


# ==========================================================
# CAMERA STATUS
# ==========================================================

@router.get("/camera")
def camera_status(

    current_user: models.User = Depends(auth.officer_required)

):

    return {

        "camera_status": "ONLINE",

        "fps": 30,

        "resolution": "1920x1080",

        "stream": "ACTIVE"

    }


# ==========================================================
# AI ENGINE STATUS
# ==========================================================

@router.get("/ai-engine")
def ai_engine(

    current_user: models.User = Depends(auth.officer_required)

):

    return {

        "model": "YOLOv8",

        "status": "RUNNING",

        "confidence": "0.50",

        "gpu": False

    }


# ==========================================================
# PIE CHART DATA
# ==========================================================

@router.get("/chart/pie")
def pie_chart(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.officer_required)

):

    vehicle = db.query(models.VehicleCount).order_by(

        models.VehicleCount.detected_time.desc()

    ).first()

    if vehicle is None:

        return {}

    return {

        "cars": vehicle.cars,

        "bikes": vehicle.bikes,

        "buses": vehicle.buses,

        "trucks": vehicle.trucks,

        "auto_rickshaw": vehicle.auto_rickshaw,

        "ambulance": vehicle.ambulance

    }


# ==========================================================
# BAR CHART
# ==========================================================

@router.get("/chart/bar")
def bar_chart(

    db: Session = Depends(get_db),

    current_user: models.User = Depends(auth.officer_required)

):

    records = db.query(models.VehicleCount).order_by(

        models.VehicleCount.detected_time.desc()

    ).limit(10).all()

    labels = []

    totals = []

    for row in reversed(records):

        labels.append(

            row.detected_time.strftime("%H:%M")

        )

        totals.append(

            row.total

        )

    return {

        "labels": labels,

        "values": totals

    }
    