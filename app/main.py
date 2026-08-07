# ==========================================================
# app/main.py
# AI Traffic Management & Congestion Detection System
# ==========================================================

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Request,
    Query,
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel

from sqlalchemy import func
from sqlalchemy.orm import Session

import uvicorn


# ==========================================================
# PROJECT IMPORTS
# ==========================================================

from app.database import engine, Base, get_db
from app import models
from app import schemas

# IMPORTANT:
# Admin authentication for incident page/API
from app.auth import admin_required


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==========================================================
# ROUTERS
# ==========================================================

# ---------------- Authentication ----------------

try:
    from app.routers import auth as auth_router
except ImportError as e:
    auth_router = None
    logger.warning(
        "Authentication router not available: %s",
        e
    )


# ---------------- Users ----------------

try:
    from app.routers import users as users_router
except ImportError as e:
    users_router = None
    logger.warning(
        "Users router not available: %s",
        e
    )


# ---------------- Settings ----------------

try:
    from app.routers import settings as settings_router
except ImportError as e:
    settings_router = None
    logger.warning(
        "Settings router not available: %s",
        e
    )


# ---------------- Detection ----------------

try:
    from app.routers import detect as detect_router
except ImportError as e:
    detect_router = None
    logger.error(
        "Could not import detection router: %s",
        e
    )


# ---------------- OpenStreetMap ----------------

try:
    from app.routers.osm_router import router as osm_router
except ImportError as e:
    osm_router = None
    logger.warning(
        "OSM router not available: %s",
        e
    )


# ---------------- ML Prediction ----------------

try:
    from app.routers.ml_prediction import router as ml_prediction_router
except ImportError as e:
    ml_prediction_router = None
    logger.warning(
        "ML prediction router not available: %s",
        e
    )


# ---------------- World Distance ----------------

try:
    from app.world_distance import get_world_distance

except ImportError:

    def get_world_distance(origin, destination):
        return 0.0


# ---------------- Heatmap ----------------

try:
    from app.routers.recommendation import (
        get_heatmap_coordinates
    )

except ImportError:

    def get_heatmap_coordinates():
        return [
            [15.8281, 78.0373, 0.9],
            [17.3850, 78.4867, 0.7],
            [13.0827, 80.2707, 0.5],
        ]


# ==========================================================
# PROJECT DIRECTORIES
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_DIR = BASE_DIR / "frontend" / "static"
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"

UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
REPORT_DIR = BASE_DIR / "reports"


# ==========================================================
# CREATE DIRECTORIES
# ==========================================================

for folder in [
    STATIC_DIR,
    TEMPLATES_DIR,
    UPLOAD_DIR,
    OUTPUT_DIR,
    REPORT_DIR,
]:
    folder.mkdir(
        parents=True,
        exist_ok=True
    )


# ==========================================================
# APPLICATION
# ==========================================================

APP_NAME = (
    "AI Traffic Management "
    "& Congestion Detection System"
)

VERSION = "1.0.0"

app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description=(
        "AI based Traffic Management and "
        "Congestion Detection System"
    ),
)


# ==========================================================
# CORS
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# STATIC FILES
# ==========================================================

if STATIC_DIR.exists():

    app.mount(
        "/static",
        StaticFiles(
            directory=str(STATIC_DIR)
        ),
        name="static",
    )


# ==========================================================
# TEMPLATES
# ==========================================================

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR)
)


# ==========================================================
# DATABASE
# ==========================================================

Base.metadata.create_all(bind=engine)


# ==========================================================
# ROUTER REGISTRATION
# ==========================================================

# ---------------- Authentication ----------------

if auth_router is not None:

    app.include_router(
        auth_router.router,
        prefix="/auth",
        tags=["Authentication"],
    )


# ---------------- Users ----------------

if users_router is not None:

    app.include_router(
        users_router.router,
        prefix="/users",
        tags=["Users"],
    )


# ---------------- Settings ----------------

if settings_router is not None:

    app.include_router(
        settings_router.router,
        prefix="/settings",
        tags=["Settings"],
    )


# ---------------- Detection ----------------

if detect_router is not None:

    existing_prefix = getattr(
        detect_router.router,
        "prefix",
        ""
    )

    if existing_prefix.startswith("/detect"):

        app.include_router(
            detect_router.router,
            tags=["Detection"],
        )

    else:

        app.include_router(
            detect_router.router,
            prefix="/detect",
            tags=["Detection"],
        )

    logger.info(
        "Detection router registered successfully"
    )

