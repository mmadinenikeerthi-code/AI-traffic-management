import random
from datetime import datetime

def generate_ai_recommendations(vehicle_count: int, emergency_count: int, avg_speed: float):
    """
    Generates rule/AI-based traffic control recommendations based on incoming metrics.
    """
    recommendations = []
    
    if emergency_count > 0:
        recommendations.append({
            "priority": "CRITICAL",
            "action": "Clear Emergency Corridor",
            "details": f"Override traffic signals on Route A. Priority green for {emergency_count} emergency vehicle(s)."
        })
        
    if vehicle_count > 40 and avg_speed < 20.0:
        recommendations.append({
            "priority": "HIGH",
            "action": "Extend Green Light Duration",
            "details": "Severe bottleneck detected. Increase signal cycle by 15 seconds on main junction."
        })
    elif vehicle_count > 25:
        recommendations.append({
            "priority": "MEDIUM",
            "action": "Reroute Incoming Traffic",
            "details": "Divert secondary traffic to Bypass Route B via digital VMS boards."
        })
    else:
        recommendations.append({
            "priority": "LOW",
            "action": "Maintain Standard Signal Cycle",
            "details": "Traffic flow is optimal. No active interventions required."
        })
        
    return recommendations

def get_heatmap_coordinates():
    """
    Generates sample GPS traffic intensity data for Leaflet.js heatmap visualization.
    Format: [latitude, longitude, intensity]
    """
    # Sample center coordinates (e.g., city intersection)
    base_lat, base_lng = 15.8281, 78.0373  
    points = []
    
    for _ in range(30):
        lat_offset = (random.random() - 0.5) * 0.02
        lng_offset = (random.random() - 0.5) * 0.02
        intensity = round(random.uniform(0.3, 1.0), 2)
        points.append([base_lat + lat_offset, base_lng + lng_offset, intensity])
        
    return points