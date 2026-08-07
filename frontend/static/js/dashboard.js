// ==========================================================
// static/js/dashboard.js
// AI TRAFFIC MANAGEMENT SYSTEM
// FINAL UNIFIED VERSION
// Dashboard + YOLO Upload + Analytics + GIS + Admin Incidents
// ==========================================================

"use strict";

console.log("==========================================");
console.log("AI TRAFFIC MANAGEMENT DASHBOARD JS");
console.log("VERSION: FINAL UNIFIED VERSION");
console.log("==========================================");

// ==========================================================
// GLOBAL VARIABLES
// ==========================================================

window.trafficChart = window.trafficChart || null;
window.pieChart = window.pieChart || null;
window.leafletMap = window.leafletMap || null;
window.heatLayer = window.heatLayer || null;

window.dashboardInterval = null;
window.dashboardSlowInterval = null;

window.dashboardInitialized = false;

// Stores latest uploaded YOLO result.
// Automatic live-dashboard refresh will NOT overwrite it.
window.latestVideoResult = null;


// ==========================================================
// PAGE LOAD
// ==========================================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("Dashboard DOM loaded.");

    initializeCharts();

    initializeRoleControl();

    initializeUploadButton();

    initializeVideoPreview();

    showIncidentNavigationForAdmin();

    initializeDashboard();

});


// ==========================================================
// INITIALIZE UPLOAD BUTTON
// ==========================================================

function initializeUploadButton() {

    const button = document.getElementById(
        "uploadVideoButton"
    );

    if (!button) {

        console.warn(
            "uploadVideoButton not found."
        );

        return;
    }

    button.addEventListener(
        "click",
        function (event) {

            event.preventDefault();

            console.log(
                "Upload button clicked."
            );

            uploadVideo();

        }
    );

    console.log(
        "Upload button initialized."
    );
}


// ==========================================================
// INITIALIZE DASHBOARD
// ==========================================================

async function initializeDashboard() {

    console.log(
        "Initializing dashboard..."
    );

    clearError();

    // ------------------------------------------------------
    // FIRST LOAD
    // ------------------------------------------------------

    await fetchDashboardData();

    // ------------------------------------------------------
    // ANALYTICS
    // ------------------------------------------------------

    fetchAlerts();

    fetchKPIs();

    fetchTrafficStatus();

    fetchTrafficTrends();

    // ------------------------------------------------------
    // GIS
    // ------------------------------------------------------

    loadHeatmap();

    // ------------------------------------------------------
    // ADMIN
    // ------------------------------------------------------

    const role = getUserRole();

    if (
        role === "admin" ||
        role === "administrator"
    ) {

        loadAdminIncidentMetrics();

        loadAdminIncidents();

    }

    // ------------------------------------------------------
    // FAST REFRESH
    // ------------------------------------------------------

    if (!window.dashboardInterval) {

        window.dashboardInterval =
            setInterval(
                function () {

                    console.log(
                        "Automatic dashboard refresh..."
                    );

                    fetchDashboardData();

                    fetchAlerts();

                    fetchKPIs();

                    fetchTrafficStatus();

                    const currentRole =
                        getUserRole();

                    if (
                        currentRole === "admin" ||
                        currentRole === "administrator"
                    ) {

                        loadAdminIncidentMetrics();

                        loadAdminIncidents();

                    }

                },
                5000
            );
    }

    // ------------------------------------------------------
    // SLOW REFRESH
    // ------------------------------------------------------

    if (!window.dashboardSlowInterval) {

        window.dashboardSlowInterval =
            setInterval(
                function () {

                    fetchTrafficTrends();

                    loadHeatmap();

                },
                30000
            );
    }

    window.dashboardInitialized = true;

    console.log(
        "Dashboard initialized successfully."
    );
}


// ==========================================================
// ROLE CONTROL
// ==========================================================

function initializeRoleControl() {

    const role = getUserRole();

    console.log(
        "Current user role:",
        role
    );

    const adminElements =
        document.querySelectorAll(
            ".admin-only"
        );

    const supervisorElements =
        document.querySelectorAll(
            ".supervisor-only"
        );

    const isAdmin =
        role === "admin" ||
        role === "administrator";

    const isSupervisor =
        role === "supervisor" ||
        role === "traffic supervisor";

    // ------------------------------------------------------
    // ADMIN
    // ------------------------------------------------------

    if (isAdmin) {

        adminElements.forEach(
            function (element) {

                element.style.display = "";

            }
        );

        supervisorElements.forEach(
            function (element) {

                element.style.display = "";

            }
        );

        setIncidentSectionDisplay(
            true
        );

    }

    // ------------------------------------------------------
    // SUPERVISOR
    // ------------------------------------------------------

    else if (isSupervisor) {

        adminElements.forEach(
            function (element) {

                element.style.display =
                    "none";

            }
        );

        supervisorElements.forEach(
            function (element) {

                element.style.display =
                    "";

            }
        );

        setIncidentSectionDisplay(
            false
        );

    }

    // ------------------------------------------------------
    // TRAFFIC OFFICER / NORMAL USER
    // ------------------------------------------------------

    else {

        adminElements.forEach(
            function (element) {

                element.style.display =
                    "none";

            }
        );

        supervisorElements.forEach(
            function (element) {

                element.style.display =
                    "none";

            }
        );

        setIncidentSectionDisplay(
            false
        );

    }
}


// ==========================================================
// ADMIN INCIDENT SECTION DISPLAY
// Handles both possible IDs
// ==========================================================

function setIncidentSectionDisplay(
    show
) {

    const sections = [

        document.getElementById(
            "adminIncidentSection"
        ),

        document.getElementById(
            "adminIncidentsSection"
        )

    ];

    sections.forEach(
        function (section) {

            if (!section) {
                return;
            }

            section.style.display =
                show
                    ? "block"
                    : "none";

        }
    );
}


// ==========================================================
// GET CURRENT USER
// ==========================================================

function getCurrentUser() {

    try {

        return JSON.parse(
            localStorage.getItem(
                "user"
            ) || "{}"
        );

    }

    catch (error) {

        console.warn(
            "Could not read user:",
            error
        );

        return {};

    }
}


