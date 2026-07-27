# ==========================================================
# app/routers/analytics.py
# Traffic Heatmap Data, Analytics, Trends & Status
# ==========================================================

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import auth, models
from app.models import Alert
from app.database import get_db

# ==========================================================
# SAFE CONGESTION CALCULATOR (NO IMPORT ERROR)
# ==========================================================

def calculate_congestion(vehicle_count: int, emergency_count: int = 0) -> dict:
    """
    Calculates congestion level, recommended green signal timing,
    and automated system recommendations based on live metrics.
    """
    if vehicle_count < 20:
        density = "Low"
        signal_time = 30
        recommendation = "Traffic speed is normal. Standard signal cycle active."
    elif vehicle_count < 40:
        density = "Medium"
        signal_time = 60
        recommendation = "Moderate congestion detected. Extending signal timing by 30 seconds."
    else:
        density = "High"
        signal_time = 90
        recommendation = "High density! Recommended action: Extend green signal timing, notify nearby officers, and open alternate bypass route."

    if emergency_count > 0:
        recommendation = f"EMERGENCY PROTOCOL ACTIVE: {emergency_count} emergency vehicle(s) detected. Overriding signal timing to immediate GREEN priority."
        signal_time += 30

    return {
        "vehicle_count": vehicle_count,
        "emergency_count": emergency_count,
        "density": density,
        "signal_time": signal_time,
        "recommendation": recommendation
    }


router = APIRouter(prefix="/analytics", tags=["Analytics & Heatmap"])


# ==========================================================
# TRAFFIC STATUS & RECOMMENDATION ENGINE
# ==========================================================

@router.get("/traffic-status")
def get_traffic_status(vehicle_count: int = 25, emergency_count: int = 0):
    """
    Returns congestion status, signal timing, and AI recommendations
    based on vehicle and emergency vehicle counts.
    """
    return calculate_congestion(vehicle_count, emergency_count)


# ==========================================================
# LEAFLET HEATMAP DATA
# ==========================================================

@router.get("/heatmap-data")
def heatmap_points(
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(auth.officer_required)
):
    """
    Returns lat, lng, and intensity weights for Leaflet heatmap integration.
    Queries recent TrafficLog entries and falls back to default coordinates if empty.
    """
    logs = []
    if hasattr(models, 'TrafficLog'):
        logs = (
            db.query(models.TrafficLog)
            .order_by(models.TrafficLog.timestamp.desc())
            .limit(100)
            .all()
        )

    if not logs:
        # Static sample heatmap coordinates if logs table is empty
        return [
            [12.9716, 77.5946, 0.85],  # Signal A
            [12.9750, 77.5990, 0.40],  # Signal B
            [12.9680, 77.5890, 0.20],  # Signal C
            [12.9800, 77.6050, 0.95]   # Signal D
        ]

    points = []
    for log in logs:
        density = getattr(log, 'density_status', 'Low')
        intensity = 0.3 if density == "Low" else (0.6 if density == "Medium" else 1.0)
        points.append([log.lat, log.lng, intensity])
    return points


# ==========================================================
# KEY PERFORMANCE INDICATORS (KPIS)
# ==========================================================

@router.get("/kpis")
def get_kpis(
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(auth.officer_required)
):
    """
    Key performance metrics for dashboard top cards.
    Calculates total vehicles detected today, active alerts, total accidents, and current density.
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. Total vehicles query
    total_vehicles = 0
    if hasattr(models, 'TrafficLog'):
        total_vehicles = db.query(func.sum(models.TrafficLog.vehicle_count)).scalar() or 0
    elif hasattr(models, 'TrafficHistory'):
        total_vehicles = db.query(func.sum(models.TrafficHistory.vehicle_count)).filter(
            models.TrafficHistory.created_at >= today_start
        ).scalar() or 0

    # 2. Active alerts count
    active_alerts = (
        db.query(func.count(Alert.id))
        .filter(Alert.status == "Active")
        .scalar()
    ) or 0

    # 3. Total accident counts
    total_accidents = 0
    if hasattr(models, 'TrafficLog'):
        total_accidents = (
            db.query(func.count(models.TrafficLog.id))
            .filter(models.TrafficLog.has_accident == True)
            .scalar()
        ) or 0
    
    if total_accidents == 0:
        total_accidents = (
            db.query(func.count(Alert.id))
            .filter(Alert.alert_type == "Accident")
            .scalar()
        ) or 0

    # 4. Current traffic density
    current_density = "Low"
    if hasattr(models, 'TrafficLog'):
        latest_log = db.query(models.TrafficLog).order_by(models.TrafficLog.timestamp.desc()).first()
        if latest_log and getattr(latest_log, 'density_status', None):
            current_density = latest_log.density_status
    elif hasattr(models, 'TrafficHistory'):
        latest_history = db.query(models.TrafficHistory).order_by(models.TrafficHistory.created_at.desc()).first()
        if latest_history and getattr(latest_history, 'density', None):
            current_density = latest_history.density

    return {
        "total_vehicles_detected": total_vehicles,
        "active_alerts": active_alerts,
        "total_accidents": total_accidents,
        "current_density": current_density
    }


# ==========================================================
# TRAFFIC TRENDS
# ==========================================================

@router.get("/trends")
def get_traffic_trends(
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(auth.officer_required)
):
    """
    Weekly traffic detection trends grouped by date.
    """
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    if hasattr(models, 'TrafficLog'):
        records = (
            db.query(
                func.date(models.TrafficLog.timestamp).label("date"),
                func.sum(models.TrafficLog.vehicle_count).label("total_vehicles"),
                func.count(models.TrafficLog.id).label("total_logs")
            )
            .filter(models.TrafficLog.timestamp >= seven_days_ago)
            .group_by(func.date(models.TrafficLog.timestamp))
            .all()
        )
        return [{"date": str(r.date), "vehicles": r.total_vehicles, "logs": r.total_logs} for r in records]

    return []