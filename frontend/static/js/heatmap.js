// ==========================================================
// frontend/static/js/heatmap.js
// Leaflet.js Interactive GIS Heatmap, Routing & Pan-India Search
// ==========================================================

let mapInstance = null;
let heatmapLayerGroup = null;
let routingControl = null;

/**
 * Initializes the Leaflet Map
 */
function initTrafficHeatmap(containerId = 'map') {
    const mapElement = document.getElementById(containerId);
    if (!mapElement) return;

    if (!mapInstance) {
        // Default center: India (Central coordinates to support Pan-India view)
        mapInstance = L.map(containerId).setView([20.5937, 78.9629], 5);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }).addTo(mapInstance);

        heatmapLayerGroup = L.layerGroup().addTo(mapInstance);
    }

    loadHeatmapData();
}

/**
 * Fetches Heatmap Points from API (Supports Search & Location Focus)
 */
async function loadHeatmapData() {
    if (!mapInstance || !heatmapLayerGroup) return;

    // 1. Read URL Parameters for Pan-India Search and Specific Location Focus
    const urlParams = new URLSearchParams(window.location.search);
    const targetLocationId = urlParams.get('location');
    const searchQuery = urlParams.get('search');

    // 2. Build the API URL dynamically
    let fetchUrl = '/heatmap/points';
    if (searchQuery) {
        fetchUrl += `?search=${encodeURIComponent(searchQuery)}`;
    }

    try {
        const res = await fetch(fetchUrl);
        const points = await res.json();

        // Clear existing map circles before drawing new ones
        heatmapLayerGroup.clearLayers();

        let targetPoint = null;

        points.forEach(pt => {
            // Generate ID if missing
            const ptId = pt.id || pt.road.replace(/\s+/g, '');

            // Check if this point is the one requested in ?location=
            if (targetLocationId) {
                const isTarget = (ptId.toLowerCase() === targetLocationId.toLowerCase()) || 
                                 (pt.road.toLowerCase().includes(targetLocationId.toLowerCase()));
                if (isTarget) {
                    targetPoint = pt;
                }
            }

            // Determine Congestion Overlay Color
            const levelUpper = (pt.level || '').toUpperCase();
            const color = (levelUpper === 'HEAVY' || pt.intensity >= 0.8) ? '#dc3545' :
                          (levelUpper === 'MEDIUM' || pt.intensity >= 0.5) ? '#ffc107' : '#198754';

            // Draw Heatmap Circles (Size adjusted for national vs local view)
            const circle = L.circle([pt.lat, pt.lng], {
                color: color,
                fillColor: color,
                fillOpacity: 0.6,
                radius: 1800 // meters
            });

            // Create informative popup with Focus Link
            const popupText = `
                <div style="font-family: Arial, sans-serif; min-width: 180px;">
                    <h6 style="margin: 0 0 5px 0;"><b>${pt.road}</b></h6>
                    <hr style="margin: 4px 0;">
                    <b>Status:</b> <span style="color:${color}; font-weight:bold;">${levelUpper}</span><br>
                    <b>Vehicles:</b> ${pt.vehicle_count || 0}<br>
                    <b>Accidents:</b> ${pt.accidents > 0 ? `<span class="text-danger fw-bold">${pt.accidents} ⚠️</span>` : '0'}<br>
                    <div style="margin-top: 10px;">
                        <a href="/heatmap?location=${ptId}" style="font-weight:bold; color: #0d6efd; text-decoration: none;">
                            🎯 Focus Statistics
                        </a>
                    </div>
                </div>
            `;

            circle.bindPopup(popupText);
            heatmapLayerGroup.addLayer(circle);
        });

        // 3. Map Camera & Side Panel Update Logic
        if (targetPoint) {
            // If user clicked a specific hotspot focus
            mapInstance.flyTo([targetPoint.lat, targetPoint.lng], 13);
            updateSidePanelStats(targetPoint);
        } else if (points.length > 0) {
            if (searchQuery) {
                // If user searched a state/city, zoom to the first result of that state
                mapInstance.flyTo([points[0].lat, points[0].lng], 11);
            } else if (!searchQuery && !targetLocationId) {
                // Default view: Zoom out to see Pan-India
                mapInstance.setView([20.5937, 78.9629], 5); 
            }
            // Update stats panel with the highest priority point in view
            updateSidePanelStats(points[0]);
        } else {
            console.warn("No traffic data found for this search/location.");
        }

    } catch (err) {
        console.error("Failed to load GIS Heatmap points:", err);
    }
}

