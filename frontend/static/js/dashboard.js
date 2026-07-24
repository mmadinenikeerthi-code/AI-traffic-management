/* ==========================================================================
   AI Traffic Management System - Dashboard Logic
   ========================================================================== */

/**
 * Initialize Dashboard Data and Timers on Page Load
 */
document.addEventListener("DOMContentLoaded", () => {
    initializeDashboard();
});

function initializeDashboard() {
    clearError();
    fetchDashboardData();

    // Auto-refresh dashboard metrics every 5 seconds
    if (!window.dashboardInterval) {
        window.dashboardInterval = setInterval(fetchDashboardData, 5000);
    }
}

/**
 * Fetch Live Dashboard Metrics from Backend API
 */
async function fetchDashboardData() {
    const token = localStorage.getItem("access_token") || localStorage.getItem("token");

    // Handle missing authentication token
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

    // Emergency Panel Alert
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

    // Update Vehicle Count Table
    updateVehicleTable(data);

    // Render Traffic Reports Table
    updateReportTable(data);

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
 * Populate Traffic Reports Table
 */
function updateReportTable(data) {
    const reportTable = document.getElementById("reportTable");
    if (!reportTable) return;

    if (data.reports && Array.isArray(data.reports) && data.reports.length > 0) {
        let reportHtml = "";
        data.reports.forEach(item => {
            reportHtml += `
                <tr>
                    <td><strong>${item.description}</strong></td>
                    <td>${item.value}</td>
                </tr>`;
        });
        reportTable.innerHTML = reportHtml;
    } else {
        // Fallback summary report when explicit backend array is absent
        reportTable.innerHTML = `
            <tr><td><strong>Total Processed Vehicles</strong></td><td>${data.total_vehicles || 0}</td></tr>
            <tr><td><strong>Congestion Level</strong></td><td>${data.congestion_level || "LOW"}</td></tr>
            <tr><td><strong>Average Traffic Speed</strong></td><td>${data.average_speed || 0} km/h</td></tr>
            <tr><td><strong>Estimated Route Delay</strong></td><td>${data.estimated_delay || 0} Mins</td></tr>
        `;
    }
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
 * Video Upload & YOLO Detection Processing Function
 */
async function uploadVideo() {
    const fileInput = document.getElementById('videoFile');
    const statusBox = document.getElementById('uploadStatus');

    if (!fileInput || fileInput.files.length === 0) {
        alert("Please select a video file first.");
        return;
    }

    const file = fileInput.files[0];
    const token = localStorage.getItem("access_token") || localStorage.getItem("token");

    if (!token) {
        alert("Session expired. Please log in again.");
        window.location.href = "/login";
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        // UI Uploading Status
        if (statusBox) {
            statusBox.innerHTML = `<span class="text-primary"><i class="fas fa-spinner fa-spin me-1"></i> Uploading video...</span>`;
        }

        // 1. Upload video to FastAPI
        const uploadRes = await fetch('/detect/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (!uploadRes.ok) {
            if (uploadRes.status === 401) throw new Error("Unauthorized. Please log in again.");
            throw new Error("Video upload failed.");
        }

        const uploadData = await uploadRes.json();
        const videoId = uploadData.video_id || uploadData.id;

        if (!videoId) {
            throw new Error("Server did not return a valid video ID.");
        }

        // UI Processing Status
        if (statusBox) {
            statusBox.innerHTML = `<span class="text-warning"><i class="fas fa-spinner fa-spin me-1"></i> Running YOLO detection... (this may take a moment)</span>`;
        }

        // 2. Trigger YOLO processing on uploaded video ID
        const processRes = await fetch(`/detect/process/${videoId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!processRes.ok) {
            throw new Error("YOLO video processing failed server-side.");
        }

        // Success Feedback
        if (statusBox) {
            statusBox.innerHTML = `<span class="text-success"><i class="fas fa-check-circle me-1"></i> Detection Complete! Refreshing dashboard...</span>`;
        }

        // 3. Re-fetch dashboard stats to get updated numbers from PostgreSQL
        fetchDashboardData();

    } catch (err) {
        console.error("Upload/Processing error:", err);
        if (statusBox) {
            statusBox.innerHTML = `<span class="text-danger"><i class="fas fa-exclamation-triangle me-1"></i> ${err.message}</span>`;
        }
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