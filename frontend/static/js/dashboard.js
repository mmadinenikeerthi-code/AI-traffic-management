// ==========================================================
// dashboard.js
// Part 1
// AI Traffic Management & Congestion Detection System
// Compatible with detect.py
// ==========================================================

// ----------------------------------------------------------
// Backend URL
// ----------------------------------------------------------

const API_URL = "http://127.0.0.1:8000";

// ----------------------------------------------------------
// Common API Function
// ----------------------------------------------------------

async function api(endpoint, method = "GET") {

    try {

        const token =
            localStorage.getItem("token") ||
            localStorage.getItem("access_token");

        if (!token) {

            alert("Please login first.");

            window.location.href = "/login";

            return null;

        }

        const response = await fetch(API_URL + endpoint, {

            method: method,

            headers: {

                "Content-Type": "application/json",

                "Authorization": `Bearer ${token}`

            }

        });

        if (response.status === 401) {

            alert("Session expired.");

            localStorage.clear();

            window.location.href = "/login";

            return null;

        }

        if (!response.ok) {

            console.error(endpoint, response.status);

            return null;

        }

        return await response.json();

    }

    catch (error) {

        console.error(error);

        return null;

    }

}

// ==========================================================
// Dashboard Summary
// GET /detect/live-dashboard
// ==========================================================

async function loadDashboard() {

    const data = await api("/detect/live-dashboard");

    if (!data) return;

    document.getElementById("totalVehicles").innerHTML =
        data.total_vehicles || 0;

    document.getElementById("cars").innerHTML =
        data.cars || 0;

    document.getElementById("bikes").innerHTML =
        data.bikes || 0;

    document.getElementById("buses").innerHTML =
        data.buses || 0;

    document.getElementById("trucks").innerHTML =
        data.trucks || 0;

    document.getElementById("autos").innerHTML =
        data.auto_rickshaw || 0;

    document.getElementById("ambulances").innerHTML =
        data.ambulance || 0;

    document.getElementById("congestionLevel").innerHTML =
        data.congestion_level || "LOW";

    document.getElementById("signalTime").innerHTML =
        (data.signal_time || 30) + " Sec";

}

// ==========================================================
// Vehicle Table
// Uses /detect/live-dashboard
// ==========================================================

async function loadVehicles() {

    const data = await api("/detect/live-dashboard");

    if (!data) return;

    const table = document.getElementById("vehicleTable");

    if (!table) return;

    table.innerHTML = `

<tr>
<td>Cars</td>
<td>${data.cars}</td>
</tr>

<tr>
<td>Bikes</td>
<td>${data.bikes}</td>
</tr>

<tr>
<td>Buses</td>
<td>${data.buses}</td>
</tr>

<tr>
<td>Trucks</td>
<td>${data.trucks}</td>
</tr>

<tr>
<td>Auto Rickshaw</td>
<td>${data.auto_rickshaw}</td>
</tr>

<tr>
<td>Ambulance</td>
<td>${data.ambulance}</td>
</tr>

<tr class="table-primary">

<th>Total</th>

<th>${data.total_vehicles}</th>

</tr>

`;

}

// ==========================================================
// Latest Congestion
// GET /detect/congestion/latest
// ==========================================================

async function loadCongestion() {

    const data = await api("/detect/congestion/latest");

    if (!data) return;

    if (data.message) {

        document.getElementById("congestionLevel").innerHTML = "LOW";

        document.getElementById("signalTime").innerHTML = "30 Sec";

        document.getElementById("density").innerHTML = "0%";

        document.getElementById("speed").innerHTML = "0 km/h";

        return;

    }

    document.getElementById("congestionLevel").innerHTML =
        data.congestion_level;

    document.getElementById("signalTime").innerHTML =
        data.signal_time + " Sec";

    document.getElementById("density").innerHTML =
        data.density + "%";

    document.getElementById("speed").innerHTML =
        data.average_speed + " km/h";

}

// ==========================================================
// AI Recommendation
// GET /detect/congestion/latest
// ==========================================================

async function loadRecommendation() {

    const data = await api("/detect/congestion/latest");

    if (!data) return;

    const recommendation =
        document.getElementById("recommendation");

    if (!recommendation) return;

    recommendation.innerHTML =
        data.recommendation || "Traffic Normal";

}

