# ==========================================================
# app/routers/incidents.py
# Incident Management Router (Admin & Supervisor Controls)
# ==========================================================

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import auth, models
from app.database import get_db

router = APIRouter(
    prefix="/api/incidents",
    tags=["Incident Management"],
)

# ==========================================================
# ROLE DEPENDENCIES
# ==========================================================

ALLOWED_VIEW_ROLES = {"admin", "administrator", "supervisor"}
ALLOWED_MANAGE_ROLES = {"admin", "administrator"}


def require_incident_view_access(
    current_user: models.User = Depends(auth.get_current_user),
) -> models.User:
    if (current_user.role or "").strip().lower() not in ALLOWED_VIEW_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin, Administrator, or Supervisor access required to view incidents.",
        )
    return current_user


def require_incident_manage_access(
    current_user: models.User = Depends(auth.get_current_user),
) -> models.User:
    if (current_user.role or "").strip().lower() not in ALLOWED_MANAGE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin clearance required to manage/modify incidents.",
        )
    return current_user


# ==========================================================
# PYDANTIC SCHEMAS
# ==========================================================

class IncidentCreate(BaseModel):
    incident_type: str = Field(..., description="Type of incident e.g., Collision, Breakdown")
    location: str = Field(..., description="Location of the incident")
    severity: str = Field(default="Low", description="Severity level: Low, Medium, High, Critical")
    vehicle_count: Optional[int] = None
    speed: Optional[str] = None
    description: Optional[str] = None


class IncidentOut(BaseModel):
    id: int
    type: str
    location: str
    severity: str
    status: str
    vehicle_count: Optional[int] = None
    speed: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_incident(cls, incident: models.Incident) -> "IncidentOut":
        return cls(
            id=incident.id,
            type=getattr(incident, "incident_type", "Collision"),
            location=incident.location,
            severity=incident.severity,
            status=incident.status,
            vehicle_count=getattr(incident, "vehicle_count", None),
            speed=getattr(incident, "speed", None),
            description=getattr(incident, "description", None),
            created_at=getattr(incident, "created_at", getattr(incident, "timestamp", None)),
            resolved_at=getattr(incident, "resolved_at", None),
        )


# ==========================================================
# ENDPOINTS
# ==========================================================

@router.get("", response_model=List[IncidentOut])
def get_incidents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_incident_view_access),
):
    """
    Returns all logged incidents. Restricted to Admin and Supervisor roles.
    """
    incidents = db.query(models.Incident).order_by(models.Incident.id.desc()).all()

    # Fallback mock data if table is empty
    if not incidents:
        return [
            IncidentOut(
                id=1,
                type="Collision",
                severity="Critical",
                location="Junction A - Main Signal",
                status="Active",
                vehicle_count=45,
                speed="12 km/h",
                description="Multi-vehicle traffic disruption.",
                created_at=datetime.utcnow(),
                resolved_at=None
            ),
            IncidentOut(
                id=2,
                type="Road Hazard",
                severity="Medium",
                location="Ring Road Sector 4",
                status="Resolved",
                vehicle_count=10,
                speed="35 km/h",
                description="Debris cleared from fast lane.",
                created_at=datetime.utcnow(),
                resolved_at=datetime.utcnow()
            )
        ]

    return [IncidentOut.from_orm_incident(i) for i in incidents]


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_incident_manage_access),
):
    """
    Creates a new incident record (Admin only).
    """
    new_incident = models.Incident(
        incident_type=payload.incident_type,
        location=payload.location,
        severity=payload.severity,
        vehicle_count=payload.vehicle_count,
        speed=payload.speed,
        status="Active",
        description=payload.description,
    )
    
    # If the database model uses 'timestamp' instead of 'created_at', set it safely if supported
    if hasattr(models.Incident, "timestamp") and not hasattr(models.Incident, "created_at"):
        setattr(new_incident, "timestamp", datetime.utcnow())

    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)

    return IncidentOut.from_orm_incident(new_incident)


@router.patch("/{incident_id}/resolve", response_model=IncidentOut)
@router.post("/{incident_id}/resolve", response_model=IncidentOut)
def resolve_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_incident_manage_access),
):
    """
    Marks an incident status as Resolved (Admin only).
    """
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = "Resolved"
    if hasattr(incident, "resolved_at"):
        incident.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(incident)

    return IncidentOut.from_orm_incident(incident)