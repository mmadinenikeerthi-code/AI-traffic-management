/**
 * hotspots.js - Global Traffic Intelligence & Worldwide GIS Monitoring Engine
 * Manages Leaflet world maps, live data fetching from FastAPI, heatmaps, markers,
 * Chart.js analytics, real-time auto-refresh polling, and search routing.
 */

let hotspotsData = [];
let map, markersLayer, heatLayerGroup, tileLayer;
let showHeatmapFlag = true;
let showMarkersFlag = true;
let searchTimeout = null;

document.addEventListener("DOMContentLoaded", () => {
    initWorldMap();
    initAnalyticsCharts();
    setupEventListeners();
    
    // Start real-time telemetry polling interval (every 10 seconds)
    setInterval(() => {
        refreshDashboardData(false);
    }, 10000);
});

/**
 * Initialize Leaflet OpenStreetMap World View
 */
function initWorldMap() {
    map = L.map('map', {
        zoomControl: true,
        attributionControl: true
    }).setView([20.0, 0.0], 2); // Global world view default

    tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    markersLayer = L.layerGroup().addTo(map);
    
    // Initial fetch from FastAPI endpoints
    fetchAllData();
}

/**
 * Fetch world hotspots and top-level stats from backend routers
 */
async function fetchAllData() {
    try {
        const [worldRes, statsRes] = await Promise.all([
            fetch('/hotspots/world'),
            fetch('/hotspots/stats').catch(() => null)
        ]);

        if (worldRes.ok) {
            hotspotsData = await worldRes.json();
            renderMapMarkers(hotspotsData);
            renderTopHotspotsSidebar(hotspotsData);
            renderAIRecommendations(hotspotsData);
        }

        if (statsRes && statsRes.ok) {
            const stats = await statsRes.json();
            updateKPICards(stats);
        }
    } catch (error) {
        console.warn("Backend API unreachable. Falling back to local live-sim telemetry model.", error);
        loadFallbackTelemetry();
    }
}

/**
 * Update top KPI header cards with real telemetry
 */
function updateKPICards(stats) {
    if (stats.countries_monitored) document.getElementById('kpi-countries').innerText = stats.countries_monitored;
    if (stats.live_vehicles) document.getElementById('kpi-vehicles').innerText = stats.live_vehicles.toLocaleString();
    if (stats.congested_cities) document.getElementById('kpi-cities').innerText = stats.congested_cities;
    if (stats.active_incidents) document.getElementById('kpi-incidents').innerText = stats.active_incidents;
    if (stats.ai_predictions) document.getElementById('kpi-predictions').innerText = stats.ai_predictions;
    document.getElementById('kpi-updated').innerText = "Just now";
}

/**
 * Render color-coded markers and heatmap overlay on the world map
 */
function renderMapMarkers(data) {
    if (!markersLayer) return;
    markersLayer.clearLayers();
    let heatPoints = [];

    data.forEach(item => {
        let intensity = item.congestion === 'Severe' ? 1.0 : item.congestion === 'High' ? 0.8 : item.congestion === 'Moderate' ? 0.5 : 0.2;
        heatPoints.push([item.lat, item.lng, intensity]);

        if (showMarkersFlag) {
            let colorHex = getCongestionColorHex(item.congestion);
            let customIcon = L.divIcon({
                className: 'custom-traffic-pin',
                html: `<div style="background-color: ${colorHex}; width: 16px; height: 16px; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 10px ${colorHex};"></div>`,
                iconSize: [16, 16],
                iconAnchor: [8, 8]
            });

            let marker = L.marker([item.lat, item.lng], { icon: customIcon });
            marker.bindPopup(`
                <div style="color:#0f172a; font-family:sans-serif; font-size:0.9rem; line-height: 1.4;">
                    <strong>📍 ${item.road}</strong><br>
                    Region: ${item.city}, ${item.country}<br>
                    Live Vehicles: <strong>${item.vehicles}</strong><br>
                    Speed: <strong>${item.speed}</strong><br>
                    Status: <span style="color:${colorHex}; font-weight:bold; text-transform:uppercase;">${item.congestion}</span><br>
                    <em>AI Action: ${item.action}</em>
                </div>
            `);
            markersLayer.addLayer(marker);
        }
    });

    if (heatLayerGroup) map.removeLayer(heatLayerGroup);
    heatLayerGroup = L.heatLayer(heatPoints, { radius: 25, blur: 15, maxZoom: 17 });
    if (showHeatmapFlag) heatLayerGroup.addTo(map);
}

function getCongestionColorHex(level) {
    if (level === 'Severe') return '#ef4444';
    if (level === 'High') return '#f97316';
    if (level === 'Moderate') return '#f59e0b';
    return '#10b981';
}

/**
 * Populate Top Traffic Hotspots right sidebar
 */
function renderTopHotspotsSidebar(data) {
    const container = document.getElementById('topHotspotsContainer');
    if (!container) return;
    container.innerHTML = '';

    // Sort by vehicle density/congestion severity
    const sorted = [...data].sort((a, b) => b.vehicles - a.vehicles);

    sorted.slice(0, 6).forEach((item, index) => {
        let badgeClass = item.congestion.toLowerCase();
        let div = document.createElement('div');
        div.className = 'hotspot-list-item';
        div.onclick = () => {
            map.setView([item.lat, item.lng], 14);
        };
        div.innerHTML = `
            <div class="hotspot-header">
                <span>${index + 1}. ${item.road}</span>
                <span class="badge ${badgeClass}">${item.congestion}</span>
            </div>
            <div style="color:var(--text-muted);">${item.city}, ${item.country} • ${item.vehicles} vehicles</div>
        `;
        container.appendChild(div);
    });
}

