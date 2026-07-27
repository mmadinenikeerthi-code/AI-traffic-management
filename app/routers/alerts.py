# ==========================================================
# app/routers/alerts.py
# Traffic Alerts, Incident Reporting, and Alert Management
# ==========================================================

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, database
from app.models import Alert
from app.schemas import AlertResponse, AccidentCreate
from app.database import get_db

router = APIRouter(prefix="", tags=["Alerts & Incidents"])


# ==========================================================
# FETCH ALERTS (STEP 1 & GENERAL FETCH)
# ==========================================================

@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    """
    Step 1: Fetch live alerts.
    Fetches active and past alerts ordered by newest first (up to 50 records).
    """
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(50).all()
    return alerts


# ==========================================================
# TRIGGER / CREATE GENERAL ALERT
# ==========================================================

@router.post("/alerts/create")
def create_alert(
    title: str,
    description: Optional[str] = None,
    location: Optional[str] = None,
    alert_type: str = "Heavy Traffic",
    severity: str = "High",
    db: Session = Depends(get_db)
):
    """
    Trigger and log a new general traffic alert.
    """
    new_alert = Alert(
        title=title,
        description=description,
        location=location,
        alert_type=alert_type,
        severity=severity,
        status="Active"
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return {"message": "Alert triggered successfully", "alert": new_alert}


# ==========================================================
# RESOLVE ALERT
# ==========================================================

@router.put("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Mark an alert as Resolved so it no longer triggers active warnings.
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "Resolved"
    db.commit()
    db.refresh(alert)
    return {"message": f"Alert {alert_id} marked as resolved", "alert": alert}


# ==========================================================
# ACCIDENT REPORTING (STEP 3)
# ==========================================================

@router.post("/accident", status_code=status.HTTP_201_CREATED)
def report_accident(data: AccidentCreate, db: Session = Depends(get_db)):
    """
    Step 3: Manual/Automated accident reporting endpoint.
    Creates an alert specifically flagged for accident events.
    Handles compatibility for both 'description' and 'message' fields.
    """
    # Safely extract message or description parameter from schema
    msg_content = getattr(data, 'message', None) or getattr(data, 'description', '')
    formatted_description = f"Accident Reported at {data.location}. Severity: {data.severity}. {msg_content}".strip()

    new_alert_kwargs = {
        "location": data.location,
        "alert_type": "Accident",
        "severity": data.severity,
        "status": "Active"
    }

    # Conditionally populate model fields if supported by Alert model
    if hasattr(Alert, 'title'):
        new_alert_kwargs["title"] = "Accident Alert"
    if hasattr(Alert, 'description'):
        new_alert_kwargs["description"] = formatted_description
    if hasattr(Alert, 'message'):
        new_alert_kwargs["message"] = formatted_description

    new_alert = Alert(**new_alert_kwargs)

    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)

    return {
        "status": "success",
        "message": "Accident alert created",
        "alert_id": new_alert.id,
        "alert": new_alert
    }