else:

    logger.warning(
        "Detection router was NOT registered"
    )


# ---------------- OpenStreetMap ----------------

if osm_router is not None:

    app.include_router(
        osm_router
    )


# ---------------- ML Prediction ----------------

if ml_prediction_router is not None:

    app.include_router(
        ml_prediction_router
    )


# ==========================================================
# TEMPLATE HELPER
# ==========================================================

def render_template(
    template_name: str,
    request: Request,
    title: str,
    active_page: str = "",
):

    target_path = TEMPLATES_DIR / template_name

    if not target_path.exists():

        logger.warning(
            "Template '%s' not found.",
            template_name
        )

        return HTMLResponse(
            content=(
                "<html>"
                "<body>"
                f"<h1>{title}</h1>"
                f"<p>Template '{template_name}' "
                "was not found.</p>"
                "<a href='/'>Go Home</a>"
                "</body>"
                "</html>"
            ),
            status_code=404,
        )

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "title": title,
            "active_page": active_page,
        },
    )


# ==========================================================
# INPUT SCHEMAS
# ==========================================================

class RouteInput(BaseModel):

    road_name: str

    density: float

    emergency_vehicle_detected: bool = False


class WorldDistanceRequest(BaseModel):

    origin: str

    destination: str


# ==========================================================
# ROOT
# ==========================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
async def root_page(
    request: Request
):

    return render_template(
        "login.html",
        request,
        "Login | AI Traffic Control",
        "login",
    )


# ==========================================================
# WORLD DISTANCE
# ==========================================================

