from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/recommendation", tags=["AI Recommendations"])

class TrafficInput(BaseModel):
    road_name: str
    density: float
    time_of_day: str
    emergency_vehicle_detected: bool = False

@router.post("/suggest")
async def generate_recommendation(payload: TrafficInput):
    """Generates AI-driven traffic optimization suggestions."""
    if payload.emergency_vehicle_detected:
        return {
            "status": "CRITICAL",
            "action": "Clear Lane Immediately",
            "recommendation": f"🚨 Emergency Vehicle detected on {payload.road_name}. Override signal to GREEN for fast passage.",
            "estimated_delay_saved": "5-8 minutes"
        }
    
    if payload.density >= 80:
        return {
            "status": "HEAVY_CONGESTION",
            "action": "Reroute Traffic",
            "recommendation": f"Heavy traffic detected on {payload.road_name}. Divert approaching traffic to Ring Road / Outer Bypass.",
            "estimated_delay_saved": "15-20 minutes"
        }
    elif payload.density >= 50:
        return {
            "status": "MODERATE_CONGESTION",
            "action": "Optimize Signal Timing",
            "recommendation": f"Moderate flow on {payload.road_name}. Increase green light duration by 15 seconds.",
            "estimated_delay_saved": "5 minutes"
        }
    else:
        return {
            "status": "CLEAR",
            "action": "Normal Operation",
            "recommendation": f"Traffic flow on {payload.road_name} is smooth. No action required.",
            "estimated_delay_saved": "0 minutes"
        }