// ==========================================================
// static/js/dashboard.js - PART 1
// AI Traffic Management System - Complete Milestone 3 Engine
// ==========================================================

// Global Chart & Map References
window.trafficChart = window.trafficChart || null;
window.pieChart = window.pieChart || null;
window.leafletMap = window.leafletMap || null;
window.heatLayer = window.heatLayer || null;
window.dashboardInterval = window.dashboardInterval || null;

/**
 * Main Initialization Function
 * Called on DOM Load or when clicking the "Refresh Dashboard" button
 */
function initializeDashboard() {
    clearError();

    // 1. Fetch YOLO live frame data (Existing functionality)
    fetchDashboardData();

    // 2. Fetch Milestone 3 API Endpoints
    fetchAlerts();
    fetchKPIs();
    fetchTrafficTrends();
    fetchTrafficStatus();
    loadHeatmap();

    // 3. Set up automated interval timers if not already active
    if (!window.dashboardInterval) {
        // Fast updates (every 5 seconds) for live counts, KPIs, and alerts
        window.dashboardInterval = setInterval(() => {
            fetchDashboardData();
            fetchAlerts();
            fetchKPIs();
            fetchTrafficStatus();
        }, 5000);

        // Slow updates (every 30 seconds) for heatmaps and historical trend charts
        setInterval(() => {
            fetchTrafficTrends();
            loadHeatmap();
        }, 30000);
    }
}

// ----------------------------------------------------------
// 1. YOLO LIVE DASHBOARD FETCH ENGINE (GET /detect/live-dashboard)
// ----------------------------------------------------------
async function fetchDashboardData() {
    try {
        const response = await fetch("/detect/live-dashboard");
        if (!response.ok) throw new Error("Failed to fetch live YOLO dashboard data");

        const data = await response.json();

        // Update counts across UI
        updateDOMText("totalVehicles", data.total_vehicles || 0);
        updateDOMText("cars", data.cars || 0);
        updateDOMText("bikes", data.bikes || 0);
        updateDOMText("buses", data.buses || 0);
        updateDOMText("trucks", data.trucks || 0);
        updateDOMText("autos", data.autos || 0);
        updateDOMText("ambulances", data.ambulances || 0);
        updateDOMText("ambulanceCount", data.ambulances || 0);

        // Update Congestion & Speed
        updateDOMText("congestionLevel", data.congestion_level || "LOW");
        updateDOMText("currentLevel", data.congestion_level || "LOW");
        updateDOMText("speed", `${data.avg_speed || 0} km/h`);
        updateDOMText("density", `${data.density_percentage || 0}%`);
        updateDOMText("roadUsage", `${data.density_percentage || 0}%`);

        // Update Emergency status panel
        const emergencyPanel = document.getElementById("emergencyPanel");
        if (emergencyPanel) {
            if ((data.ambulances || 0) > 0) {
                emergencyPanel.className = "alert alert-danger fw-bold";
                emergencyPanel.innerHTML = `<i class="fas fa-exclamation-triangle me-1"></i> EMERGENCY OVERRIDE: ${data.ambulances} Ambulance(s) Detected!`;
            } else {
                emergencyPanel.className = "alert alert-success";
                emergencyPanel.innerHTML = `<i class="fas fa-check-circle me-1"></i> No Emergency Vehicle Detected`;
            }
        }

        // Update Vehicle Distribution Pie/Doughnut Chart
        if (window.pieChart) {
            window.pieChart.data.datasets[0].data = [
                data.cars || 0,
                data.bikes || 0,
                data.buses || 0,
                data.trucks || 0,
                data.autos || 0,
                data.ambulances || 0
            ];
            window.pieChart.update();
        }

        // Render Vehicle Table
        renderVehicleTable(data);

    } catch (err) {
        console.warn("Live YOLO stream fetch fallback:", err);
    }
}