@app.post("/world-distance")
def calculate_world_distance_api(
    payload: WorldDistanceRequest,
):

    try:

        distance_km = get_world_distance(
            payload.origin,
            payload.destination,
        )

        if isinstance(distance_km, str):

            raise HTTPException(
                status_code=404,
                detail=distance_km,
            )

        return {
            "status": "success",
            "origin": payload.origin,
            "destination": payload.destination,
            "distance_km": round(
                distance_km,
                2
            ),
            "distance_miles": round(
                distance_km * 0.621371,
                2
            ),
        }

    except HTTPException:
        raise

    except Exception as e:

        logger.exception(
            "World distance error"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================================
# RECOMMENDATION
# ==========================================================

@app.post("/recommendation/suggest")
def generate_recommendation(
    payload: RouteInput,
):

    if payload.emergency_vehicle_detected:

        return {
            "status": "CRITICAL",
            "action": "Clear Lane Immediately",
            "recommendation": (
                f"Emergency Vehicle on "
                f"{payload.road_name}. "
                "Green priority signal overridden."
            ),
            "estimated_time_saved": "8 minutes",
        }

    if payload.density >= 75.0:

        return {
            "status": "HEAVY_CONGESTION",
            "action": "Divert Traffic",
            "recommendation": (
                f"Heavy density on "
                f"{payload.road_name}. "
                "Reroute vehicles via "
                "Outer Ring Road."
            ),
            "estimated_time_saved": "15 minutes",
        }

    return {
        "status": "CLEAR",
        "action": "Normal Flow",
        "recommendation": (
            f"Flow on {payload.road_name} "
            "is smooth. Standard signal "
            "timing active."
        ),
        "estimated_time_saved": "0 minutes",
    }


# ==========================================================
# ROUTE COMPARISON
# ==========================================================

@app.post("/recommendation/compare-routes")
def compare_alternative_routes(
    payload: dict,
):

    routes = payload.get(
        "routes",
        [
            {
                "name": "Route A (Main Corridor)",
                "distance_km": 12.0,
                "duration_min": 24,
                "density": 85,
            },
            {
                "name": "Route B (Ring Road Bypass)",
                "distance_km": 14.0,
                "duration_min": 22,
                "density": 45,
            },
            {
                "name": "Route C (Inner Lane)",
                "distance_km": 16.0,
                "duration_min": 20,
                "density": 20,
            },
        ],
    )

    evaluated_routes = []

    for route in routes:

        density = route.get(
            "density",
            50
        )

        if density >= 75:

            status_tag = "Heavy"
            recommendation = "Avoid"

        elif density >= 40:

            status_tag = "Medium"
            recommendation = "Alternative"

        else:

            status_tag = "Low"
            recommendation = "Recommended"

        evaluated_routes.append(
            {
                "name": route["name"],
                "distance_km":
                    route["distance_km"],
                "duration_min":
                    route["duration_min"],
                "traffic_status":
                    status_tag,
                "ai_advice":
                    recommendation,
            }
        )

    if evaluated_routes:

        best_route = min(
            evaluated_routes,
            key=lambda x: (
                x["traffic_status"] == "Heavy",
                x["duration_min"],
            ),
        )

        optimal_selection = best_route["name"]

    else:

        optimal_selection = None

    return {
        "status": "success",
        "optimal_selection":
            optimal_selection,
        "evaluated_options":
            evaluated_routes,
    }


# ==========================================================
# ANALYTICS SUMMARY
# ==========================================================

@app.get("/analytics/summary")
def get_analytics_summary(
    db: Session = Depends(get_db),
):

    try:

        total_v = (
            db.query(
                func.sum(
                    models.VehicleCount.total
                )
            )
            .scalar()
            or 0
        )

        active_a = (
            db.query(
                func.count(
                    models.Alert.id
                )
            )
            .filter(
                models.Alert.status == "Active"
            )
            .scalar()
            or 0
        )

        total_v = int(total_v)

        if total_v >= 150:
            congestion_level = "High"

        elif total_v >= 75:
            congestion_level = "Moderate"

        else:
            congestion_level = "Low"

        return {
            "total_vehicles": total_v,
            "congestion_level":
                congestion_level,
            "alerts_today":
                int(active_a),
            "average_speed_kmh": 36.5,
            "peak_traffic_hour":
                "08:30 AM - 10:00 AM",
            "vehicle_type_distribution": {
                "Cars":
                    int(total_v * 0.55),
                "Bikes":
                    int(total_v * 0.25),
                "Buses":
                    int(total_v * 0.10),
                "Trucks":
                    int(total_v * 0.10),
            },
        }

    except Exception as e:

        logger.exception(
            "Analytics summary error"
        )

        return {
            "total_vehicles": 0,
            "congestion_level": "Unknown",
            "alerts_today": 0,
            "average_speed_kmh": 0,
            "peak_traffic_hour": "N/A",
            "vehicle_type_distribution": {
                "Cars": 0,
                "Bikes": 0,
                "Buses": 0,
                "Trucks": 0,
            },
        }


# ==========================================================
# TRAFFIC TRENDS
# ==========================================================

@app.get("/analytics/trends")
def get_traffic_trends(
    db: Session = Depends(get_db),
):

    try:

        rows = (
            db.query(
                models.VehicleCount
            )
            .order_by(
                models.VehicleCount
                .detected_time
                .asc()
            )
            .all()
        )

        if not rows:

            return {
                "hourly_labels": [],
                "vehicles_per_hour": [],
                "congestion_percentage": [],
            }

        hourly = {}

        for row in rows:

            if row.detected_time:

                hour = row.detected_time.strftime(
                    "%H:00"
                )

                if hour not in hourly:
                    hourly[hour] = 0

                hourly[hour] += (
                    row.total or 0
                )

        labels = list(hourly.keys())
        vehicles = list(hourly.values())

        congestion = []

        for value in vehicles:

            percentage = min(
                100,
                int(
                    (value / 200) * 100
                )
            )

            congestion.append(
                percentage
            )

        return {
            "hourly_labels": labels,
            "vehicles_per_hour": vehicles,
            "congestion_percentage":
                congestion,
        }

    except Exception as e:

        logger.exception(
            "Traffic trends error"
        )

        return {
            "hourly_labels": [],
            "vehicles_per_hour": [],
            "congestion_percentage": [],
        }


# ==========================================================
# KPI
# ==========================================================

@app.get("/analytics/kpis")
async def get_kpis(
    db: Session = Depends(get_db),
):

    try:

        latest = (
            db.query(
                models.VehicleCount
            )
            .order_by(
                models.VehicleCount
                .detected_time
                .desc()
            )
            .first()
        )

        if latest is None:

            return {
                "total_vehicles": 0,
                "avg_speed": 0,
                "details": None,
            }

        latest_congestion = (
            db.query(
                models.Congestion
            )
            .order_by(
                models.Congestion
                .created_at
                .desc()
            )
            .first()
        )

        avg_speed = 0

        if latest_congestion:

            avg_speed = (
                latest_congestion.average_speed
                or 0
            )

        return {
            "total_vehicles":
                latest.total or 0,

            "avg_speed":
                avg_speed,

            "details": {
                "cars":
                    latest.cars or 0,
                "bikes":
                    latest.bikes or 0,
                "buses":
                    latest.buses or 0,
                "trucks":
                    latest.trucks or 0,
                "autos":
                    latest.auto_rickshaw or 0,
                "ambulances":
                    latest.ambulance or 0,
                "time":
                    (
                        latest.detected_time.isoformat()
                        if latest.detected_time
                        else None
                    ),
            },
        }

    except Exception as e:

        logger.exception(
            "KPI error"
        )

        return {
            "total_vehicles": 0,
            "avg_speed": 0,
            "details": None,
        }


# ==========================================================
# TRAFFIC STATUS
# ==========================================================

@app.get("/analytics/traffic-status")
async def get_traffic_status(
    vehicle_count: int = 0,
    emergency_count: int = 0,
):

    if emergency_count > 0:

        status_value = "critical"

    elif vehicle_count >= 75:

        status_value = "high"

    elif vehicle_count >= 40:

        status_value = "moderate"

    else:

        status_value = "normal"

    return {
        "vehicle_count":
            vehicle_count,

        "emergency_count":
            emergency_count,

        "status":
            status_value,
    }


# ==========================================================
# LIVE DASHBOARD
# ==========================================================

@app.get("/detect/live-dashboard")
def live_dashboard_api(
    db: Session = Depends(get_db),
):

    try:

        latest_count = (
            db.query(
                models.VehicleCount
            )
            .order_by(
                models.VehicleCount
                .detected_time
                .desc()
            )
            .first()
        )

        latest_congestion = (
            db.query(
                models.Congestion
            )
            .order_by(
                models.Congestion
                .created_at
                .desc()
            )
            .first()
        )

        if not latest_count:

            return {
                "total_vehicles": 0,
                "cars": 0,
                "bikes": 0,
                "buses": 0,
                "trucks": 0,
                "autos": 0,
                "ambulances": 0,
                "congestion_level": "LOW",
                "avg_speed": 0,
                "density_percentage": 0,
            }

        return {
            "total_vehicles":
                latest_count.total or 0,

            "cars":
                latest_count.cars or 0,

            "bikes":
                latest_count.bikes or 0,

            "buses":
                latest_count.buses or 0,

            "trucks":
                latest_count.trucks or 0,

            "autos":
                latest_count.auto_rickshaw or 0,

            "ambulances":
                latest_count.ambulance or 0,

            "congestion_level":
                (
                    latest_congestion.congestion_level
                    if latest_congestion
                    else "LOW"
                ),

            "avg_speed":
                (
                    latest_congestion.average_speed
                    if latest_congestion
                    else 0
                ),

            "density_percentage":
                (
                    latest_congestion.density
                    if latest_congestion
                    else 0
                ),

            "detected_time":
                (
                    latest_count.detected_time.isoformat()
                    if latest_count.detected_time
                    else None
                ),
        }

    except Exception as e:

        logger.exception(
            "Live dashboard error: %s",
            e
        )

        return {
            "total_vehicles": 0,
            "cars": 0,
            "bikes": 0,
            "buses": 0,
            "trucks": 0,
            "autos": 0,
            "ambulances": 0,
            "congestion_level": "LOW",
            "avg_speed": 0,
            "density_percentage": 0,
        }


# ==========================================================
# HEATMAP POINTS
# ==========================================================

@app.get("/heatmap/points")
def get_heatmap_points_api(
    search: Optional[str] = Query(None),
):

    data = [

        {
            "id": "AP_Kurnool",
            "road":
                "Raj Vihar Center, Kurnool",
            "lat": 15.8281,
            "lng": 78.0373,
            "intensity": 0.85,
            "level": "HEAVY",
            "vehicle_count": 145,
            "speed": "18 km/h",
        },

        {
            "id": "TG_Hyd",
            "road":
                "Ameerpet Junction, Hyderabad",
            "lat": 17.4375,
            "lng": 78.4482,
            "intensity": 0.92,
            "level": "HEAVY",
            "vehicle_count": 210,
            "speed": "10 km/h",
        },

        {
            "id": "KA_Blr",
            "road":
                "Silk Board, Bangalore",
            "lat": 12.9172,
            "lng": 77.6228,
            "intensity": 0.98,
            "level": "HEAVY",
            "vehicle_count": 350,
            "speed": "5 km/h",
        },

        {
            "id": "MH_Mum",
            "road":
                "BKC, Mumbai",
            "lat": 19.0693,
            "lng": 72.8656,
            "intensity": 0.75,
            "level": "MEDIUM",
            "vehicle_count": 190,
            "speed": "22 km/h",
        },
    ]

    if search:

        search_lower = search.lower()

        data = [
            point
            for point in data
            if search_lower
            in point["road"].lower()
        ]

    return data


# ==========================================================
# HEATMAP API
# ==========================================================

@app.get("/api/heatmap")
def heatmap_api():

    try:

        return {
            "points":
                get_heatmap_coordinates()
        }

    except Exception as e:

        logger.exception(
            "Heatmap error: %s",
            e
        )

        return {
            "points": []
        }


# ==========================================================
# AI RECOMMENDATIONS
# ==========================================================

@app.get("/api/recommendations")
def get_ai_recommendations(
    db: Session = Depends(get_db),
):

    try:

        zones = (
            db.query(
                models.TrafficZone
            )
            .all()
        )

        traffic_zones = [

            {
                "road_name":
                    zone.road_name,

                "density":
                    zone.density,

                "avg_speed":
                    zone.avg_speed,

                "vehicle_count":
                    zone.vehicle_count,

                "has_accident":
                    zone.has_accident,
            }

            for zone in zones
        ]

        if not traffic_zones:

            traffic_zones = [

                {
                    "road_name":
                        "Outer Ring Road, Hyderabad",
                    "density": 0.85,
                    "avg_speed": 14,
                    "vehicle_count": 280,
                    "has_accident": False,
                },

                {
                    "road_name":
                        "MG Road, Bangalore",
                    "density": 0.45,
                    "avg_speed": 35,
                    "vehicle_count": 110,
                    "has_accident": False,
                },

                {
                    "road_name":
                        "NH44 Highway Junction",
                    "density": 0.92,
                    "avg_speed": 8,
                    "vehicle_count": 340,
                    "has_accident": True,
                },
            ]

        recommendations = []

        for zone in traffic_zones:

            road = zone["road_name"]

            density = float(
                zone["density"] or 0
            )

            speed = float(
                zone["avg_speed"] or 0
            )

            vehicles = int(
                zone["vehicle_count"] or 0
            )

            accident = bool(
                zone["has_accident"]
            )

            if accident:

                severity = "HIGH"

                rec_text = (
                    f"Accident reported on "
                    f"{road}. Dispatch emergency "
                    "vehicle and route traffic "
                    "via alternative lane."
                )

            elif (
                density >= 0.75
                or vehicles > 200
                or speed < 15
            ):

                severity = "HIGH"

                rec_text = (
                    f"Heavy congestion "
                    f"({int(density * 100)}% density) "
                    f"on {road}. Reduce signal "
                    "green time by 20% or divert "
                    "traffic."
                )

            elif (
                density >= 0.40
                or speed < 30
            ):

                severity = "MODERATE"

                rec_text = (
                    f"Moderate traffic flow on "
                    f"{road}. Extend green signal "
                    "cycle by 15 seconds to ease "
                    "buildup."
                )

            else:

                severity = "LOW"

                rec_text = (
                    f"Optimal traffic conditions "
                    f"on {road}. Flow is moving "
                    f"smoothly at {speed} km/h."
                )

            recommendations.append(
                {
                    "road": road,
                    "severity": severity,
                    "recommendation":
                        rec_text,
                }
            )

        return recommendations

    except Exception as e:

        logger.exception(
            "Error generating recommendations: %s",
            e
        )

        return [
            {
                "road":
                    "Global Corridor Network",

                "severity":
                    "MODERATE",

                "recommendation":
                    "All regional nodes syncing "
                    "normally. Monitoring live "
                    "telemetry.",
            }
        ]


# ==========================================================
# ALERTS API
# ==========================================================

@app.get("/api/alerts")
def fetch_alerts_api(
    db: Session = Depends(get_db),
):

    try:

        alerts = (
            db.query(
                models.Alert
            )
            .order_by(
                models.Alert.created_at.desc()
            )
            .limit(20)
            .all()
        )

        if not alerts:

            return [
                {
                    "id": 0,
                    "alert_type":
                        "System Check",
                    "severity":
                        "Low",
                    "title":
                        "System Check",
                    "description":
                        "All signals running smoothly.",
                    "location":
                        "City-Wide",
                    "message":
                        "All signals running smoothly.",
                    "status":
                        "Active",
                    "created_at":
                        None,
                }
            ]

        return [

            {
                "id":
                    alert.id,

                "title":
                    alert.title,

                "description":
                    alert.description,

                "location":
                    alert.location,

                "alert_type":
                    alert.alert_type,

                "severity":
                    alert.severity,

                "message":
                    getattr(
                        alert,
                        "message",
                        None
                    ),

                "status":
                    alert.status,

                "created_at":
                    (
                        alert.created_at.isoformat()
                        if alert.created_at
                        else None
                    ),
            }

            for alert in alerts
        ]

    except Exception as e:

        logger.exception(
            "Alert fetch error: %s",
            e
        )

        return []


# ==========================================================
# ADMIN INCIDENTS API
# ==========================================================
#
# GET:
#     /api/incidents
#
# SECURITY:
#     Valid JWT token required
#     Admin role required
#
# FRONTEND MUST SEND:
#
# Authorization: Bearer <access_token>
#
# ==========================================================

@app.get("/api/incidents")
def fetch_incidents_api(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(admin_required),
):

    try:

        # --------------------------------------------------
        # VERIFY ADMIN
        # --------------------------------------------------

        role_value = getattr(
            current_user.role,
            "value",
            current_user.role
        )

        if str(role_value).strip().lower() != "admin":

            raise HTTPException(
                status_code=403,
                detail="Only Admin users can view incidents."
            )

        # --------------------------------------------------
        # FETCH ALERTS / INCIDENTS
        # --------------------------------------------------

        incidents = (
            db.query(
                models.Alert
            )
            .order_by(
                models.Alert.created_at.desc()
            )
            .limit(20)
            .all()
        )

        logger.info(
            "Admin '%s' requested incidents. Found %d incidents.",
            getattr(
                current_user,
                "username",
                "unknown"
            ),
            len(incidents)
        )

        # --------------------------------------------------
        # NO INCIDENTS
        # --------------------------------------------------

        if not incidents:

            return []

        # --------------------------------------------------
        # RETURN INCIDENTS
        # --------------------------------------------------

        return [

            {
                "id":
                    alert.id,

                "title":
                    alert.title,

                "description":
                    alert.description,

                "location":
                    alert.location,

                "alert_type":
                    alert.alert_type,

                "severity":
                    alert.severity,

                "message":
                    getattr(
                        alert,
                        "message",
                        None
                    ),

                "status":
                    alert.status,

                "created_at":
                    (
                        alert.created_at.isoformat()
                        if alert.created_at
                        else None
                    ),
            }

            for alert in incidents
        ]

    except HTTPException:
        raise

    except Exception as e:

        logger.exception(
            "Incident fetch error: %s",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch incidents"
        )


# ==========================================================
# RESOLVE ALERT
# ==========================================================

@app.post("/alerts/resolve/{alert_id}")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):

    alert = (
        db.query(
            models.Alert
        )
        .filter(
            models.Alert.id == alert_id
        )
        .first()
    )

    if not alert:

        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    alert.status = "Resolved"

    db.commit()

    return {
        "message":
            "Alert resolved"
    }