/**
 * Updates the Right-Side Panel with Live Junction Statistics & AI
 */
function updateSidePanelStats(pt) {
    const title = document.getElementById('selected-location-title');
    const level = document.getElementById('selected-level');
    const vehicles = document.getElementById('selected-vehicles');
    const speed = document.getElementById('selected-speed');
    const congestion = document.getElementById('selected-congestion');
    const recommendation = document.getElementById('selected-recommendation');

    if (title) title.innerText = pt.road;
    if (vehicles) vehicles.innerText = pt.vehicle_count || 0;
    if (speed) speed.innerText = pt.speed || 'N/A';

    const densityPct = pt.intensity ? Math.round(pt.intensity * 100) : 0;
    if (congestion) congestion.innerText = `${densityPct}%`;

    if (level) {
        const levelUpper = (pt.level || 'LOW').toUpperCase();
        level.innerText = levelUpper;
        level.className = `badge fs-6 px-3 py-1 ${levelUpper === 'HEAVY' ? 'bg-danger' : levelUpper === 'MEDIUM' ? 'bg-warning text-dark' : 'bg-success'}`;
    }

    if (recommendation) {
        recommendation.innerText = pt.recommendation || 'Maintain normal traffic flow. Standard signal cycle active.';
    }
}

/**
 * Calculates Route between Source and Destination Dropdowns
 */
function calculateRoute() {
    if (!mapInstance) return;

    const sourceSelect = document.getElementById('sourceSelect');
    const destSelect = document.getElementById('destSelect');

    if (!sourceSelect || !destSelect) return;

    const sourceVal = sourceSelect.value.split(',');
    const destVal = destSelect.value.split(',');

    const srcLat = parseFloat(sourceVal[0]);
    const srcLng = parseFloat(sourceVal[1]);
    const destLat = parseFloat(destVal[0]);
    const destLng = parseFloat(destVal[1]);

    // Remove existing route line if one exists
    if (routingControl) {
        mapInstance.removeControl(routingControl);
    }

    // Initialize Leaflet Routing Machine
    routingControl = L.Routing.control({
        waypoints: [
            L.latLng(srcLat, srcLng),
            L.latLng(destLat, destLng)
        ],
        routeWhileDragging: false,
        addWaypoints: false,
        showAlternatives: false,
        fitSelectedRoutes: true,
        lineOptions: {
            styles: [{ color: '#0d6efd', opacity: 0.8, weight: 6 }]
        },
        createMarker: function() { return null; } // Hide default markers to keep map clean
    }).addTo(mapInstance);

    // Extract distance and time once route is calculated
    routingControl.on('routesfound', function(e) {
        const routes = e.routes;
        const summary = routes[0].summary;
        
        // Convert distance to km and time to minutes
        const distanceKm = (summary.totalDistance / 1000).toFixed(2);
        const timeMin = Math.round(summary.totalTime / 60);

        const distEl = document.getElementById('routeDistance');
        const timeEl = document.getElementById('routeTime');

        if(distEl) distEl.innerText = `${distanceKm} km`;
        if(timeEl) timeEl.innerText = `${timeMin} min`;
    });
}

// Auto-initialize when the DOM is fully loaded
document.addEventListener("DOMContentLoaded", () => {
    initTrafficHeatmap('map');
});

