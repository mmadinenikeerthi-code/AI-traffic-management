from fastapi import APIRouter
from datetime import datetime
import random

router = APIRouter(
    prefix="/hotspots",
    tags=["Global Hotspots"]
)

# Global dataset pool spanning major worldwide cities & coordinates
GLOBAL_HOTSPOTS_DB = [
    {"id": 1, "country": "USA", "city": "New York", "road": "Times Square", "lat": 40.7580, "lng": -73.9855, "base_count": 450},
    {"id": 2, "country": "USA", "city": "Los Angeles", "road": "I-405 Freeway Corridor", "lat": 34.0522, "lng": -118.2437, "base_count": 580},
    {"id": 3, "country": "USA", "city": "Chicago", "road": "The Loop Interchange", "lat": 41.8781, "lng": -87.6298, "base_count": 320},
    {"id": 4, "country": "Canada", "city": "Toronto", "road": "Gardiner Expressway", "lat": 43.6532, "lng": -79.3832, "base_count": 240},
    {"id": 5, "country": "Mexico", "city": "Mexico City", "road": "Paseo de la Reforma", "lat": 19.4326, "lng": -99.1332, "base_count": 490},
    {"id": 6, "country": "Japan", "city": "Tokyo", "road": "Shibuya Crossing", "lat": 35.6595, "lng": 139.7004, "base_count": 380},
    {"id": 7, "country": "Japan", "city": "Osaka", "road": "Midosuji Boulevard", "lat": 34.6937, "lng": 135.5022, "base_count": 200},
    {"id": 8, "country": "India", "city": "Bengaluru", "road": "MG Road", "lat": 12.9750, "lng": 77.6050, "base_count": 210},
    {"id": 9, "country": "India", "city": "Mumbai", "road": "Western Express Highway", "lat": 19.0760, "lng": 72.8777, "base_count": 530},
    {"id": 10, "country": "India", "city": "New Delhi", "road": "Connaught Place Ring", "lat": 28.6139, "lng": 77.2090, "base_count": 470},
    {"id": 11, "country": "China", "city": "Shanghai", "road": "Yan'an Elevated Road", "lat": 31.2304, "lng": 121.4737, "base_count": 440},
    {"id": 12, "country": "China", "city": "Beijing", "road": "3rd Ring Road", "lat": 39.9042, "lng": 116.4074, "base_count": 560},
    {"id": 13, "country": "Singapore", "city": "Singapore", "road": "Orchard Road", "lat": 1.3521, "lng": 103.8198, "base_count": 120},
    {"id": 14, "country": "South Korea", "city": "Seoul", "road": "Teheran-ro", "lat": 37.5665, "lng": 126.9780, "base_count": 300},
    {"id": 15, "country": "Australia", "city": "Sydney", "road": "Sydney Harbour Bridge Approach", "lat": -33.8688, "lng": 151.2093, "base_count": 185},
    {"id": 16, "country": "Australia", "city": "Melbourne", "road": "Flinders Street Junction", "lat": -37.8136, "lng": 144.9631, "base_count": 140},
    {"id": 17, "country": "UK", "city": "London", "road": "Oxford Circus", "lat": 51.5150, "lng": -0.1410, "base_count": 175},
    {"id": 18, "country": "UK", "city": "Manchester", "road": "M60 Ring Motorway", "lat": 53.4808, "lng": -2.2426, "base_count": 280},
    {"id": 19, "country": "France", "city": "Paris", "road": "Champs-Élysées", "lat": 48.8698, "lng": 2.3075, "base_count": 305},
    {"id": 20, "country": "Germany", "city": "Berlin", "road": "Alexanderplatz", "lat": 52.5219, "lng": 13.4132, "base_count": 255},
    {"id": 21, "country": "Germany", "city": "Frankfurt", "road": "A5 Autobahn Interchange", "lat": 50.1109, "lng": 8.6821, "base_count": 420},
    {"id": 22, "country": "Italy", "city": "Rome", "road": "Via del Corso Corridor", "lat": 41.9028, "lng": 12.4964, "base_count": 220},
    {"id": 23, "country": "Spain", "city": "Madrid", "road": "Paseo de la Castellana", "lat": 40.4168, "lng": -3.7038, "base_count": 195},
    {"id": 24, "country": "Netherlands", "city": "Amsterdam", "road": "A10 Ring Road", "lat": 52.3676, "lng": 4.9041, "base_count": 165},
    {"id": 25, "country": "Brazil", "city": "São Paulo", "road": "Avenida Paulista", "lat": -23.5505, "lng": -46.6333, "base_count": 510},
    {"id": 26, "country": "Brazil", "city": "Rio de Janeiro", "road": "Avenida Atlântica", "lat": -22.9068, "lng": -43.1729, "base_count": 295},
    {"id": 27, "country": "Argentina", "city": "Buenos Aires", "road": "Avenida 9 de Julio", "lat": -34.6037, "lng": -58.3816, "base_count": 370},
    {"id": 28, "country": "UAE", "city": "Dubai", "road": "Sheikh Zayed Road", "lat": 25.2048, "lng": 55.2708, "base_count": 410},
    {"id": 29, "country": "South Africa", "city": "Johannesburg", "road": "M1 Highway Corridor", "lat": -26.2041, "lng": 28.0473, "base_count": 350}
]

@router.get("/")
def read_root():
    return {
        "status": "online",
        "system": "Global Traffic Intelligence & YOLOv8 Engine",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@router.get("/world")
def get_global_hotspots():
    """
    Generates live, real-time fluctuating traffic metrics for worldwide hotspots.
    Simulates continuous YOLOv8 frame-by-frame inference count variations.
    """
    live_hotspots = []
    
    for item in GLOBAL_HOTSPOTS_DB:
        # Introduce dynamic live fluctuations to simulate real video stream feeds
        flux = random.randint(-25, 30)
        current_vehicles = max(50, item["base_count"] + flux)
        
        # Calculate dynamic speed and congestion based on live vehicle volume
        if current_vehicles > 450:
            congestion = "Severe"
            speed = f"{random.randint(10, 15)} km/h"
            action = "Reroute traffic & reduce green signal phase"
        elif current_vehicles > 320:
            congestion = "High"
            speed = f"{random.randint(16, 23)} km/h"
            action = "Extend green wave timing by 20 sec"
        elif current_vehicles > 180:
            congestion = "Moderate"
            speed = f"{random.randint(24, 35)} km/h"
            action = "Maintain adaptive light phasing"
        else:
            congestion = "Low"
            speed = f"{random.randint(36, 60)} km/h"
            action = "Optimal flow, standard monitoring"

        live_hotspots.append({
            "id": item["id"],
            "country": item["country"],
            "city": item["city"],
            "road": item["road"],
            "lat": item["lat"],
            "lng": item["lng"],
            "congestion": congestion,
            "vehicles": current_vehicles,
            "speed": speed,
            "action": action
        })
        
    return live_hotspots

@router.get("/stats")
def get_global_stats():
    """Returns top-level aggregate KPI numbers with live real-time variations."""
    total_vehicles = random.randint(24800, 26200)
    congested_count = random.randint(45, 52)
    incidents_count = random.randint(12, 18)
    
    return {
        "countries_monitored": 120,
        "live_vehicles": total_vehicles,
        "congested_cities": congested_count,
        "active_incidents": incidents_count,
        "ai_predictions": 39
    }