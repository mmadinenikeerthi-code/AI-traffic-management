# ==========================================================
# app/routers/analytics.py
# Traffic Heatmap Data, Analytics, Trends & Status
# ==========================================================

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import auth, models
from app.models import Alert
from app.database import get_db

# ==========================================================
# ROUTER SETUP
# ==========================================================

router = APIRouter(prefix="/analytics", tags=["Analytics & Heatmap"])


# ==========================================================
# SAFE CONGESTION CALCULATOR
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
        points.append([getattr(log, 'lat', 12.9716), getattr(log, 'lng', 77.5946), intensity])
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
# DASHBOARD SUMMARY KPI ENDPOINT
# ==========================================================

@router.get("/summary")
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(auth.officer_required)
):
    """
    Aggregates KPI metrics and vehicle type distribution for UI rendering.
    Combines live DB values with standard calculations.
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    total_vehicles = 0
    if hasattr(models, 'TrafficLog'):
        total_vehicles = db.query(func.sum(models.TrafficLog.vehicle_count)).scalar() or 0
    elif hasattr(models, 'TrafficHistory'):
        total_vehicles = db.query(func.sum(models.TrafficHistory.vehicle_count)).filter(
            models.TrafficHistory.created_at >= today_start
        ).scalar() or 0

    alerts_today = (
        db.query(func.count(Alert.id))
        .filter(Alert.timestamp >= today_start if hasattr(Alert, 'timestamp') else Alert.id > 0)
        .scalar()
    ) or 0

    # Default fallback data if live values are uninitialized
    if total_vehicles == 0:
        total_vehicles = 14250
        alerts_today = 12

    return {
        "total_vehicles": total_vehicles,
        "congestion_level": "Heavy",
        "alerts_today": alerts_today,
        "average_speed_kmh": 34.5,
        "peak_traffic_hour": "08:00 AM - 09:30 AM",
        "vehicle_type_distribution": {
            "Cars": int(total_vehicles * 0.60),
            "Bikes": int(total_vehicles * 0.22),
            "Buses": int(total_vehicles * 0.08),
            "Trucks": int(total_vehicles * 0.10)
        }
    }


# ==========================================================
# TRAFFIC TRENDS (CHART & DATABASE QUERIES)
# ==========================================================

@router.get("/trends")
def get_traffic_trends(
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(auth.officer_required)
):
    """
    Returns structured chart trend data (hourly, daily) merged with
    weekly database query logs if available.
    """
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    db_records = []

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
        db_records = [{"date": str(r.date), "vehicles": r.total_vehicles, "logs": r.total_logs} for r in records]

    return {
        "hourly_labels": ["06:00", "08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00"],
        "vehicles_per_hour": [450, 1280, 920, 610, 750, 1100, 1520, 890],
        "congestion_percentage": [20, 85, 60, 35, 45, 70, 92, 50],
        "daily_labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "daily_totals": [12400, 13100, 14250, 13800, 15600, 9800, 7500],
        "db_records": db_records
    }


# ==========================================================
# ANALYTICS FRONTEND API EXTENSIONS
# ==========================================================

@router.get("/api/analytics/summary")
def analytics_summary():
    return {
        "total_vehicles": 81,
        "congestion": 65,
        "alerts_today": 4,
        "avg_speed": 38,
        "peak_hours": "08:00 - 10:00 and 17:00 - 19:00"
    }


@router.get("/api/analytics/hourly")
def analytics_hourly():
    return {
        "hours": [
            "06:00", "07:00", "08:00", "09:00", "10:00", "11:00", 
            "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", 
            "18:00", "19:00"
        ],
        "vehicles": [
            20, 35, 60, 82, 70, 55, 48, 52, 58, 65, 72, 88, 95, 80
        ],
        "congestion": [
            10, 20, 45, 70, 55, 40, 35, 38, 42, 48, 55, 72, 80, 65
        ]
    }


@router.get("/api/analytics/vehicle-distribution")
def vehicle_distribution():
    return {
        "labels": ["Cars", "Bikes", "Buses", "Trucks"],
        "values": [42, 25, 8, 6]
    }


class RouteRequest(BaseModel):
    road: str
    traffic_score: float


@router.post("/api/analytics/route-recommendation")
def route_recommendation(request: RouteRequest):
    score = request.traffic_score

    if score >= 80:
        level = "High Congestion"
        recommendation = "Avoid this road during peak hours."
        suggested_route = "Use an alternate route."
    elif score >= 50:
        level = "Moderate Congestion"
        recommendation = "Travel with caution."
        suggested_route = "Alternate route recommended."
    else:
        level = "Low Congestion"
        recommendation = "Road is suitable for travel."
        suggested_route = "Continue on this route."

    return {
        "road": request.road,
        "traffic_score": score,
        "traffic_level": level,
        "recommendation": recommendation,
        "suggested_route": suggested_route
    }