# ==========================================================
# CSV REPORT
# ==========================================================

@app.get("/reports/export/csv")
def export_csv(
    db: Session = Depends(get_db),
):

    logs = (
        db.query(
            models.VehicleCount
        )
        .all()
    )

    data = [

        {
            "ID":
                log.id,

            "Cars":
                log.cars,

            "Bikes":
                log.bikes,

            "Total":
                log.total,

            "Time":
                str(
                    log.detected_time
                ),
        }

        for log in logs
    ]

    if not data:

        data = [
            {
                "Status":
                    "No Log Records Available"
            }
        ]

    df = pd.DataFrame(data)

    csv_bytes = (
        df.to_csv(
            index=False
        )
        .encode("utf-8")
    )

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition":
                "attachment; "
                "filename=traffic_report.csv"
        },
    )


# ==========================================================
# LOGIN PAGE
# ==========================================================

@app.get(
    "/login",
    response_class=HTMLResponse
)
async def login_page(
    request: Request
):

    return render_template(
        "login.html",
        request,
        "Login | AI Traffic Control",
        "login",
    )


# ==========================================================
# REGISTER PAGE
# ==========================================================

@app.get(
    "/register",
    response_class=HTMLResponse
)
async def register_page(
    request: Request
):

    return render_template(
        "register.html",
        request,
        "Register | AI Traffic Control",
        "register",
    )