// ==========================================================
// Prediction
// ==========================================================

async function loadPrediction() {

    const data = await api("/detect/congestion/latest");

    if (!data) return;

    const prediction =
        document.getElementById("prediction");

    if (!prediction) return;

    prediction.innerHTML =
        data.congestion_level || "LOW";

}

// ==========================================================
// Signal Status
// ==========================================================

async function loadSignal() {

    const data = await api("/detect/congestion/latest");

    if (!data) return;

    const signal =
        document.getElementById("signalStatus");

    if (!signal) return;

    signal.innerHTML =
        data.congestion_level || "LOW";

}
// ==========================================================
// dashboard.js
// Part 2
// Emergency • Alerts • Reports • AI • Camera • Charts
// Compatible with detect.py
// ==========================================================

// ----------------------------------------------------------
// Emergency Vehicle
// Uses /detect/live-dashboard
// ----------------------------------------------------------

async function loadEmergency() {

    const data = await api("/detect/live-dashboard");

    if (!data) return;

    const emergencyDetected = (data.ambulance || 0) > 0;

    const panel = document.getElementById("emergencyPanel");

    if (panel) {

        panel.className = emergencyDetected
            ? "alert alert-danger"
            : "alert alert-success";

        panel.innerHTML = emergencyDetected
            ? "Emergency Vehicle Detected"
            : "No Emergency Vehicle Detected";
    }

    const count = document.getElementById("emergencyCount");
    if (count) count.innerHTML = data.ambulance || 0;

    const ambulance = document.getElementById("ambulanceCount");
    if (ambulance) ambulance.innerHTML = data.ambulance || 0;

    const priority = document.getElementById("priority");
    if (priority)
        priority.innerHTML = emergencyDetected ? "HIGH" : "NORMAL";

    const extension = document.getElementById("extension");
    if (extension)
        extension.innerHTML = (data.signal_time || 30) + " Seconds";

}

// ----------------------------------------------------------
// Live Alerts
// ----------------------------------------------------------

async function loadAlerts() {

    const data = await api("/detect/congestion/latest");

    if (!data) return;

    const panel = document.getElementById("alertPanel");

    if (!panel) return;

    panel.innerHTML = "";

    if (data.message) {

        panel.innerHTML = `
            <div class="alert alert-success">
                No alerts available.
            </div>
        `;

        return;
    }

    if (data.congestion_level === "HIGH") {

        panel.innerHTML = `
            <div class="alert alert-danger">
                Heavy Traffic Detected
            </div>
        `;

    }

    else if (data.congestion_level === "MEDIUM") {

        panel.innerHTML = `
            <div class="alert alert-warning">
                Moderate Traffic
            </div>
        `;

    }

    else {

        panel.innerHTML = `
            <div class="alert alert-success">
                No alerts available.
            </div>
        `;

    }

}

// ----------------------------------------------------------
// Reports
// Uses /detect/statistics
// ----------------------------------------------------------

async function loadReports() {

    const data = await api("/detect/statistics");

    if (!data) return;

    const table = document.getElementById("reportTable");

    if (!table) return;

    table.innerHTML = `

<tr>
<td>Uploaded Videos</td>
<td>${data.uploaded_videos}</td>
</tr>

<tr>
<td>Processed Videos</td>
<td>${data.processed_videos}</td>
</tr>

<tr>
<td>Vehicle Records</td>
<td>${data.vehicle_records}</td>
</tr>

<tr>
<td>Congestion Records</td>
<td>${data.congestion_records}</td>
</tr>

`;

}

// ----------------------------------------------------------
// Camera Status
// Uses /detect/health
// ----------------------------------------------------------

async function loadCameraStatus() {

    const data = await api("/detect/health");

    if (!data) return;

    const camera = document.getElementById("cameraStatus");

    if (!camera) return;

    camera.innerHTML = data.status;

}

// ----------------------------------------------------------
// AI Engine
// Uses /detect/performance
// ----------------------------------------------------------

async function loadAIEngine() {

    const data = await api("/detect/performance");

    if (!data) return;

    const ai = document.getElementById("aiEngine");

    if (!ai) return;

    ai.innerHTML =
        `${data.ai_model}<br>${data.status}`;

}