// ----------------------------------------------------------
// 2. MILESTONE 3 ALERTS ENGINE (GET /alerts)
// ----------------------------------------------------------
async function fetchAlerts() {
    try {
        const response = await fetch("/alerts");
        if (!response.ok) throw new Error("Failed to fetch alerts");

        const alerts = await response.json();
        const alertBox = document.getElementById("alertBox") || document.getElementById("alerts-container");

        if (!alertBox) return;

        if (!alerts || alerts.length === 0) {
            alertBox.innerHTML = `
                <div class="alert alert-success mb-0 py-2">
                    <i class="fas fa-check-circle me-1"></i> No active alerts available. All signals operating normally.
                </div>`;
            return;
        }

        alertBox.innerHTML = alerts.map(alert => {
            const isHigh = alert.severity === "High" || alert.alert_type === "Accident";
            const badgeClass = isHigh ? "bg-danger" : "bg-warning text-dark";

            return `
                <div class="alert ${isHigh ? 'alert-danger' : 'alert-warning'} p-2 mb-2 shadow-sm rounded">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <strong class="text-uppercase small"><i class="fas fa-exclamation-triangle me-1"></i>${alert.alert_type || 'Alert'}</strong>
                        <span class="badge ${badgeClass}">${alert.severity || 'Medium'}</span>
                    </div>
                    <div class="small">${alert.description || alert.message || 'Traffic incident detected.'}</div>
                    <div class="d-flex justify-content-between align-items-center mt-2 pt-1 border-top border-secondary-subtle">
                        <small class="text-muted"><i class="fas fa-map-marker-alt me-1"></i>${alert.location || 'Central Intersection'}</small>
                        ${alert.status === 'Active' ? `
                            <button class="btn btn-xs btn-outline-dark py-0 px-2" style="font-size: 0.75rem;" onclick="resolveAlert(${alert.id})">
                                Resolve
                            </button>
                        ` : `<span class="badge bg-secondary">Resolved</span>`}
                    </div>
                </div>`;
        }).join("");

    } catch (err) {
        console.error("Error fetching live alerts:", err);
    }
}

// ----------------------------------------------------------
// 3. MILESTONE 3 KPIS ENGINE (GET /analytics/kpis)
// ----------------------------------------------------------
async function fetchKPIs() {
    try {
        const response = await fetch("/analytics/kpis");
        if (!response.ok) throw new Error("Failed to fetch KPIs");

        const kpis = await response.json();

        updateDOMText("kpi-total-vehicles", kpis.total_vehicles_detected || 0);
        updateDOMText("kpi-active-alerts", kpis.active_alerts || 0);
        updateDOMText("kpi-total-accidents", kpis.total_accidents || 0);
        updateDOMText("kpi-current-density", kpis.current_density || "Low");

    } catch (err) {
        console.error("Error fetching KPIs:", err);
    }
}

// ----------------------------------------------------------
// 4. AI RECOMMENDATION & STATUS ENGINE (GET /analytics/traffic-status)
// ----------------------------------------------------------
async function fetchTrafficStatus() {
    try {
        const response = await fetch("/analytics/traffic-status?vehicle_count=25&emergency_count=0");
        if (!response.ok) throw new Error("Failed to fetch traffic status");

        const status = await response.json();

        updateDOMText("recommendation", status.recommendation || "Traffic operating within normal parameters.");
        updateDOMText("ai-recommendation", status.recommendation || "Traffic operating within normal parameters.");
        updateDOMText("signalTime", `${status.signal_time || 30} Sec`);
        updateDOMText("signal-timer", `${status.signal_time || 30}s`);

    } catch (err) {
        console.error("Error fetching AI traffic status:", err);
    }
}
// ==========================================================
// static/js/dashboard.js - PART 2
// AI Traffic Management System - Complete Milestone 3 Engine
// ==========================================================

