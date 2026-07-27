# ==========================================================
# app/routers/congestion.py
# Smart Congestion Management, Emergency Priority, Alerts & Analytics
# ==========================================================

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import auth, config, models, utils
from app.database import get_db

router = APIRouter(prefix="/congestion", tags=["Smart Congestion Management"])


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def calculate_density(vehicle_count: int):
    """
    Determines traffic status and suggested signal duration.
    """
    if vehicle_count < 20:
        return "Low", 30  # (Status, Suggested Signal Timing in sec)
    elif vehicle_count <= 40:
        return "Medium", 60
    else:
        return "High", 90


def calculate_congestion(vehicle_count: int, emergency_count: int = 0) -> dict:
    """
    Calculates congestion density, dynamic signal timing, and AI recommendations.
    Supports emergency override protocols.
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
        "density": density,
        "signal_time": signal_time,
        "recommendation": recommendation
    }


# ==========================================================
# LATEST CONGESTION
# ==========================================================

@router.get("/latest")
def latest_congestion(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    congestion = (
        db.query(models.Congestion)
        .order_by(models.Congestion.created_at.desc())
        .first()
    )

    if congestion is None:
        raise HTTPException(
            status_code=404,
            detail="No congestion data available."
        )

    return congestion


# ==========================================================
# LIVE TRAFFIC STATUS
# ==========================================================

@router.get("/live")
def live_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    vehicle = (
        db.query(models.VehicleCount)
        .order_by(models.VehicleCount.id.desc())
        .first()
    )

    if vehicle is None:
        return {"status": "No Live Data"}

    level, signal, message = utils.congestion_level(vehicle.total)

    return {
        "total_vehicles": vehicle.total,
        "congestion": level,
        "green_signal": signal,
        "message": message,
        "density": utils.density_percentage(vehicle.total),
        "average_speed": utils.average_speed(level)
    }


# ==========================================================
# SMART SIGNAL
# ==========================================================

@router.get("/signal")
def signal(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    vehicle = (
        db.query(models.VehicleCount)
        .order_by(models.VehicleCount.id.desc())
        .first()
    )

    if vehicle is None:
        return {"green_signal": 30}

    level, signal_time, _ = utils.congestion_level(vehicle.total)

    return {
        "traffic_level": level,
        "green_signal": signal_time
    }


# ==========================================================
# AI RECOMMENDATION
# ==========================================================

@router.get("/recommendation")
def recommendation(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    vehicle = (
        db.query(models.VehicleCount)
        .order_by(models.VehicleCount.id.desc())
        .first()
    )

    if vehicle is None:
        return {"recommendation": "No recommendation."}

    level, _, _ = utils.congestion_level(vehicle.total)

    return {
        "traffic_level": level,
        "recommendation": utils.recommendation(level)
    }


# ==========================================================
# DENSITY
# ==========================================================

@router.get("/density")
def density(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    vehicle = (
        db.query(models.VehicleCount)
        .order_by(models.VehicleCount.id.desc())
        .first()
    )

    if vehicle is None:
        return {"density": 0}

    return {
        "density": utils.density_percentage(vehicle.total)
    }


# ==========================================================
# PROCESS DETECTED FRAME & LOG TRAFFIC
# ==========================================================

@router.post("/process-frame")
def process_detection(
    location: str,
    lat: float,
    lng: float,
    vehicle_count: int,
    accident: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    density_status, signal_time = calculate_density(vehicle_count)

    # Save detailed detection log
    log = models.TrafficLog(
        location=location,
        lat=lat,
        lng=lng,
        vehicle_count=vehicle_count,
        density_status=density_status,
        has_accident=accident
    )
    db.add(log)

    # Auto-generate system Alert if High Congestion or Accident
    if density_status == "High":
        alert = models.Alert(
            title="Heavy Traffic Alert",
            description=f"High density detected at {location}",
            location=location,
            alert_type="Heavy Traffic",
            severity="High",
            status="Active"
        )
        db.add(alert)

    if accident:
        alert = models.Alert(
            title="Accident Alert",
            description=f"Accident reported at {location}",
            location=location,
            alert_type="Accident",
            severity="Critical",
            status="Active"
        )
        db.add(alert)

    db.commit()

    return {
        "location": location,
        "vehicle_count": vehicle_count,
        "density": density_status,
        "suggested_signal_time_sec": signal_time,
        "accident_reported": accident
    }


# ==========================================================
# EMERGENCY VEHICLE PRIORITY
# ==========================================================

@router.get("/emergency")
def emergency_priority(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    vehicle = (
        db.query(models.VehicleCount)
        .order_by(models.VehicleCount.id.desc())
        .first()
    )

    if vehicle is None:
        return {
            "emergency_detected": False,
            "signal_time": 30,
            "message": "No vehicle data available."
        }

    emergency_detected = vehicle.ambulance > 0

    if emergency_detected:
        return {
            "emergency_detected": True,
            "ambulance_count": vehicle.ambulance,
            "signal_time": 90,
            "priority": "HIGH",
            "message": "Emergency vehicle detected. Green signal extended."
        }

    return {
        "emergency_detected": False,
        "signal_time": 30,
        "priority": "NORMAL",
        "message": "No emergency vehicle detected."
    }


# ==========================================================
# CONGESTION ALERTS
# ==========================================================

@router.get("/alerts")
def congestion_alerts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    latest = (
        db.query(models.Congestion)
        .order_by(models.Congestion.created_at.desc())
        .first()
    )

    if latest is None:
        return []

    alerts = []

    if latest.congestion_level == "HIGH":
        alerts.append({
            "type": "HIGH CONGESTION",
            "severity": "HIGH",
            "message": "Heavy traffic detected."
        })
    elif latest.congestion_level == "MEDIUM":
        alerts.append({
            "type": "MEDIUM CONGESTION",
            "severity": "MEDIUM",
            "message": "Traffic is increasing."
        })

    if latest.average_speed < 20:
        alerts.append({
            "type": "LOW SPEED",
            "severity": "HIGH",
            "message": "Average traffic speed is below threshold."
        })

    return alerts


# ==========================================================
# CONGESTION HISTORY
# ==========================================================

@router.get("/history")
def congestion_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    history = (
        db.query(models.Congestion)
        .order_by(models.Congestion.created_at.desc())
        .all()
    )
    return history


# ==========================================================
# HEATMAP DATA
# ==========================================================

@router.get("/heatmap")
def heatmap(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    records = db.query(models.Congestion).all()
    heatmap_data = []

    latitude = 12.9716
    longitude = 77.5946

    for record in records:
        heatmap_data.append({
            "latitude": latitude,
            "longitude": longitude,
            "density": record.density,
            "level": record.congestion_level
        })
        latitude += 0.001
        longitude += 0.001

    return heatmap_data


# ==========================================================
# DAILY ANALYTICS
# ==========================================================

@router.get("/analytics/daily")
def daily_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    today = datetime.utcnow().date()

    total = (
        db.query(func.count(models.Congestion.id))
        .filter(func.date(models.Congestion.created_at) == today)
        .scalar()
    )

    return {
        "date": str(today),
        "records": total
    }


# ==========================================================
# WEEKLY ANALYTICS
# ==========================================================

@router.get("/analytics/weekly")
def weekly_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    last_week = datetime.utcnow() - timedelta(days=7)

    total = (
        db.query(func.count(models.Congestion.id))
        .filter(models.Congestion.created_at >= last_week)
        .scalar()
    )

    return {
        "last_7_days": total
    }


# ==========================================================
# MONTHLY ANALYTICS
# ==========================================================

@router.get("/analytics/monthly")
def monthly_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    last_month = datetime.utcnow() - timedelta(days=30)

    total = (
        db.query(func.count(models.Congestion.id))
        .filter(models.Congestion.created_at >= last_month)
        .scalar()
    )

    return {
        "last_30_days": total
    }


# ==========================================================
# TRAFFIC PREDICTION
# ==========================================================

@router.get("/prediction")
def traffic_prediction(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    latest = (
        db.query(models.Congestion)
        .order_by(models.Congestion.created_at.desc())
        .first()
    )

    if latest is None:
        return {"prediction": "Insufficient data."}

    if latest.congestion_level == "HIGH":
        prediction = "High congestion expected during the next hour."
    elif latest.congestion_level == "MEDIUM":
        prediction = "Moderate congestion expected."
    else:
        prediction = "Traffic expected to remain normal."

    return {
        "current_level": latest.congestion_level,
        "prediction": prediction
    }


# ==========================================================
# TRAFFIC DIVERSION
# ==========================================================

@router.get("/diversion")
def traffic_diversion(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    latest = (
        db.query(models.Congestion)
        .order_by(models.Congestion.created_at.desc())
        .first()
    )

    if latest is None:
        return {"diversion": "No suggestion available."}

    if latest.congestion_level == "HIGH":
        route = "Redirect vehicles to Alternate Route B."
    elif latest.congestion_level == "MEDIUM":
        route = "Reduce heavy vehicle entry."
    else:
        route = "No diversion required."

    return {
        "traffic_level": latest.congestion_level,
        "diversion": route
    }


# ==========================================================
# ADMIN SUMMARY
# ==========================================================

@router.get("/admin/summary")
def admin_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.admin_required)
):
    total_records = db.query(models.Congestion).count()

    high = (
        db.query(models.Congestion)
        .filter(models.Congestion.congestion_level == "HIGH")
        .count()
    )

    medium = (
        db.query(models.Congestion)
        .filter(models.Congestion.congestion_level == "MEDIUM")
        .count()
    )

    low = (
        db.query(models.Congestion)
        .filter(models.Congestion.congestion_level == "LOW")
        .count()
    )

    critical = (
        db.query(models.Congestion)
        .filter(models.Congestion.congestion_level == "CRITICAL")
        .count()
    )

    return {
        "total_records": total_records,
        "high_congestion": high,
        "medium_congestion": medium,
        "low_congestion": low,
        "critical_congestion": critical
    }