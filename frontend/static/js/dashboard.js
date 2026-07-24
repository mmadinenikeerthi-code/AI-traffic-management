/* ==========================================================================
   AI Traffic Management System - Dashboard Logic
   ========================================================================== */

// 1. Declare chart variables at top-level scope
let trafficChart = null;
let pieChart = null;

/**
 * Initialize Dashboard Data and Charts
 */
document.addEventListener("DOMContentLoaded", () => {
    initializeDashboard();
});

function initializeDashboard() {
    clearError();
    fetchDashboardData();

    // Auto-refresh dashboard every 5 seconds
    if (!window.dashboardInterval) {
        window.dashboardInterval = setInterval(fetchDashboardData, 5000);
    }
}

/**
 * Fetch Live Dashboard Metrics from Backend API
 */
async function fetchDashboardData() {
    const token = localStorage.getItem("access_token") || localStorage.getItem("token");

    // 2. Handle missing token immediately
    if (!token) {
        window.location.href = "/login";
        return;
    }

    try {
        const response = await fetch("/detect/live-dashboard", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = "/login";
                return;
            }
            throw new Error("Failed to load live traffic data from server.");
        }

        const data = await response.json();
        updateDashboardUI(data);

    } catch (error) {
        console.error("Dashboard fetch error:", error);
        showError(error.message);
    }
}

/**
 * Update UI Elements with API Response Data
 */
function updateDashboardUI(data) {
    // Top Summary Cards
    setElementText("totalVehicles", data.total_vehicles || 0);
    setElementText("congestionLevel", data.congestion_level || "LOW");
    setElementText("signalTime", (data.signal_time || 30) + " Sec");
    setElementText("ambulanceCount", data.ambulance || 0);

    // Vehicle Breakdown Cards
    setElementText("cars", data.cars || 0);
    setElementText("bikes", data.bikes || 0);
    setElementText("buses", data.buses || 0);
    setElementText("trucks", data.trucks || 0);
    setElementText("autos", data.auto_rickshaw || 0);
    setElementText("ambulances", data.ambulance || 0);

    // AI Recommendations & Analytics
    setElementText("density", (data.density || 0) + "%");
    setElementText("speed", (data.average_speed || 0) + " km/h");
    
    // Dynamic Signal Status Display
    let signalStatusText = "GREEN";
    if (data.signal_time >= 120) {
        signalStatusText = "CRITICAL";
    } else if (data.signal_time >= 90) {
        signalStatusText = "EXTENDED GREEN";
    } else if (data.signal_time >= 60) {
        signalStatusText = "MEDIUM";
    }
    setElementText("signalStatus", signalStatusText);

    setElementText("prediction", data.prediction || "Normal Traffic Flow");

    if (data.recommendation) {
        const recBox = document.getElementById("recommendation");
        if (recBox) recBox.innerText = data.recommendation;
    }

    // Congestion Summary Table
    setElementText("currentLevel", data.congestion_level || "LOW");
    setElementText("roadUsage", (data.density || 0) + "%");
    setElementText("delay", (data.estimated_delay || 0) + " Minutes");
    setElementText("route", data.suggested_route || "Main Highway");

    // Emergency Panel
    const emergencyPanel = document.getElementById("emergencyPanel");
    if (emergencyPanel) {
        if (data.ambulance > 0 || data.has_emergency) {
            emergencyPanel.className = "alert alert-danger";
            emergencyPanel.innerHTML = "<strong>🚨 Priority Alert:</strong> Emergency Vehicle Detected! Clearing Route...";
        } else {
            emergencyPanel.className = "alert alert-success";
            emergencyPanel.innerHTML = "No Emergency Vehicle Detected";
        }
    }

    // Update Recent Vehicle Table
    updateVehicleTable(data);

    // Update Live Charts Safely
    updatePieChart(data);
    if (data.chart_labels && data.chart_values) {
        updateTrafficChart(data.chart_labels, data.chart_values);
    }
}

/**
 * Populate Vehicle Breakdown Table
 */
function updateVehicleTable(data) {
    const tableBody = document.getElementById("vehicleTable");
    if (!tableBody) return;

    const vehicles = [
        { type: "Cars", count: data.cars || 0 },
        { type: "Bikes / Two-Wheelers", count: data.bikes || 0 },
        { type: "Buses", count: data.buses || 0 },
        { type: "Trucks / Heavy Vehicles", count: data.trucks || 0 },
        { type: "Auto Rickshaws", count: data.auto_rickshaw || 0 },
        { type: "Emergency Vehicles", count: data.ambulance || 0 }
    ];

    let html = "";
    vehicles.forEach(item => {
        html += `
            <tr>
                <td><strong>${item.type}</strong></td>
                <td><span class="badge bg-primary rounded-pill">${item.count}</span></td>
            </tr>
        `;
    });

    tableBody.innerHTML = html;
}

/**
 * Update Vehicle Doughnut/Pie Chart safely
 */
function updatePieChart(data) {
    if (typeof pieChart !== "undefined" && pieChart && pieChart.data) {
        pieChart.data.datasets[0].data = [
            data.cars || 0,
            data.bikes || 0,
            data.buses || 0,
            data.trucks || 0,
            data.auto_rickshaw || 0,
            data.ambulance || 0
        ];
        pieChart.update();
    }
}

/**
 * Update Traffic Trend Line Chart safely
 */
function updateTrafficChart(labels, values) {
    if (typeof trafficChart !== "undefined" && trafficChart && trafficChart.data) {
        trafficChart.data.labels = labels;
        trafficChart.data.datasets[0].data = values;
        trafficChart.update();
    }
}

/**
 * Helper Utilities
 */
function setElementText(id, text) {
    const element = document.getElementById(id);
    if (element) {
        element.innerText = text;
    }
}

function showError(message) {
    const errorBox = document.getElementById("errorBox");
    if (errorBox) {
        errorBox.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <strong>System Alert:</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
    }
}

function clearError() {
    const errorBox = document.getElementById("errorBox");
    if (errorBox) {
        errorBox.innerHTML = "";
    }
}