// ----------------------------------------------------------
// 5. MILESTONE 3 TRAFFIC TRENDS CHART ENGINE (GET /analytics/trends)
// ----------------------------------------------------------
async function fetchTrafficTrends() {
    try {
        const response = await fetch("/analytics/trends");
        if (!response.ok) throw new Error("Failed to fetch traffic trends");

        const data = await response.json();
        
        // Target either Milestone 3 chart canvas or legacy chart canvas
        const canvasId = document.getElementById("trafficTrendsChart") ? "trafficTrendsChart" : "trafficChart";
        const ctx = document.getElementById(canvasId);

        if (!ctx) return;

        const labels = data.labels || ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
        const counts = data.values || data.counts || [120, 190, 300, 250, 420, 310, 180];

        if (window.trafficChart) {
            window.trafficChart.data.labels = labels;
            window.trafficChart.data.datasets[0].data = counts;
            window.trafficChart.update();
        } else {
            window.trafficChart = new Chart(ctx, {
                type: "line",
                data: {
                    labels: labels,
                    datasets: [{
                        label: "Vehicle Volume Trend",
                        data: counts,
                        borderWidth: 3,
                        borderColor: "#2563eb",
                        backgroundColor: "rgba(37, 99, 235, 0.1)",
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: true } },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }

    } catch (err) {
        console.error("Error updating traffic trends chart:", err);
    }
}

// ----------------------------------------------------------
// 6. OPENSTREETMAP HEATMAP ENGINE (GET /analytics/heatmap-data)
// ----------------------------------------------------------
async function loadHeatmap() {
    const mapElement = document.getElementById("traffic-map");
    if (!mapElement || typeof L === "undefined") return;

    try {
        const response = await fetch("/analytics/heatmap-data");
        let points = [];

        if (response.ok) {
            const heatmapData = await response.json();
            // Expecting format: [[lat, lng, intensity], ...] or objects
            points = heatmapData.map(p => Array.isArray(p) ? p : [p.lat, p.lng, p.intensity || 0.6]);
        } else {
            // Default fallback map points centered on city intersection
            points = [
                [12.9716, 77.5946, 0.8],
                [12.9720, 77.5950, 0.5],
                [12.9710, 77.5940, 0.9],
                [12.9725, 77.5960, 0.3]
            ];
        }

        // Initialize Leaflet map if not already created
        if (!window.leafletMap) {
            window.leafletMap = L.map("traffic-map").setView([12.9716, 77.5946], 14);

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "© OpenStreetMap contributors"
            }).addTo(window.leafletMap);
        }

        // Render or update Leaflet heat layer
        if (typeof L.heatLayer === "function") {
            if (window.heatLayer) {
                window.leafletMap.removeLayer(window.heatLayer);
            }
            window.heatLayer = L.heatLayer(points, { radius: 25, blur: 15, maxZoom: 17 }).addTo(window.leafletMap);
        }

    } catch (err) {
        console.error("Error rendering OpenStreetMap heatmap:", err);
    }
}

// ----------------------------------------------------------
// 7. VIDEO FILE UPLOAD ENGINE (POST /detect/upload)
// ----------------------------------------------------------
async function uploadVideo() {
    const fileInput = document.getElementById("videoFile");
    const statusDiv = document.getElementById("uploadStatus");

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        if (statusDiv) {
            statusDiv.className = "text-danger mt-2 fw-bold";
            statusDiv.innerText = "Please select a video file first!";
        }
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    if (statusDiv) {
        statusDiv.className = "text-primary mt-2 fw-semibold";
        statusDiv.innerHTML = `<div class="spinner-border spinner-border-sm me-1" role="status"></div> Processing video stream...`;
    }

    try {
        const response = await fetch("/detect/upload", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            if (statusDiv) {
                statusDiv.className = "text-success mt-2 fw-bold";
                statusDiv.innerText = "Video uploaded and AI analysis started successfully!";
            }
            // Trigger an immediate dashboard data refresh
            initializeDashboard();
        } else {
            throw new Error(result.detail || result.message || "Upload failed");
        }
    } catch (err) {
        console.error("Video upload error:", err);
        if (statusDiv) {
            statusDiv.className = "text-danger mt-2 fw-bold";
            statusDiv.innerText = `Error: ${err.message}`;
        }
    }
}

// ----------------------------------------------------------
// 8. ALERT RESOLVER ENGINE (POST /alerts/resolve)
// ----------------------------------------------------------
async function resolveAlert(alertId) {
    try {
        const response = await fetch(`/alerts/resolve/${alertId}`, { method: "POST" });
        if (response.ok) {
            fetchAlerts();
            fetchKPIs();
        } else {
            // Fallback for query param style endpoints
            await fetch(`/alerts/resolve?id=${alertId}`, { method: "POST" });
            fetchAlerts();
            fetchKPIs();
        }
    } catch (err) {
        console.error("Error resolving alert:", err);
    }
}

// ----------------------------------------------------------
// 9. HELPER UTILITIES & DOM RENDERERS
// ----------------------------------------------------------
function updateDOMText(elementId, text) {
    const el = document.getElementById(elementId);
    if (el) el.innerText = text;
}

function clearError() {
    const errorBox = document.getElementById("errorBox");
    if (errorBox) errorBox.innerHTML = "";
}

function renderVehicleTable(data) {
    const vehicleTable = document.getElementById("vehicleTable");
    if (!vehicleTable) return;

    const items = [
        { type: "Cars", count: data.cars || 0 },
        { type: "Bikes / Motorcycles", count: data.bikes || 0 },
        { type: "Buses", count: data.buses || 0 },
        { type: "Trucks", count: data.trucks || 0 },
        { type: "Auto Rickshaws", count: data.autos || 0 },
        { type: "Ambulances (Emergency)", count: data.ambulances || 0 }
    ];

    vehicleTable.innerHTML = items.map(item => `
        <tr>
            <td><strong>${item.type}</strong></td>
            <td><span class="badge bg-secondary fs-6">${item.count}</span></td>
        </tr>
    `).join("");
}

// Automatically bind initialization on window ready
window.addEventListener("DOMContentLoaded", () => {
    initializeDashboard();
});