// ==========================================================
// GET USER ROLE
// ==========================================================

function getUserRole() {

    const user =
        getCurrentUser();

    return (
        user.role ||
        user.user_role ||
        localStorage.getItem(
            "role"
        ) ||
        ""
    )
        .toString()
        .trim()
        .toLowerCase();
}


// ==========================================================
// GET JWT TOKEN
// ==========================================================

function getAuthToken() {

    return (
        localStorage.getItem(
            "access_token"
        ) ||

        localStorage.getItem(
            "token"
        ) ||

        ""
    );
}


// ==========================================================
// NORMALIZE VEHICLE DATA
// ==========================================================

function normalizeVehicleData(data) {

    data = data || {};

    // ------------------------------------------------------
    // Nested result
    // ------------------------------------------------------

    if (
        data.result &&
        typeof data.result === "object"
    ) {

        data = {
            ...data,
            ...data.result
        };

    }

    // ------------------------------------------------------
    // Nested data
    // ------------------------------------------------------

    if (
        data.data &&
        typeof data.data === "object"
    ) {

        data = {
            ...data,
            ...data.data
        };

    }

    // ------------------------------------------------------
    // Nested analysis
    // ------------------------------------------------------

    if (
        data.analysis &&
        typeof data.analysis === "object"
    ) {

        data = {
            ...data,
            ...data.analysis
        };

    }

    // ------------------------------------------------------
    // VEHICLES
    // ------------------------------------------------------

    const cars =
        Number(
            data.cars ??
            data.car ??
            0
        );

    const bikes =
        Number(
            data.bikes ??
            data.motorcycles ??
            data.motorbikes ??
            0
        );

    const buses =
        Number(
            data.buses ??
            data.bus ??
            0
        );

    const trucks =
        Number(
            data.trucks ??
            data.truck ??
            0
        );

    const autos =
        Number(
            data.autos ??
            data.auto_rickshaw ??
            data.auto_rickshaws ??
            data.auto ??
            0
        );

    const ambulances =
        Number(
            data.ambulances ??
            data.ambulance ??
            0
        );

    // ------------------------------------------------------
    // TOTAL
    // ------------------------------------------------------

    let total =
        Number(
            data.total_vehicles ??
            data.totalVehicles ??
            data.total ??
            0
        );

    if (
        !Number.isFinite(total) ||
        total <= 0
    ) {

        total =
            cars +
            bikes +
            buses +
            trucks +
            autos +
            ambulances;

    }

    return {

        ...data,

        total_vehicles:
            total,

        cars:
            cars,

        bikes:
            bikes,

        buses:
            buses,

        trucks:
            trucks,

        autos:
            autos,

        auto_rickshaw:
            autos,

        ambulances:
            ambulances,

        ambulance:
            ambulances

    };
}


// ==========================================================
// FETCH LIVE DASHBOARD
// GET /detect/live-dashboard
// ==========================================================

async function fetchDashboardData() {

    try {

        const token =
            getAuthToken();

        const response =
            await fetch(
                "/detect/live-dashboard",
                {

                    method:
                        "GET",

                    headers: {

                        "Accept":
                            "application/json",

                        ...(token
                            ? {
                                "Authorization":
                                    `Bearer ${token}`
                            }
                            : {})

                    }

                }
            );

        if (!response.ok) {

            throw new Error(
                `Live dashboard returned ${response.status}`
            );

        }

        let data =
            await response.json();

        console.log(
            "LIVE DASHBOARD RESPONSE:",
            data
        );

        data =
            normalizeVehicleData(
                data
            );

        // --------------------------------------------------
        // LATEST UPLOADED VIDEO HAS PRIORITY
        // --------------------------------------------------

        if (
            window.latestVideoResult
        ) {

            console.log(
                "Using latest uploaded YOLO result."
            );

            data =
                normalizeVehicleData(
                    window.latestVideoResult
                );

        }

        updateDashboardFromVideoResult(
            data
        );

    }

    catch (error) {

        console.warn(
            "Live dashboard fetch failed:",
            error.message
        );

    }
}


// ==========================================================
// UPDATE COMPLETE DASHBOARD FROM YOLO RESULT
// ==========================================================

function updateDashboardFromVideoResult(
    rawData
) {

    console.log(
        "=========================================="
    );

    console.log(
        "UPDATING DASHBOARD"
    );

    console.log(
        "RAW DATA:",
        rawData
    );

    const data =
        normalizeVehicleData(
            rawData
        );

    console.log(
        "NORMALIZED DATA:",
        data
    );

    console.log(
        "=========================================="
    );

    // ------------------------------------------------------
    // TOTAL
    // ------------------------------------------------------

    updateDOMText(
        "totalVehicles",
        data.total_vehicles
    );

    updateDOMText(
        "kpi-total-vehicles",
        data.total_vehicles
    );

    // ------------------------------------------------------
    // CARS
    // ------------------------------------------------------

    updateDOMText(
        "cars",
        data.cars
    );

    // ------------------------------------------------------
    // BIKES
    // ------------------------------------------------------

    updateDOMText(
        "bikes",
        data.bikes
    );

    // ------------------------------------------------------
    // BUSES
    // ------------------------------------------------------

    updateDOMText(
        "buses",
        data.buses
    );

    // ------------------------------------------------------
    // TRUCKS
    // ------------------------------------------------------

    updateDOMText(
        "trucks",
        data.trucks
    );

    // ------------------------------------------------------
    // AUTO
    // ------------------------------------------------------

    updateDOMText(
        "autos",
        data.autos
    );

    // ------------------------------------------------------
    // AMBULANCE
    // ------------------------------------------------------

    updateDOMText(
        "ambulances",
        data.ambulances
    );

    updateDOMText(
        "ambulanceCount",
        data.ambulances
    );

    // ------------------------------------------------------
    // CONGESTION
    // ------------------------------------------------------

    const congestion =
        data.congestion_level ||
        data.congestion ||
        "LOW";

    updateDOMText(
        "congestionLevel",
        congestion
    );

    updateDOMText(
        "currentLevel",
        congestion
    );

    // ------------------------------------------------------
    // DENSITY
    // ------------------------------------------------------

    const density =
        data.density_percentage ??
        data.density ??
        0;

    updateDOMText(
        "density",
        `${density}%`
    );

    updateDOMText(
        "roadUsage",
        `${density}%`
    );

    // ------------------------------------------------------
    // SPEED
    // ------------------------------------------------------

    const speed =
        data.avg_speed ??
        data.average_speed ??
        data.average_speed_kmh ??
        0;

    updateDOMText(
        "speed",
        `${speed} km/h`
    );

    updateDOMText(
        "kpi-speed",
        `${speed} km/h`
    );

    // ------------------------------------------------------
    // SIGNAL TIME
    // ------------------------------------------------------

    if (
        data.signal_time !== undefined
    ) {

        updateDOMText(
            "signalTime",
            `${data.signal_time} Sec`
        );

        updateDOMText(
            "signal-timer",
            `${data.signal_time}s`
        );

    }

    // ------------------------------------------------------
    // RECOMMENDATION
    // ------------------------------------------------------

    if (
        data.recommendation
    ) {

        updateDOMText(
            "recommendation",
            data.recommendation
        );

    }

    // ------------------------------------------------------
    // EMERGENCY
    // ------------------------------------------------------

    updateEmergencyPanel(
        data.ambulances
    );

    // ------------------------------------------------------
    // TABLE
    // ------------------------------------------------------

    renderVehicleTable(
        data
    );

    // ------------------------------------------------------
    // PIE CHART
    // ------------------------------------------------------

    updateVehicleChart(
        data
    );

    console.log(
        "Dashboard numbers updated successfully."
    );
}