# ==========================================================
# DASHBOARD
# ==========================================================

@app.get(
    "/dashboard",
    response_class=HTMLResponse
)
@app.get(
    "/dashboard-page",
    response_class=HTMLResponse
)
async def dashboard_page(
    request: Request
):

    return render_template(
        "dashboard.html",
        request,
        "Dashboard | AI Traffic Management",
        "dashboard",
    )


# ==========================================================
# TRAFFIC GIS
# ==========================================================

@app.get(
    "/traffic-gis",
    response_class=HTMLResponse
)
@app.get(
    "/heatmap",
    response_class=HTMLResponse
)
async def heatmap_page(
    request: Request
):

    return render_template(
        "traffic-gis.html",
        request,
        "Traffic GIS & Heatmap",
        "heatmap",
    )


# ==========================================================
# ROUTE PLANNER
# ==========================================================

@app.get(
    "/route-planner",
    response_class=HTMLResponse
)
async def route_planner_page(
    request: Request
):

    return render_template(
        "map.html",
        request,
        "Route Planner",
        "route-planner",
    )


# ==========================================================
# HOTSPOTS
# ==========================================================

@app.get(
    "/hotspots",
    response_class=HTMLResponse
)
async def hotspots_page(
    request: Request
):

    return render_template(
        "hotspots.html",
        request,
        "Pan-India Hotspots",
        "hotspots",
    )