// ----------------------------------------------------------
// Pie Chart
// Uses /detect/analytics/classes
// ----------------------------------------------------------

async function loadPieChart() {

    if (typeof pieChart === "undefined") return;

    const data = await api("/detect/analytics/classes");

    if (!data) return;

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

// ----------------------------------------------------------
// Bar Chart
// Uses /detect/history
// ----------------------------------------------------------

async function loadBarChart() {

    if (typeof trafficChart === "undefined") return;

    const history = await api("/detect/history");

    if (!history) return;

    trafficChart.data.labels =
        history.map((_, index) => `#${index + 1}`);

    trafficChart.data.datasets[0].data =
        history.map(item => item.total);

    trafficChart.update();

}

// ----------------------------------------------------------
// Error Display
// ----------------------------------------------------------

function showError(message) {

    console.error(message);

    const errorBox = document.getElementById("errorBox");

    if (!errorBox) return;

    errorBox.innerHTML = `
        <div class="alert alert-danger">
            ${message}
        </div>
    `;

}

// ==========================================================
// dashboard.js
// Part 3
// Initialization • Auto Refresh • Logout • Session
// Compatible with detect.py
// ==========================================================

// ----------------------------------------------------------
// Auto Refresh
// ----------------------------------------------------------

function startAutoRefresh() {

    setInterval(async () => {

        await loadDashboard();
        await loadVehicles();
        await loadCongestion();
        await loadRecommendation();
        await loadPrediction();
        await loadSignal();
        await loadEmergency();
        await loadAlerts();
        await loadReports();
        await loadCameraStatus();
        await loadAIEngine();
        await loadPieChart();
        await loadBarChart();

    }, 10000);

}

// ----------------------------------------------------------
// Logout
// ----------------------------------------------------------

function logout() {

    localStorage.removeItem("token");
    localStorage.removeItem("access_token");
    localStorage.removeItem("username");
    localStorage.removeItem("user");

    window.location.href = "/login";

}

// ----------------------------------------------------------
// Session Check
// ----------------------------------------------------------

function checkSession() {

    const token =
        localStorage.getItem("token") ||
        localStorage.getItem("access_token");

    if (!token) {

        alert("Session expired. Please login again.");

        window.location.href = "/login";

        return false;

    }

    return true;

}

// ----------------------------------------------------------
// Initialize Dashboard
// ----------------------------------------------------------

async function initializeDashboard() {

    if (!checkSession()) return;

    try {

        await Promise.all([

            loadDashboard(),
            loadVehicles(),
            loadCongestion(),
            loadRecommendation(),
            loadPrediction(),
            loadSignal(),
            loadEmergency(),
            loadAlerts(),
            loadReports(),
            loadCameraStatus(),
            loadAIEngine(),
            loadPieChart(),
            loadBarChart()

        ]);

        console.log("Dashboard Loaded Successfully");

    }

    catch (error) {

        console.error(error);

        showError("Unable to load dashboard.");

    }

    startAutoRefresh();

}

// ----------------------------------------------------------
// Refresh Button
// ----------------------------------------------------------

const refreshBtn = document.querySelector(".btn.btn-primary");

if (refreshBtn) {

    refreshBtn.addEventListener("click", async () => {

        await initializeDashboard();

    });

}

// ----------------------------------------------------------
// Logout Button
// ----------------------------------------------------------

const logoutBtn = document.getElementById("logoutBtn");

if (logoutBtn) {

    logoutBtn.addEventListener("click", logout);

}

// ----------------------------------------------------------
// Page Load
// ----------------------------------------------------------

window.addEventListener("DOMContentLoaded", () => {

    if (

        window.location.pathname !== "/login" &&
        window.location.pathname !== "/register"

    ) {

        initializeDashboard();

    }

});

// ----------------------------------------------------------
// Global Error Handler
// ----------------------------------------------------------

window.onerror = function(message, source, line, column, error) {

    console.error("JavaScript Error");

    console.error("Message :", message);
    console.error("Source  :", source);
    console.error("Line    :", line);

    return false;

};

// ----------------------------------------------------------
// Unhandled Promise Errors
// ----------------------------------------------------------

window.addEventListener("unhandledrejection", function(event){

    console.error("Unhandled Promise:", event.reason);

});

// ==========================================================
// End dashboard.js
// ==========================================================