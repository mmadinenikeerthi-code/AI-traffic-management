/* ==========================================================================
   AI Traffic Management System - Dashboard Logic
   ========================================================================== */

let trafficChart = null;
let vehiclePieChart = null;

/**
 * Initialize Dashboard Data and Charts
 */
document.addEventListener("DOMContentLoaded", () => {
    initializeDashboard();
});

function initializeDashboard() {
    clearError();
    fetchDashboardData();
}

/**
 * Fetch Live Dashboard Metrics from Backend API
 */
async function fetchDashboardData() {
    const token = localStorage.getItem("access_token") || localStorage.getItem("token");

    try {
        const response = await fetch("/api/dashboard/metrics", {
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
            throw new Error("Failed to load dashboard data from server.");
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
    // 1. Top Summary Cards
    setElementText("totalVehicles", data.total_vehicles || 0);
    setElementText("congestionLevel", data.congestion_level || "LOW");
    setElementText("signalTime", (data.signal_time || 30) + " Sec");
    setElementText("ambulanceCount", data.ambulance_count || 0);

    // 2. Vehicle Breakdown Cards
    setElementText("cars", data.cars || 0);
    setElementText("bikes", data.bikes || 0);
    setElementText("buses", data.buses || 0);
    setElementText("trucks", data.trucks || 0);
    setElementText("autos", data.auto_rickshaw || 0);
    setElementText("ambulances", data.ambulance || 0);

    // 3. AI Recommendations & Analytics
    setElementText("density", (data.density || 0) + "%");
    setElementText("speed", (data.speed || 0) + " km/h");
    setElementText("signalStatus", data.signal_status || "GREEN");
    setElementText("prediction", data.prediction || "Normal Traffic Flow");

    if (data.ai_recommendation) {
        const recBox = document.getElementById("recommendation");
        if (recBox) recBox.innerText = data.ai_recommendation;
    }

    // 4. Congestion Summary Table
    setElementText("currentLevel", data.congestion_level || "LOW");
    setElementText("roadUsage", (data.road_usage || 0) + "%");
    setElementText("delay", (data.estimated_delay || 0) + " Minutes");
    setElementText("route", data.suggested_route || "Main Highway");

    // 5. Emergency Panel
    const emergencyPanel = document.getElementById("emergencyPanel");
    if (emergencyPanel) {
        if (data.ambulance_count > 0 || data.has_emergency) {
            emergencyPanel.className = "alert alert-danger";
            emergencyPanel.innerHTML = "<strong>🚨 Priority Alert:</strong> Emergency Vehicle Detected! Clearing Route...";
        } else {
            emergencyPanel.className = "alert alert-success";
            emergencyPanel.innerHTML = "No Emergency Vehicle Detected";
        }
    }

    // 6. Update Recent Vehicle Table
    updateVehicleTable(data);

    // 7. Update Live Charts
    if (data.chart_labels && data.chart_values) {
        updateTrafficChart(data.chart_labels, data.chart_values);
    }

    updatePieChart(data);
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
 * Helper to Safely Set Text Content
 */
function setElementText(id, text) {
    const element = document.getElementById(id);
    if (element) {
        element.innerText = text;
    }
}

/**
 * Display Error Messages
 */
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

/**
 * Clear Error Messages
 */
function clearError() {
    const errorBox = document.getElementById("errorBox");
    if (errorBox) {
        errorBox.innerHTML = "";
    }
}