// ==========================================================
// EMERGENCY PANEL
// ==========================================================

function updateEmergencyPanel(
    ambulanceCount
) {

    const panel =
        document.getElementById(
            "emergencyPanel"
        );

    if (!panel) {
        return;
    }

    if (
        Number(ambulanceCount) > 0
    ) {

        panel.className =
            "alert alert-danger fw-bold py-2";

        panel.innerHTML = `
            <i class="fas fa-exclamation-triangle me-1"></i>
            EMERGENCY OVERRIDE:
            ${ambulanceCount}
            Ambulance(s) Detected!
        `;

    }

    else {

        panel.className =
            "alert alert-success py-2";

        panel.innerHTML = `
            <i class="fas fa-check-circle me-1"></i>
            No Emergency Vehicle Detected
        `;

    }
}


// ==========================================================
// VIDEO UPLOAD + YOLO PROCESSING
//
// POST /detect/upload
// POST /detect/process/{video_id}
// ==========================================================

async function uploadVideo() {

    console.log(
        "=========================================="
    );

    console.log(
        "VIDEO UPLOAD STARTED"
    );

    console.log(
        "=========================================="
    );

    const fileInput =
        document.getElementById(
            "videoFile"
        );

    const uploadButton =
        document.getElementById(
            "uploadVideoButton"
        );

    // ------------------------------------------------------
    // CHECK INPUT
    // ------------------------------------------------------

    if (!fileInput) {

        console.error(
            "videoFile element not found."
        );

        showUploadStatus(
            "Video input element not found.",
            "danger"
        );

        return;

    }

    // ------------------------------------------------------
    // CHECK FILE
    // ------------------------------------------------------

    if (
        !fileInput.files ||
        fileInput.files.length === 0
    ) {

        showUploadStatus(
            "Please select a traffic video first.",
            "danger"
        );

        return;

    }

    const file =
        fileInput.files[0];

    console.log(
        "Selected file:",
        file.name
    );

    console.log(
        "File size:",
        file.size
    );

    // ------------------------------------------------------
    // CHECK TOKEN
    // ------------------------------------------------------

    const token =
        getAuthToken();

    if (!token) {

        showUploadStatus(
            "Login session expired. Please login again.",
            "danger"
        );

        setTimeout(
            function () {

                window.location.href =
                    "/login";

            },
            1500
        );

        return;

    }

    // ------------------------------------------------------
    // DISABLE BUTTON
    // ------------------------------------------------------

    if (uploadButton) {

        uploadButton.disabled =
            true;

        uploadButton.innerHTML = `
            <span
                class="spinner-border spinner-border-sm me-2">
            </span>
            Uploading Video...
        `;

    }

    showUploadStatus(
        `
        <i class="fas fa-upload me-1"></i>
        Uploading
        <strong>
            ${escapeHtml(file.name)}
        </strong>
        ...
        `,
        "primary"
    );

    try {

        // ==================================================
        // STEP 1 - UPLOAD
        // ==================================================

        const formData =
            new FormData();

        formData.append(
            "file",
            file
        );

        console.log(
            "POST /detect/upload"
        );

        const uploadResponse =
            await fetch(
                "/detect/upload",
                {

                    method:
                        "POST",

                    headers: {

                        "Authorization":
                            `Bearer ${token}`,

                        "Accept":
                            "application/json"

                    },

                    body:
                        formData

                }
            );

        const uploadContentType =
            uploadResponse.headers.get(
                "content-type"
            ) || "";

        let uploadResult;

        if (
            uploadContentType.includes(
                "application/json"
            )
        ) {

            uploadResult =
                await uploadResponse.json();

        }

        else {

            const text =
                await uploadResponse.text();

            uploadResult = {

                detail:
                    text

            };

        }

        console.log(
            "UPLOAD RESPONSE:",
            uploadResult
        );

        if (!uploadResponse.ok) {

            throw new Error(
                uploadResult.detail ||
                uploadResult.message ||
                `Upload failed: ${uploadResponse.status}`
            );

        }

        // ==================================================
        // VIDEO ID
        // ==================================================

        const videoId =
            uploadResult.video_id ||
            uploadResult.id ||
            uploadResult.videoId;

        if (!videoId) {

            throw new Error(
                "Video uploaded, but backend did not return video_id."
            );

        }

        console.log(
            "VIDEO ID:",
            videoId
        );

        showUploadStatus(
            `
            <div class="alert alert-info py-2">

                <i class="fas fa-check-circle me-1"></i>

                <strong>
                    Video uploaded successfully!
                </strong>

                <br>

                <small>
                    Video ID:
                    ${escapeHtml(videoId)}
                </small>

                <br>

                <small>
                    Starting YOLOv8 detection...
                </small>

            </div>
            `,
            "info"
        );

        // --------------------------------------------------
        // BUTTON
        // --------------------------------------------------

        if (uploadButton) {

            uploadButton.innerHTML = `
                <span
                    class="spinner-border spinner-border-sm me-2">
                </span>
                Processing with YOLOv8...
            `;

        }

        // ==================================================
        // STEP 2 - PROCESS
        // ==================================================

        console.log(
            "POST /detect/process/" +
            videoId
        );

        const processResponse =
            await fetch(
                `/detect/process/${videoId}`,
                {

                    method:
                        "POST",

                    headers: {

                        "Authorization":
                            `Bearer ${token}`,

                        "Accept":
                            "application/json"

                    }

                }
            );

        const processContentType =
            processResponse.headers.get(
                "content-type"
            ) || "";

        let processResult;

        if (
            processContentType.includes(
                "application/json"
            )
        ) {

            processResult =
                await processResponse.json();

        }

        else {

            const text =
                await processResponse.text();

            processResult = {

                detail:
                    text

            };

        }

        console.log(
            "=========================================="
        );

        console.log(
            "YOLO PROCESS RESPONSE:",
            processResult
        );

        console.log(
            "=========================================="
        );

        if (!processResponse.ok) {

            throw new Error(
                processResult.detail ||
                processResult.message ||
                `YOLO processing failed: ${processResponse.status}`
            );

        }

        // ==================================================
        // NORMALIZE RESULT
        // ==================================================

        const result =
            normalizeVehicleData(
                processResult
            );

        console.log(
            "FINAL YOLO RESULT:",
            result
        );

        // ==================================================
        // SAVE LATEST VIDEO RESULT
        // ==================================================

        window.latestVideoResult =
            result;

        // ==================================================
        // SHOW RESULT
        // ==================================================

        showUploadStatus(
            `
            <div class="alert alert-success py-2">

                <i class="fas fa-check-circle me-1"></i>

                <strong>
                    Video processed successfully!
                </strong>

                <hr class="my-2">

                <div>
                    <strong>
                        Total Vehicles:
                    </strong>
                    ${result.total_vehicles}
                </div>

                <div>
                    Cars:
                    ${result.cars}
                </div>

                <div>
                    Bikes:
                    ${result.bikes}
                </div>

                <div>
                    Buses:
                    ${result.buses}
                </div>

                <div>
                    Trucks:
                    ${result.trucks}
                </div>

                <div>
                    Auto:
                    ${result.autos}
                </div>

                <div>
                    Ambulance:
                    ${result.ambulances}
                </div>

            </div>
            `,
            "success"
        );

        // ==================================================
        // UPDATE DASHBOARD IMMEDIATELY
        // ==================================================

        updateDashboardFromVideoResult(
            result
        );

        // ==================================================
        // REFRESH ANALYTICS
        // ==================================================

        fetchKPIs();

        fetchAlerts();

        fetchTrafficStatus();

        fetchTrafficTrends();

        // ==================================================
        // ADMIN INCIDENTS
        // ==================================================

        if (
            getUserRole() === "admin" ||
            getUserRole() === "administrator"
        ) {

            loadAdminIncidentMetrics();

            loadAdminIncidents();

        }

        // --------------------------------------------------
        // CLEAR FILE
        // --------------------------------------------------

        fileInput.value = "";

    }

    catch (error) {

        console.error(
            "VIDEO PROCESSING ERROR:",
            error
        );

        showUploadStatus(
            `
            <div class="alert alert-danger py-2">

                <i class="fas fa-times-circle me-1"></i>

                <strong>
                    Video processing failed.
                </strong>

                <br>

                <small>
                    ${escapeHtml(
                        error.message
                    )}
                </small>

            </div>
            `,
            "danger"
        );

    }

    finally {

        if (uploadButton) {

            uploadButton.disabled =
                false;

            uploadButton.innerHTML = `
                <i class="fas fa-cloud-upload-alt me-1"></i>
                Upload & Process Video with YOLOv8
            `;

        }

    }
}