/**
 * Populate AI Recommendations right sidebar
 */
function renderAIRecommendations(data) {
    const container = document.getElementById('aiRecommendationsContainer');
    if (!container) return;
    container.innerHTML = '';

    data.slice(0, 5).forEach(item => {
        let cardClass = item.congestion === 'Severe' ? '' : item.congestion === 'High' ? 'orange' : 'warning';
        let div = document.createElement('div');
        div.className = `rec-card ${cardClass}`;
        div.innerHTML = `
            <div style="font-weight:700;">📍 ${item.road}, ${item.city}</div>
            <div>Action: <strong>${item.action}</strong></div>
            <div style="font-size:0.75rem; color:var(--text-muted);">AI Confidence: 94% • Level: ${item.congestion}</div>
        `;
        container.appendChild(div);
    });
}

/**
 * Global Search and Nominatim Live Autocomplete Integration
 */
function setupEventListeners() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
        let query = e.target.value.trim();
        let box = document.getElementById('searchResultsBox');
        if (!box) return;

        if (query.length < 2) {
            box.style.display = 'none';
            return;
        }

        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(async () => {
            try {
                let res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`);
                let results = await res.json();
                
                box.innerHTML = '';
                if (results && results.length > 0) {
                    box.style.display = 'block';
                    results.forEach(loc => {
                        let item = document.createElement('div');
                        item.className = 'search-result-item';
                        item.innerText = loc.display_name;
                        item.onclick = () => {
                            searchInput.value = loc.display_name;
                            box.style.display = 'none';
                            map.setView([parseFloat(loc.lat), parseFloat(loc.lon)], 13);
                        };
                        box.appendChild(item);
                    });
                } else {
                    box.style.display = 'none';
                }
            } catch (err) {
                console.error("Nominatim geocoding error:", err);
            }
        }, 350);
    });
}

async function handleWorldSearch() {
    let query = document.getElementById('searchInput').value.trim();
    if (!query) return;
    let box = document.getElementById('searchResultsBox');
    if (box) box.style.display = 'none';

    try {
        let res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`);
        let data = await res.json();
        if (data && data.length > 0) {
            map.setView([parseFloat(data[0].lat), parseFloat(data[0].lon)], 13);
        } else {
            alert("Location not found in global directory.");
        }
    } catch (e) {
        alert("Search service connection error.");
    }
}

/**
 * Filtering controls by Country and Congestion level
 */
function applyFilters() {
    let countryVal = document.getElementById('countryFilter').value;
    let congestionVal = document.getElementById('congestionFilter').value;

    let filtered = hotspotsData.filter(item => {
        let matchCountry = (countryVal === 'all' || item.country === countryVal);
        let matchCongestion = (congestionVal === 'all' || item.congestion === congestionVal);
        return matchCountry && matchCongestion;
    });

    renderMapMarkers(filtered);
}

/**
 * Map Layer switcher (Street, Satellite, Terrain)
 */
function changeMapLayer(layerType) {
    if (!tileLayer) return;
    if (layerType === 'satellite') {
        tileLayer.setUrl('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}');
    } else if (layerType === 'terrain') {
        tileLayer.setUrl('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png');
    } else {
        tileLayer.setUrl('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png');
    }
}

function toggleHeatmap() {
    showHeatmapFlag = !showHeatmapFlag;
    let btn = document.getElementById('btn-heatmap');
    if (showHeatmapFlag) {
        btn.classList.add('active');
        heatLayerGroup.addTo(map);
    } else {
        btn.classList.remove('active');
        map.removeLayer(heatLayerGroup);
    }
}

function toggleMarkers() {
    showMarkersFlag = !showMarkersFlag;
    let btn = document.getElementById('btn-marker');
    if (showMarkersFlag) btn.classList.add('active');
    else btn.classList.remove('active');
    renderMapMarkers(hotspotsData);
}

function triggerRefresh() {
    let btn = document.getElementById('btn-refresh');
    btn.innerText = '⏳ Syncing...';
    setTimeout(() => {
        btn.innerText = '🔄 Refresh';
        refreshDashboardData(true);
    }, 600);
}

async function refreshDashboardData(showAlert = false) {
    await fetchAllData();
    if (showAlert) {
        document.getElementById('kpi-updated').innerText = "Just now";
    }
}

/**
 * Initialize Chart.js analytics graphs
 */
function initAnalyticsCharts() {
    const ctx1 = document.getElementById('vehicleTrendChart');
    if (ctx1) {
        new Chart(ctx1.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                datasets: [{
                    label: 'Global Fleet Count',
                    data: [12000, 9500, 24000, 28000, 31000, 25340],
                    borderColor: '#3b82f6',
                    tension: 0.4,
                    fill: true,
                    backgroundColor: 'rgba(59,130,246,0.1)'
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
    }

    const ctx2 = document.getElementById('fleetDistChart');
    if (ctx2) {
        new Chart(ctx2.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Cars', 'Bikes', 'Buses', 'Trucks', 'Emergency'],
                datasets: [{
                    data: [14210, 5120, 1840, 3450, 120],
                    backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#f97316', '#ef4444']
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, color: '#94a3b8' } } } }
        });
    }
}