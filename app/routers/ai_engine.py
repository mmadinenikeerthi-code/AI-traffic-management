# ==========================================================
# app/routers/ai_engine.py
# AI Recommendation Engine
# ==========================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import auth, models
from app.database import get_db

router = APIRouter(prefix="/ai", tags=["AI Recommendations"])


@router.get("/recommendations")
def get_recommendations(
    vehicle_count: int = 0,
    density: str = "Low",
    accident: bool = False,
    current_user: models.User = Depends(auth.officer_required)
):
    """Generates real-time dynamic action plan based on current traffic parameters."""
    actions = []

    if accident:
        actions.append("🚨 Dispatch emergency team immediately & reroute approaching vehicles.")
    
    if density.upper() in ["HIGH", "CRITICAL"] or vehicle_count > 50:
        actions.append("🚦 Extend green signal timing to 90 seconds on main arterial road.")
        actions.append("🗺️ Dynamic rerouting: Advise vehicles via OpenStreetMap to take Bypass B.")
    elif density.upper() == "MEDIUM":
        actions.append("🟡 Maintain green signal timing at 60 seconds.")
        actions.append("👁️ Monitor inflow from adjacent junction.")
    else:
        actions.append("✅ Traffic flow optimal. Standard 30-second signal cycle in effect.")

    return {
        "density": density,
        "vehicle_count": vehicle_count,
        "accident_reported": accident,
        "recommendations": actions
    }