from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
import requests

router = APIRouter(prefix="/osm", tags=["OpenStreetMap Routing"])

ROUTE_COLORS = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c"]

@router.get("/calculate-route")
def calculate_route(
    origin_lat: float = Query(..., description="Origin Latitude"),
    origin_lon: float = Query(..., description="Origin Longitude"),
    dest_lat: float = Query(..., description="Destination Latitude"),
    dest_lon: float = Query(..., description="Destination Longitude")
):
    """Calculates alternative routes with geometry, distance, and duration."""
    osrm_url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        f"?overview=full&geometries=geojson&alternatives=true"
    )

    try:
        response = requests.get(osrm_url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OSRM Routing Service Error: {str(e)}")

    if "routes" not in data or len(data["routes"]) == 0:
        raise HTTPException(status_code=404, detail="No routes found between selected locations")

    routes_data = []
    for idx, route in enumerate(data["routes"]):
        dist_km = round(route["distance"] / 1000, 2)
        total_minutes = int(round(route["duration"] / 60))
        hours = total_minutes // 60
        mins = total_minutes % 60
        
        time_str = f"{hours} hr {mins} min" if hours > 0 else f"{mins} min"

        routes_data.append({
            "id": idx,
            "name": f"Route {idx + 1}" + (" (Fastest)" if idx == 0 else " (Alternative)"),
            "distance_km": dist_km,
            "duration_minutes": total_minutes,
            "time_formatted": time_str,
            "color": ROUTE_COLORS[idx % len(ROUTE_COLORS)],
            "geometry": route["geometry"]
        })

    return {
        "status": "success",
        "total_routes": len(routes_data),
        "routes": routes_data
    }

@router.get("/map", response_class=HTMLResponse)
def get_map_view(dashboard_url: str = "/dashboard"):
    """Serves Google Maps-style UI with route selection, ETA, distance, and alternative paths."""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>World Map & Route Planner</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ display: flex; height: 100vh; overflow: hidden; }}
            
            /* Sidebar Controls */
            #sidebar {{
                width: 380px;
                background: #ffffff;
                box-shadow: 2px 0 10px rgba(0,0,0,0.15);
                display: flex;
                flex-direction: column;
                z-index: 1000;
            }}
            .header {{
                padding: 16px;
                background: #1e293b;
                color: white;
            }}
            .btn-back {{
                display: inline-block;
                color: #38bdf8;
                text-decoration: none;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
            .btn-back:hover {{ text-decoration: underline; }}
            .input-group {{
                padding: 16px;
                display: flex;
                flex-direction: column;
                gap: 10px;
                border-bottom: 1px solid #e2e8f0;
            }}
            .input-box {{
                display: flex;
                flex-direction: column;
                gap: 4px;
            }}
            .input-box label {{ font-size: 12px; font-weight: bold; color: #64748b; }}
            .input-box input {{
                padding: 10px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 14px;
            }}
            .btn-search {{
                background: #2563eb;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                cursor: pointer;
                transition: background 0.2s;
            }}
            .btn-search:hover {{ background: #1d4ed8; }}
            
            /* Route Cards */
            #route-list {{
                flex: 1;
                overflow-y: auto;
                padding: 16px;
            }}
            .route-card {{
                padding: 14px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-bottom: 12px;
                cursor: pointer;
                transition: all 0.2s;
                background: #f8fafc;
            }}
            .route-card:hover {{ border-color: #94a3b8; }}
            .route-card.selected {{
                border-color: #2563eb;
                background: #eff6ff;
                box-shadow: 0 2px 8px rgba(37,99,235,0.15);
            }}
            .route-title {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-weight: bold;
                font-size: 16px;
                color: #1e293b;
            }}
            .route-meta {{
                margin-top: 6px;
                font-size: 14px;
                color: #475569;
            }}
            .badge-color {{
                width: 12px;
                height: 12px;
                border-radius: 50%;
                display: inline-block;
            }}

            /* Map Area */
            #map {{ flex: 1; height: 100%; }}
        </style>
    </head>
    <body>

        <div id="sidebar">
            <div class="header">
                <a href="{dashboard_url}" class="btn-back">← Back to Dashboard</a>
                <h2>World Route Finder</h2>
            </div>
            
            <div class="input-group">
                <div class="input-box">
                    <label>ORIGIN</label>
                    <input type="text" id="origin" value="Mumbai" placeholder="Enter city or address...">
                </div>
                <div class="input-box">
                    <label>DESTINATION</label>
                    <input type="text" id="destination" value="Pune" placeholder="Enter city or address...">
                </div>
                <button class="btn-search" onclick="calculateRoutes()">Find Routes</button>
            </div>

            <div id="route-list">
                <p style="color: #64748b;">Enter origin and destination to search routes.</p>
            </div>
        </div>

        <div id="map"></div>

        <script>
            // Initialize Leaflet Map
            const map = L.map('map').setView([19.0760, 72.8777], 8);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);

            let routeLayers = [];
            let markerGroup = L.layerGroup().addTo(map);
            let globalRoutes = [];
            let selectedRouteId = 0;

            async function geocode(query) {{
                const res = await fetch(https://nominatim.openstreetmap.org/search?format=json&q=${{encodeURIComponent(query)}});
                const data = await res.json();
                if (data.length === 0) throw new Error(Location not found: ${{query}});
                return {{ lat: parseFloat(data[0].lat), lon: parseFloat(data[0].lon), name: data[0].display_name }};
            }}

            async function calculateRoutes() {{
                const originInput = document.getElementById('origin').value;
                const destInput = document.getElementById('destination').value;
                const routeListDiv = document.getElementById('route-list');

                routeListDiv.innerHTML = "<p>Searching locations and routes...</p>";

                try {{
                    const origin = await geocode(originInput);
                    const dest = await geocode(destInput);

                    const res = await fetch(/osm/calculate-route?origin_lat=${{origin.lat}}&origin_lon=${{origin.lon}}&dest_lat=${{dest.lat}}&dest_lon=${{dest.lon}});
                    const data = await res.json();

                    if (data.status !== 'success') throw new Error("Could not calculate routes.");

                    globalRoutes = data.routes;
                    selectedRouteId = 0;

                    // Render Markers
                    markerGroup.clearLayers();
                    L.marker([origin.lat, origin.lon]).addTo(markerGroup).bindPopup("<b>Origin:</b> " + origin.name);
                    L.marker([dest.lat, dest.lon]).addTo(markerGroup).bindPopup("<b>Destination:</b> " + dest.name);

                    renderMapAndCards();

                }} catch (err) {{
                    routeListDiv.innerHTML = <p style="color: red;">${{err.message}}</p>;
                }}
            }}

            function renderMapAndCards() {{
                const routeListDiv = document.getElementById('route-list');
                routeListDiv.innerHTML = '';

                // Clear existing route polylines
                routeLayers.forEach(layer => map.removeLayer(layer));
                routeLayers = [];

                let allBounds = [];

                globalRoutes.forEach((route, index) => {{
                    const isSelected = (route.id === selectedRouteId);
                    
                    // Render UI Card
                    const card = document.createElement('div');
                    card.className = route-card ${{isSelected ? 'selected' : ''}};
                    card.onclick = () => selectRoute(route.id);
                    card.innerHTML = `
                        <div class="route-title">
                            <span>${{route.name}}</span>
                            <span class="badge-color" style="background-color: ${{route.color}};"></span>
                        </div>
                        <div class="route-meta">
                            <strong>⏱️ ${{route.time_formatted}}</strong> (${{route.distance_km}} km)
                        </div>
                    `;
                    routeListDiv.appendChild(card);

                    // Render Map Polyline
                    const polyline = L.geoJSON(route.geometry, {{
                        style: {{
                            color: isSelected ? '#2563eb' : route.color,
                            weight: isSelected ? 8 : 4,
                            opacity: isSelected ? 0.9 : 0.4
                        }}
                    }}).addTo(map);

                    polyline.on('click', () => selectRoute(route.id));
                    routeLayers.push(polyline);
                    allBounds.push(polyline.getBounds());
                }});

                if (allBounds.length > 0) {{
                    map.fitBounds(allBounds[0]);
                }}
            }}

            function selectRoute(id) {{
                selectedRouteId = id;
                renderMapAndCards();
            }}

            // Auto-load initial route search on startup
            window.onload = () => {{ calculateRoutes(); }};
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)