// ==========================================================
// UPLOAD STATUS
// ==========================================================

function showUploadStatus(
    message,
    type = "info"
) {

    const statusDiv =
        document.getElementById(
            "uploadStatus"
        );

    if (!statusDiv) {

        console.warn(
            "uploadStatus element not found."
        );

        return;

    }

    statusDiv.className =
        `text-${type} mt-2 fw-semibold`;

    statusDiv.innerHTML =
        message;
}


// ==========================================================
// ALERTS
// GET /api/alerts
// ==========================================================

async function fetchAlerts() {

    try {

        const token =
            getAuthToken();

        const response =
            await fetch(
                "/api/alerts",
                {

                    headers: {

                        "Accept":
                            "application/json",

                        ...(token
                            ? {
                                "Authorization":
                                    `Bearer ${token}`
                            }
                            : {})

                    }

                }
            );

        if (!response.ok) {

            throw new Error(
                `Alerts API returned ${response.status}`
            );

        }

        const alerts =
            await response.json();

        const alertBox =
            document.getElementById(
                "alertBox"
            ) ||
            document.getElementById(
                "alerts-container"
            );

        if (!alertBox) {
            return;
        }

        if (
            !alerts ||
            !Array.isArray(alerts) ||
            alerts.length === 0
        ) {

            alertBox.innerHTML = `
                <div class="alert alert-success mb-0 py-2">
                    <i class="fas fa-check-circle me-1"></i>
                    No active congestion alerts.
                </div>
            `;

            return;

        }

        alertBox.innerHTML =
            alerts.map(
                function (alert) {

                    const severity =
                        String(
                            alert.severity ||
                            "Medium"
                        ).toLowerCase();

                    const isHigh =
                        severity === "high" ||
                        severity === "critical" ||
                        alert.alert_type ===
                            "Accident";

                    const alertClass =
                        isHigh
                            ? "alert-danger"
                            : "alert-warning";

                    const badgeClass =
                        isHigh
                            ? "bg-danger"
                            : "bg-warning text-dark";

                    return `
                        <div
                            class="alert ${alertClass}
                            p-2 mb-2">

                            <div
                                class="d-flex
                                justify-content-between">

                                <strong>
                                    ${escapeHtml(
                                        alert.alert_type ||
                                        alert.title ||
                                        "Alert"
                                    )}
                                </strong>

                                <span
                                    class="badge
                                    ${badgeClass}">

                                    ${escapeHtml(
                                        alert.severity ||
                                        "Medium"
                                    )}

                                </span>

                            </div>

                            <div class="small mt-1">

                                ${escapeHtml(
                                    alert.description ||
                                    alert.message ||
                                    "Traffic incident detected."
                                )}

                            </div>

                        </div>
                    `;

                }
            ).join("");

    }

    catch (error) {

        console.warn(
            "Could not fetch alerts:",
            error.message
        );

    }
}


// ==========================================================
// KPI
// GET /analytics/kpis
// ==========================================================

async function fetchKPIs() {

    try {

        const response =
            await fetch(
                "/analytics/kpis"
            );

        if (!response.ok) {

            throw new Error(
                `KPI API returned ${response.status}`
            );

        }

        const kpis =
            await response.json();

        console.log(
            "KPI RESPONSE:",
            kpis
        );

        // Latest video has priority
        if (
            window.latestVideoResult &&
            window.latestVideoResult
                .total_vehicles !== undefined
        ) {

            updateDOMText(
                "kpi-total-vehicles",
                window.latestVideoResult
                    .total_vehicles
            );

        }

        else {

            updateDOMText(
                "kpi-total-vehicles",
                kpis.total_vehicles ??
                0
            );

        }

        updateDOMText(
            "kpi-active-alerts",
            kpis.active_alerts ??
            0
        );

        updateDOMText(
            "kpi-total-accidents",
            kpis.total_accidents ??
            0
        );

        updateDOMText(
            "kpi-current-density",
            kpis.current_density ??
            "Low"
        );

        updateDOMText(
            "kpi-alerts",
            kpis.active_alerts ??
            0
        );

    }

    catch (error) {

        console.warn(
            "KPI unavailable:",
            error.message
        );

    }
}


// ==========================================================
// TRAFFIC STATUS
// GET /analytics/traffic-status
// ==========================================================

async function fetchTrafficStatus() {

    try {

        const vehicleCount =
            window.latestVideoResult
                ? window.latestVideoResult
                    .total_vehicles
                : getNumericDOMValue(
                    "totalVehicles"
                );

        const ambulanceCount =
            window.latestVideoResult
                ? window.latestVideoResult
                    .ambulances
                : getNumericDOMValue(
                    "ambulanceCount"
                );

        const url =
            `/analytics/traffic-status` +
            `?vehicle_count=${vehicleCount}` +
            `&emergency_count=${ambulanceCount}`;

        const response =
            await fetch(
                url
            );

        if (!response.ok) {

            throw new Error(
                `Traffic status returned ${response.status}`
            );

        }

        const status =
            await response.json();

        console.log(
            "TRAFFIC STATUS:",
            status
        );

        updateDOMText(
            "recommendation",
            status.recommendation ||
            "Traffic operating within normal parameters."
        );

        updateDOMText(
            "signalTime",
            `${status.signal_time ?? 30} Sec`
        );

        updateDOMText(
            "signal-timer",
            `${status.signal_time ?? 30}s`
        );

        const signalElement =
            document.getElementById(
                "signalStatus"
            );

        if (
            signalElement &&
            status.signal_status
        ) {

            signalElement.innerHTML = `
                <span class="badge bg-success">
                    ${escapeHtml(
                        status.signal_status
                    )}
                </span>
            `;

        }

    }

    catch (error) {

        console.warn(
            "Traffic status unavailable:",
            error.message
        );

    }
}


// ==========================================================
// TRAFFIC TRENDS
// GET /analytics/trends
// ==========================================================

async function fetchTrafficTrends() {

    try {

        const response =
            await fetch(
                "/analytics/trends"
            );

        if (!response.ok) {

            throw new Error(
                `Traffic trends returned ${response.status}`
            );

        }

        const data =
            await response.json();

        const canvas =
            document.getElementById(
                "trafficChart"
            ) ||
            document.getElementById(
                "trafficTrendsChart"
            );

        if (!canvas) {
            return;
        }

        const labels =
            data.hourly_labels ||
            data.labels ||
            [];

        const values =
            data.vehicles_per_hour ||
            data.values ||
            data.counts ||
            [];

        if (
            window.trafficChart
        ) {

            window.trafficChart
                .data
                .labels =
                labels;

            window.trafficChart
                .data
                .datasets[0]
                .data =
                values;

            window.trafficChart.update(
                "none"
            );

        }

    }

    catch (error) {

        console.warn(
            "Traffic trends unavailable:",
            error.message
        );

    }
}


// ==========================================================
// INITIALIZE CHARTS
// ==========================================================

function initializeCharts() {

    if (
        typeof Chart ===
        "undefined"
    ) {

        console.warn(
            "Chart.js is not loaded."
        );

        return;

    }

    // ------------------------------------------------------
    // LINE CHART
    // ------------------------------------------------------

    const trafficCanvas =
        document.getElementById(
            "trafficChart"
        );

    if (trafficCanvas) {

        if (
            window.trafficChart
        ) {

            try {

                window.trafficChart.destroy();

            }

            catch (error) {}

        }

        window.trafficChart =
            new Chart(
                trafficCanvas,
                {

                    type:
                        "line",

                    data: {

                        labels: [
                            "06:00",
                            "08:00",
                            "10:00",
                            "12:00",
                            "14:00",
                            "16:00",
                            "18:00",
                            "20:00"
                        ],

                        datasets: [

                            {

                                label:
                                    "Vehicles / Hr",

                                data: [
                                    0,
                                    0,
                                    0,
                                    0,
                                    0,
                                    0,
                                    0,
                                    0
                                ],

                                borderWidth:
                                    3,

                                tension:
                                    0.3,

                                fill:
                                    true

                            }

                        ]

                    },

                    options: {

                        responsive:
                            true,

                        maintainAspectRatio:
                            false,

                        scales: {

                            y: {

                                beginAtZero:
                                    true

                            }

                        }

                    }

                }
            );

    }

    // ------------------------------------------------------
    // DOUGHNUT CHART
    // ------------------------------------------------------

    const vehicleCanvas =
        document.getElementById(
            "vehicleChart"
        );

    if (vehicleCanvas) {

        if (
            window.pieChart
        ) {

            try {

                window.pieChart.destroy();

            }

            catch (error) {}

        }

        window.pieChart =
            new Chart(
                vehicleCanvas,
                {

                    type:
                        "doughnut",

                    data: {

                        labels: [

                            "Cars",
                            "Bikes",
                            "Buses",
                            "Trucks",
                            "Auto",
                            "Ambulance"

                        ],

                        datasets: [

                            {

                                data: [
                                    0,
                                    0,
                                    0,
                                    0,
                                    0,
                                    0
                                ],

                                backgroundColor: [

                                    "#2563eb",
                                    "#f59e0b",
                                    "#16a34a",
                                    "#dc2626",
                                    "#06b6d4",
                                    "#ef4444"

                                ]

                            }

                        ]

                    },

                    options: {

                        responsive:
                            true,

                        maintainAspectRatio:
                            false

                    }

                }
            );

    }
}


// ==========================================================
// UPDATE VEHICLE CHART
// ==========================================================

function updateVehicleChart(
    rawData
) {

    if (
        !window.pieChart
    ) {

        return;

    }

    const data =
        normalizeVehicleData(
            rawData
        );

    window.pieChart
        .data
        .datasets[0]
        .data = [

            data.cars,
            data.bikes,
            data.buses,
            data.trucks,
            data.autos,
            data.ambulances

        ];

    window.pieChart.update(
        "none"
    );
}


// ==========================================================
// VEHICLE TABLE
// ==========================================================

function renderVehicleTable(
    rawData
) {

    const table =
        document.getElementById(
            "vehicleTable"
        );

    if (!table) {
        return;
    }

    const data =
        normalizeVehicleData(
            rawData
        );

    const items = [

        {
            type:
                "Cars",

            count:
                data.cars
        },

        {
            type:
                "Bikes / Motorcycles",

            count:
                data.bikes
        },

        {
            type:
                "Buses",

            count:
                data.buses
        },

        {
            type:
                "Trucks",

            count:
                data.trucks
        },

        {
            type:
                "Auto Rickshaws",

            count:
                data.autos
        },

        {
            type:
                "Ambulances",

            count:
                data.ambulances
        }

    ];

    table.innerHTML =
        items.map(
            function (item) {

                return `
                    <tr>

                        <td>

                            <strong>
                                ${escapeHtml(
                                    item.type
                                )}
                            </strong>

                        </td>

                        <td>

                            <span
                                class="badge
                                bg-secondary
                                fs-6">

                                ${item.count}

                            </span>

                        </td>

                    </tr>
                `;

            }
        ).join("");
}


// ==========================================================
// OPENSTREETMAP HEATMAP
// GET /api/heatmap
// ==========================================================

async function loadHeatmap() {

    const mapElement =
        document.getElementById(
            "traffic-map"
        ) ||
        document.getElementById(
            "map"
        );

    if (!mapElement) {
        return;
    }

    if (
        typeof L ===
        "undefined"
    ) {

        console.warn(
            "Leaflet is not loaded."
        );

        return;

    }

    try {

        let points = [];

        const response =
            await fetch(
                "/api/heatmap"
            );

        if (response.ok) {

            const heatmapData =
                await response.json();

            const rawPoints =
                heatmapData.points ||
                heatmapData ||
                [];

            if (
                Array.isArray(
                    rawPoints
                )
            ) {

                points =
                    rawPoints.map(
                        function (point) {

                            if (
                                Array.isArray(
                                    point
                                )
                            ) {

                                return point;

                            }

                            return [

                                point.lat,

                                point.lng,

                                point.intensity ??
                                    0.6

                            ];

                        }
                    );

            }

        }

        // --------------------------------------------------
        // CREATE MAP
        // --------------------------------------------------

        if (
            !window.leafletMap
        ) {

            window.leafletMap =
                L.map(
                    mapElement.id
                ).setView(
                    [
                        15.8281,
                        78.0373
                    ],
                    6
                );

            L.tileLayer(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                {

                    attribution:
                        "© OpenStreetMap contributors"

                }
            ).addTo(
                window.leafletMap
            );

        }

        // --------------------------------------------------
        // HEAT LAYER
        // --------------------------------------------------

        if (
            typeof L.heatLayer ===
            "function"
        ) {

            if (
                window.heatLayer
            ) {

                window.leafletMap
                    .removeLayer(
                        window.heatLayer
                    );

            }

            window.heatLayer =
                L.heatLayer(
                    points,
                    {

                        radius:
                            25,

                        blur:
                            15,

                        maxZoom:
                            17

                    }
                ).addTo(
                    window.leafletMap
                );

        }

    }

    catch (error) {

        console.warn(
            "Heatmap unavailable:",
            error.message
        );

    }
}


// ==========================================================
// ADMIN INCIDENT NAVIGATION
// ==========================================================

function showIncidentNavigationForAdmin() {

    const incidentNav =
        document.getElementById(
            "incidentNav"
        );

    if (!incidentNav) {
        return;
    }

    const userData =
        localStorage.getItem(
            "user"
        );

    if (!userData) {

        incidentNav.style.display =
            "none";

        return;

    }

    try {

        const user =
            JSON.parse(
                userData
            );

        const role = (
            user.role ||
            user.user_role ||
            ""
        )
            .toString()
            .trim()
            .toLowerCase();

        if (
            role === "admin" ||
            role === "administrator"
        ) {

            incidentNav.style.display =
                "block";

        }

        else {

            incidentNav.style.display =
                "none";

        }

    }

    catch (error) {

        console.error(
            "Unable to read logged-in user:",
            error
        );

        incidentNav.style.display =
            "none";

    }
}


// ==========================================================
// ADMIN INCIDENTS
// GET /api/incidents
// ==========================================================

async function loadAdminIncidents() {

    const userData =
        localStorage.getItem(
            "user"
        );

    const token =
        getAuthToken();

    if (
        !userData ||
        !token
    ) {

        return;

    }

    let user;

    try {

        user =
            JSON.parse(
                userData
            );

    }

    catch (error) {

        console.warn(
            "Unable to parse user data."
        );

        return;

    }

    const role = (
        user.role ||
        user.user_role ||
        ""
    )
        .toString()
        .trim()
        .toLowerCase();

    // ------------------------------------------------------
    // SUPPORT BOTH IDs
    // ------------------------------------------------------

    const section =
        document.getElementById(
            "adminIncidentSection"
        ) ||
        document.getElementById(
            "adminIncidentsSection"
        );

    const container =
        document.getElementById(
            "dashboardIncidentContainer"
        );

    if (
        !section ||
        !container
    ) {

        return;

    }

    // ------------------------------------------------------
    // ADMIN ONLY
    // ------------------------------------------------------

    if (
        role !== "admin" &&
        role !== "administrator"
    ) {

        section.style.display =
            "none";

        return;

    }

    section.style.display =
        "block";

    try {

        const response =
            await fetch(
                "/api/incidents",
                {

                    method:
                        "GET",

                    headers: {

                        "Authorization":
                            `Bearer ${token}`,

                        "Accept":
                            "application/json"

                    }

                }
            );

        if (
            response.status === 401
        ) {

            localStorage.clear();

            window.location.href =
                "/login";

            return;

        }

        if (
            response.status === 403
        ) {

            section.style.display =
                "none";

            return;

        }

        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }

        const incidents =
            await response.json();

        // --------------------------------------------------
        // CHECK ARRAY
        // --------------------------------------------------

        if (
            !Array.isArray(
                incidents
            )
        ) {

            console.warn(
                "Incidents API did not return an array:",
                incidents
            );

            container.innerHTML = `
                <div class="alert alert-warning">
                    Invalid incident data received.
                </div>
            `;

            return;

        }

        // --------------------------------------------------
        // NO INCIDENTS
        // --------------------------------------------------

        if (
            incidents.length === 0
        ) {

            container.innerHTML = `
                <div class="no-incidents">

                    <h3>
                        No Incidents Found
                    </h3>

                    <p>
                        There are currently no
                        traffic incidents.
                    </p>

                </div>
            `;

            return;

        }

        // --------------------------------------------------
        // SHOW ONLY LATEST 5
        // --------------------------------------------------

        container.innerHTML =
            incidents
                .slice(0, 5)
                .map(
                    function (incident) {

                        const status =
                            String(
                                incident.status ||
                                "Unknown"
                            );

                        const severity =
                            String(
                                incident.severity ||
                                "Unknown"
                            );

                        return `
                            <div
                                class="incident-card
                                border rounded p-3 mb-3">

                                <h3>
                                    ${escapeHtml(
                                        incident.title ||
                                        incident.alert_type ||
                                        "Traffic Incident"
                                    )}
                                </h3>

                                <p>
                                    <strong>
                                        Location:
                                    </strong>

                                    ${escapeHtml(
                                        incident.location ||
                                        "Unknown"
                                    )}
                                </p>

                                <p>
                                    <strong>
                                        Severity:
                                    </strong>

                                    <span
                                        class="badge
                                        bg-warning text-dark">

                                        ${escapeHtml(
                                            severity
                                        )}

                                    </span>
                                </p>

                                <p>
                                    <strong>
                                        Status:
                                    </strong>

                                    ${escapeHtml(
                                        status
                                    )}
                                </p>

                                <p>
                                    ${escapeHtml(
                                        incident.description ||
                                        incident.message ||
                                        "No description"
                                    )}
                                </p>

                            </div>
                        `;

                    }
                )
                .join("");

    }

    catch (error) {

        console.error(
            "Admin incident error:",
            error
        );

        container.innerHTML = `
            <div class="alert alert-danger">
                Unable to load incidents.
            </div>
        `;

    }
}


// ==========================================================
// ADMIN INCIDENT METRICS
// ==========================================================

async function loadAdminIncidentMetrics() {

    const role =
        getUserRole();

    if (
        role !== "admin" &&
        role !== "administrator"
    ) {

        return;

    }

    const token =
        getAuthToken();

    if (!token) {
        return;
    }

    try {

        const response =
            await fetch(
                "/api/incidents",
                {

                    headers: {

                        "Authorization":
                            `Bearer ${token}`,

                        "Accept":
                            "application/json"

                    }

                }
            );

        if (
            response.status === 401
        ) {

            localStorage.clear();

            window.location.href =
                "/login";

            return;

        }

        if (!response.ok) {

            console.warn(
                "Incident API returned:",
                response.status
            );

            return;

        }

        const incidents =
            await response.json();

        if (
            !Array.isArray(
                incidents
            )
        ) {

            return;

        }

        const active =
            incidents.filter(
                function (incident) {

                    return String(
                        incident.status ||
                        ""
                    )
                        .toLowerCase() ===
                        "active";

                }
            ).length;

        const critical =
            incidents.filter(
                function (incident) {

                    return String(
                        incident.severity ||
                        ""
                    )
                        .toLowerCase() ===
                        "critical";

                }
            ).length;

        const resolved =
            incidents.filter(
                function (incident) {

                    return String(
                        incident.status ||
                        ""
                    )
                        .toLowerCase() ===
                        "resolved";

                }
            ).length;

        updateDOMText(
            "activeIncidents",
            active
        );

        updateDOMText(
            "criticalIncidents",
            critical
        );

        updateDOMText(
            "resolvedIncidents",
            resolved
        );

    }

    catch (error) {

        console.warn(
            "Incident metrics unavailable:",
            error.message
        );

    }
}


// ==========================================================
// RESOLVE ALERT
// ==========================================================

async function resolveAlert(
    alertId
) {

    try {

        const response =
            await fetch(
                `/alerts/resolve/${alertId}`,
                {

                    method:
                        "POST",

                    headers: {

                        "Authorization":
                            `Bearer ${getAuthToken()}`

                    }

                }
            );

        if (
            response.ok
        ) {

            fetchAlerts();

            fetchKPIs();

        }

        else {

            console.warn(
                "Unable to resolve alert:",
                response.status
            );

        }

    }

    catch (error) {

        console.error(
            "Error resolving alert:",
            error
        );

    }
}


// ==========================================================
// AI RECOMMENDATION
// ==========================================================

async function fetchAIRecommendation() {

    const roadInput =
        document.getElementById(
            "road-input"
        );

    const densityInput =
        document.getElementById(
            "density-input"
        );

    const output =
        document.getElementById(
            "ai-recommendation-output"
        );

    if (
        !roadInput ||
        !densityInput
    ) {

        return;

    }

    const road =
        roadInput.value.trim();

    const density =
        parseFloat(
            densityInput.value
        ) || 0;

    try {

        const response =
            await fetch(
                "/recommendation/suggest",
                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${getAuthToken()}`

                    },

                    body:
                        JSON.stringify({

                            road_name:
                                road,

                            density:
                                density,

                            time_of_day:
                                "08:30 AM"

                        })

                }
            );

        const result =
            await response.json();

        if (!response.ok) {

            throw new Error(
                result.detail ||
                "Recommendation request failed."
            );

        }

        if (output) {

            output.classList.remove(
                "d-none"
            );

            output.innerHTML = `

                <strong>
                    Action Required:
                </strong>

                <span
                    class="badge bg-danger">

                    ${escapeHtml(
                        result.action ||
                        "Reroute"
                    )}

                </span>

                <br>

                <strong>
                    AI Suggestion:
                </strong>

                ${escapeHtml(
                    result.recommendation ||
                    "No recommendation available."
                )}

                <br>

                <small
                    class="text-success fw-bold">

                    Estimated Delay Saved:
                    ${escapeHtml(
                        result.estimated_time_saved ||
                        "15 mins"
                    )}

                </small>

            `;

        }

    }

    catch (error) {

        console.error(
            "AI recommendation error:",
            error
        );

    }
}


// ==========================================================
// ERROR BOX
// ==========================================================

function clearError() {

    const errorBox =
        document.getElementById(
            "errorBox"
        );

    if (errorBox) {

        errorBox.innerHTML =
            "";

    }
}


// ==========================================================
// DOM UPDATE
// ==========================================================

function updateDOMText(
    elementId,
    text
) {

    const element =
        document.getElementById(
            elementId
        );

    if (element) {

        element.innerText =
            text;

    }
}


// ==========================================================
// NUMERIC DOM VALUE
// ==========================================================

function getNumericDOMValue(
    elementId
) {

    const element =
        document.getElementById(
            elementId
        );

    if (!element) {

        return 0;

    }

    const value =
        parseFloat(
            String(
                element.innerText
            )
                .replace(
                    /[^0-9.-]/g,
                    ""
                )
        );

    return Number.isFinite(
        value
    )
        ? value
        : 0;
}


// ==========================================================
// HTML ESCAPE
// ==========================================================

function escapeHtml(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }

    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );
}


// Keep both spellings available.
// Your original code used escapeHTML in the
// admin incident function.

function escapeHTML(
    value
) {

    return escapeHtml(
        value
    );

}


// ==========================================================
// SESSION MONITOR
// ==========================================================

function sessionExpired() {

    const token =
        getAuthToken();

    if (!token) {

        console.warn(
            "JWT token missing."
        );

        window.location.href =
            "/login";

    }
}

setInterval(
    sessionExpired,
    60000
);


// ==========================================================
// VIDEO PREVIEW
// ==========================================================

function initializeVideoPreview() {

    document.addEventListener(
        "change",
        function (event) {

            if (
                event.target.id !==
                "videoFile"
            ) {

                return;

            }

            const file =
                event.target.files &&
                event.target.files[0];

            if (!file) {
                return;
            }

            console.log(
                "Selected video:",
                file.name
            );

            let preview =
                document.getElementById(
                    "videoPreview"
                );

            if (!preview) {

                preview =
                    document.createElement(
                        "video"
                    );

                preview.id =
                    "videoPreview";

                preview.controls =
                    true;

                preview.className =
                    "w-100 rounded mt-3";

                preview.style.maxHeight =
                    "300px";

                event.target.parentElement
                    .appendChild(
                        preview
                    );

            }

            const objectUrl =
                URL.createObjectURL(
                    file
                );

            preview.src =
                objectUrl;

            preview.load();

        }
    );
}


// ==========================================================
// CLEANUP
// ==========================================================

window.addEventListener(
    "beforeunload",
    function () {

        if (
            window.dashboardInterval
        ) {

            clearInterval(
                window.dashboardInterval
            );

            window.dashboardInterval =
                null;

        }

        if (
            window.dashboardSlowInterval
        ) {

            clearInterval(
                window.dashboardSlowInterval
            );

            window.dashboardSlowInterval =
                null;

        }

    }
);


// ==========================================================
// MAKE FUNCTIONS AVAILABLE TO HTML
// ==========================================================

window.uploadVideo =
    uploadVideo;

window.fetchDashboardData =
    fetchDashboardData;

window.fetchAlerts =
    fetchAlerts;

window.fetchKPIs =
    fetchKPIs;

window.fetchTrafficStatus =
    fetchTrafficStatus;

window.fetchTrafficTrends =
    fetchTrafficTrends;

window.loadHeatmap =
    loadHeatmap;

window.fetchAIRecommendation =
    fetchAIRecommendation;

window.resolveAlert =
    resolveAlert;

window.updateDashboardFromVideoResult =
    updateDashboardFromVideoResult;

window.loadAdminIncidents =
    loadAdminIncidents;

window.loadAdminIncidentMetrics =
    loadAdminIncidentMetrics;

window.showIncidentNavigationForAdmin =
    showIncidentNavigationForAdmin;


// ==========================================================
// END
// ==========================================================

console.log(
    "AI Traffic Dashboard JS loaded successfully."
);