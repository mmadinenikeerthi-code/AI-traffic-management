# ==========================================================
# app/routers/heatmap.py
# Traffic Heatmap & Routing Endpoint (Pan-India Support & Bug Fix)
# ==========================================================

from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
from pathlib import Path

from app import auth, models
from app.database import get_db

# Note: If you use prefix="/heatmap" in main.py, change the route decorators below 
# to @router.get("") and @router.get("/points") to avoid /heatmap/heatmap.
router = APIRouter(tags=["Traffic Heatmap & Routing"])

# Setup Templates Directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = os.path.join(BASE_DIR, "frontend", "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ==========================================================
# PAGE ROUTE: /heatmap
# ==========================================================
@router.get("/heatmap", response_class=HTMLResponse)
async def heatmap_page(request: Request, location: Optional[str] = ""):
    """Serves the Heatmap & Routing HTML page"""
    
    # FIXED: Explicitly define keyword arguments to prevent the 'unhashable dict' error
    return templates.TemplateResponse(
        request=request,
        name="heatmap.html",
        context={
            "request": request,
            "location": location
        }
    )

# ==========================================================
# DATA API ROUTE: /heatmap/points
# ==========================================================
@router.get("/heatmap/points")
def get_heatmap_points(
    search: Optional[str] = Query(None, description="Search by state, city, or road name"),
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(auth.officer_required)
):
    """
    Returns congestion data points for the map. 
    Filters by the 'search' parameter to return specific locations nationwide.
    """
    logs = []
    
    # 1. Try to fetch live data from the database
    if hasattr(models, 'TrafficLog'):
        query = db.query(models.TrafficLog)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(models.TrafficLog.road_name.ilike(search_term))
            
        logs = query.order_by(models.TrafficLog.timestamp.desc()).limit(500).all()

    if logs:
        points = []
        for log in logs:
            density = getattr(log, 'density_status', 'LOW')
            intensity = 0.3 if density == "LOW" else (0.6 if density == "MEDIUM" else 0.9)
            points.append({
                "id": f"junction_{getattr(log, 'id', '1')}",
                "road": getattr(log, 'road_name', 'Signal Junction'),
                "lat": getattr(log, 'lat', 0.0),
                "lng": getattr(log, 'lng', 0.0),
                "intensity": intensity,
                "level": density,
                "vehicle_count": getattr(log, 'vehicle_count', 0),
                "speed": f"{getattr(log, 'average_speed', 30)} km/h",
                "recommendation": getattr(log, 'recommendation', 'Maintain Traffic Flow')
            })
        return points

    # 2. Fallback Data: Spanning Major States across India
    fallback_data = [
        {"id": "AP_Kurnool", "road": "Raj Vihar Center, Kurnool (AP)", "lat": 15.8281, "lng": 78.0373, "intensity": 0.85, "level": "HEAVY", "vehicle_count": 145, "speed": "18 km/h", "recommendation": "Divert to NH44 Bypass"},
        {"id": "TG_Hyd", "road": "Ameerpet Junction, Hyderabad (TG)", "lat": 17.4375, "lng": 78.4482, "intensity": 0.92, "level": "HEAVY", "vehicle_count": 210, "speed": "10 km/h", "recommendation": "Severe Congestion. Route to Metro."},
        {"id": "KA_Blr", "road": "Silk Board Junction, Bangalore (KA)", "lat": 12.9172, "lng": 77.6228, "intensity": 0.98, "level": "HEAVY", "vehicle_count": 450, "speed": "5 km/h", "recommendation": "Avoid Route. Use Elevated Tollway."},
        {"id": "MH_Mum", "road": "Bandra Kurla Complex, Mumbai (MH)", "lat": 19.0693, "lng": 72.8656, "intensity": 0.95, "level": "HEAVY", "vehicle_count": 320, "speed": "8 km/h", "recommendation": "Heavy Congestion."},
        {"id": "DL_CP", "road": "Connaught Place, Delhi (DL)", "lat": 28.6315, "lng": 77.2167, "intensity": 0.70, "level": "MEDIUM", "vehicle_count": 150, "speed": "25 km/h", "recommendation": "Monitor closely for evening peak."},
        {"id": "TN_Che", "road": "Kathipara Junction, Chennai (TN)", "lat": 13.0125, "lng": 80.2016, "intensity": 0.90, "level": "HEAVY", "vehicle_count": 240, "speed": "16 km/h", "recommendation": "Use Grade Separator"},
        {"id": "WB_Kol", "road": "Park Street, Kolkata (WB)", "lat": 22.5555, "lng": 88.3522, "intensity": 0.82, "level": "HEAVY", "vehicle_count": 190, "speed": "18 km/h", "recommendation": "Use alternate routes."}
    ]

    # 3. Apply the Search Filter to Fallback Data
    if search:
        search_lower = search.lower()
        fallback_data = [
            pt for pt in fallback_data 
            if search_lower in pt["road"].lower() or search_lower in pt["id"].lower()
        ]

    return fallback_data
    