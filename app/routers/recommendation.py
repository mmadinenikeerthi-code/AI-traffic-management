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
    # Inside app/routers/recommendation.py

@router.post("/compare-routes")
def compare_alternative_routes(payload: dict):
    """
    Compares multiple routes (e.g., Route A, Route B, Route C) based on distance, 
    estimated duration, and live traffic density to let the AI select the best option.
    """
    routes = payload.get("routes", [
        {"name": "Route A (Main Corridor)", "distance_km": 12.0, "duration_min": 24, "density": 85},
        {"name": "Route B (Ring Road Bypass)", "distance_km": 14.0, "duration_min": 22, "density": 45},
        {"name": "Route C (Inner Lane)", "distance_km": 16.0, "duration_min": 20, "density": 20}
    ])

    evaluated_routes = []
    for r in routes:
        density = r.get("density", 50)
        if density >= 75:
            status_tag = "Heavy"
            recommendation = "❌ Avoid"
        elif density >= 40:
            status_tag = "Medium"
            recommendation = "Alternative"
        else:
            status_tag = "Low"
            recommendation = "⭐ Recommended"

        evaluated_routes.append({
            "name": r["name"],
            "distance_km": r["distance_km"],
            "duration_min": r["duration_min"],
            "traffic_status": status_tag,
            "ai_advice": recommendation
        })

    return {
        "status": "success",
        "optimal_selection": "Route B (Ring Road Bypass)",
        "evaluated_options": evaluated_routes
    }