# ==========================================================
# ANALYTICS PAGE
# ==========================================================

@app.get(
    "/analytics",
    response_class=HTMLResponse
)
@app.get(
    "/analytics-page",
    response_class=HTMLResponse
)
async def analytics_page(
    request: Request
):

    return render_template(
        "analytics.html",
        request,
        "Traffic Analytics",
        "analytics",
    )


# ==========================================================
# REPORTS PAGE
# ==========================================================

@app.get(
    "/reports",
    response_class=HTMLResponse
)
@app.get(
    "/reports-page",
    response_class=HTMLResponse
)
async def reports_page(
    request: Request
):

    return render_template(
        "reports.html",
        request,
        "Traffic System Reports",
        "reports",
    )


# ==========================================================
# ALERTS PAGE
# ==========================================================

@app.get(
    "/alerts",
    response_class=HTMLResponse
)
async def alerts_page(
    request: Request
):

    return render_template(
        "alerts.html",
        request,
        "System Alerts",
        "alerts",
    )


# ==========================================================
# USERS PAGE
# ==========================================================

@app.get(
    "/users-page",
    response_class=HTMLResponse
)
async def users_page(
    request: Request
):

    return render_template(
        "users.html",
        request,
        "User Management",
        "users",
    )


# ==========================================================
# SETTINGS PAGE
# ==========================================================

@app.get(
    "/settings-page",
    response_class=HTMLResponse
)
async def settings_page(
    request: Request
):

    return render_template(
        "settings.html",
        request,
        "System Settings",
        "settings",
    )


# ==========================================================
# INCIDENTS PAGE
# ==========================================================
#
# PAGE:
#     http://127.0.0.1:8000/incidents
#
# DATA:
#     http://127.0.0.1:8000/api/incidents
#
# The PAGE itself is public.
#
# The DATA endpoint is ADMIN ONLY.
#
# ==========================================================

@app.get(
    "/incidents",
    response_class=HTMLResponse
)
@app.get(
    "/incident",
    response_class=HTMLResponse
)
async def incidents_page(
    request: Request
):

    return render_template(
        "incident.html",
        request,
        "Incidents | AI Traffic Management",
        "incidents",
    )


# ==========================================================
# HEALTH
# ==========================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "project": APP_NAME,
        "version": VERSION,
    }


# ==========================================================
# RUN DIRECTLY
# ==========================================================

if __name__ == "__main__":

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )