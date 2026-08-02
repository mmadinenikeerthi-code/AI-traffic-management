// ==========================================================
// frontend/static/js/analytics.js
// Charts, KPI Summary & AI Recommendation Frontend Logic
// ==========================================================

let hourlyTrendChart = null;
let vehicleDistChart = null;

async function loadAnalyticsDashboard() {
    await fetchKPIs();
    await fetchTrendCharts();
}

// 1. Fetch KPI Cards Data
async function fetchKPIs() {
    try {
        const res = await fetch('/analytics/summary');
        const data = await res.json();

        if (document.getElementById('totalVehicles')) document.getElementById('totalVehicles').innerText = data.total_vehicles.toLocaleString();
        if (document.getElementById('congestionLevel')) document.getElementById('congestionLevel').innerText = data.congestion_level;
        if (document.getElementById('alertsToday')) document.getElementById('alertsToday').innerText = data.alerts_today;
        if (document.getElementById('avgSpeed')) document.getElementById('avgSpeed').innerText = `${data.average_speed_kmh} km/h`;
        if (document.getElementById('peakHour')) document.getElementById('peakHour').innerText = data.peak_traffic_hour;

        renderVehicleDistributionChart(data.vehicle_type_distribution);
    } catch (err) {
        console.error("Failed to load KPIs:", err);
    }
}

// 2. Render Vehicle Type Distribution Pie Chart
function renderVehicleDistributionChart(distData) {
    const ctx = document.getElementById('vehicleTypeChart');
    if (!ctx) return;

    if (vehicleDistChart) vehicleDistChart.destroy();

    vehicleDistChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(distData),
            datasets: [{
                data: Object.values(distData),
                backgroundColor: ['#2563eb', '#f59e0b', '#16a34a', '#dc2626', '#06b6d4']
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

// 3. Fetch Trend Charts Data (Step 4)
async function fetchTrendCharts() {
    const ctx = document.getElementById('trendAnalysisChart');
    if (!ctx) return;

    try {
        const res = await fetch('/analytics/trends');
        const trends = await res.json();

        if (hourlyTrendChart) hourlyTrendChart.destroy();

        hourlyTrendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: trends.hourly_labels,
                datasets: [
                    {
                        label: 'Vehicles / Hr',
                        data: trends.vehicles_per_hour,
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Congestion %',
                        data: trends.congestion_percentage,
                        borderColor: '#dc2626',
                        borderDash: [5, 5],
                        tension: 0.3
                    }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    } catch (err) {
        console.error("Failed to load trend charts:", err);
    }
}

// 4. Submit AI Recommendation Query (Step 3)
async function submitAIRecommendation() {
    const road = document.getElementById('road-input').value;
    const density = parseFloat(document.getElementById('density-input').value);

    try {
        const res = await fetch('/recommendation/suggest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ road_name: road, density: density, time_of_day: "08:30 AM" })
        });

        const result = await res.json();
        const outputDiv = document.getElementById('ai-recommendation-output');
        outputDiv.classList.remove('d-none');
        outputDiv.innerHTML = `
            <strong>Action:</strong> <span class="badge bg-danger">${result.action}</span><br>
            <strong>Suggestion:</strong> ${result.recommendation}<br>
            <small class="text-success fw-bold">Time Saved: ${result.estimated_time_saved}</small>
        `;

        if (density >= 80 && typeof triggerNotification === 'function') {
            triggerNotification(`🚨 Congestion Alert: ${road}`, `Density reached ${density}%. Alternate route advised.`, 'error');
        }
    } catch (err) {
        console.error("AI Recommendation error:", err);
    }
}

document.addEventListener("DOMContentLoaded", () => loadAnalyticsDashboard());