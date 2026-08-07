// ==========================================================
// static/js/traffic-gis.js
// Complete Unified Traffic GIS, Heatmap, and Search Engine
// ==========================================================

let map = null;
let heatLayer = null;
let trafficMarkers = [];
let selectedLocationMarker = null;

document.addEventListener("DOMContentLoaded", function () {
    console.log("======================================");
    console.log("AI TRAFFIC GIS INITIALIZING");
    console.log("======================================");

    // ========================================================
    // MAP INITIALIZATION
    // ========================================================
    map = L.map("map", {
        zoomControl: true
    }).setView([20.5937, 78.9629], 5);

    // ========================================================
    // OPENSTREETMAP
    // ========================================================
    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap contributors'
        }
    ).addTo(map);

    console.log("OpenStreetMap loaded");

    // ========================================================
    // SEARCH ELEMENTS
    // ========================================================
    const searchInput = document.getElementById("locationSearch");
    const searchBtn = document.getElementById("searchBtn");
    const refreshBtn = document.getElementById("refreshBtn");
    const suggestions = document.getElementById("suggestions");

    /* ========================================================
       TRAFFIC COLORS & LEVELS
    ======================================================== */
    function trafficColor(intensity) {
        intensity = Number(intensity) || 0;
        if (intensity >= 0.70) {
            return "#ff2633"; // Heavy
        }
        if (intensity >= 0.40) {
            return "#22d66f"; // Moderate
        }
        return "#ffd429"; // Low
    }

    function trafficLevel(intensity) {
        intensity = Number(intensity) || 0;
        if (intensity >= 0.70) {
            return "HEAVY";
        }
        if (intensity >= 0.40) {
            return "MODERATE";
        }
        return "LOW";
    }

    /* ========================================================
       CREATE TRAFFIC MARKER
    ======================================================== */
    function createTrafficMarker(point) {
        const lat = Number(point.lat);
        const lng = Number(point.lng);
        const intensity = Number(point.intensity ?? 0);

        if (Number.isNaN(lat) || Number.isNaN(lng)) {
            return null;
        }

        const level = point.level || trafficLevel(intensity);
        const color = trafficColor(intensity);

        const marker = L.circleMarker([lat, lng], {
            radius: 10 + intensity * 8,
            color: "#ffffff",
            weight: 1.5,
            fillColor: color,
            fillOpacity: 0.85
        });

        marker.bindPopup(`
            <div style="min-width:180px">
                <b>${escapeHtml(point.road || point.name || "Traffic Location")}</b>
                <hr style="margin:7px 0">
                <b>Level:</b> ${level}<br>
                <b>Vehicles:</b> ${point.vehicle_count ?? "--"}<br>
                <b>Speed:</b> ${point.speed ?? "--"}<br>
                <b>Intensity:</b> ${intensity.toFixed(2)}
            </div>
        `);

        marker.on("click", function () {
            selectTrafficPoint(point);
        });

        marker.addTo(map);
        trafficMarkers.push(marker);
        return marker;
    }

    /* ========================================================
       LOAD TRAFFIC DATA
    ======================================================== */
    async function loadTrafficData() {
        console.log("Loading traffic data...");

        try {
            const response = await fetch("/heatmap/points", {
                method: "GET"
            });

            if (!response.ok) {
                throw new Error("Heatmap API returned HTTP " + response.status);
            }

            const rawData = await response.json();
            console.log("Backend heatmap response:", rawData);

            let points = [];

            if (Array.isArray(rawData)) {
                points = rawData;
            } else if (rawData && Array.isArray(rawData.points)) {
                points = rawData.points.map(p => {
                    if (Array.isArray(p)) {
                        return {
                            lat: p[0],
                            lng: p[1],
                            intensity: p[2],
                            level: trafficLevel(p[2]),
                            vehicle_count: "--",
                            speed: "--",
                            road: "Traffic Zone"
                        };
                    }
                    return p;
                });
            }

            clearTrafficMarkers();
            points.forEach(createTrafficMarker);
            createHeatmap(points);
            updateTrafficList(points);

            console.log("Traffic points displayed:", points.length);

            if (points.length === 0) {
                showDemoTraffic(map.getCenter().lat, map.getCenter().lng);
            }
        } catch (error) {
            console.error("Traffic API error:", error);
            showDemoTraffic(map.getCenter().lat, map.getCenter().lng);
        }
    }

    /* ========================================================
       CREATE HEATMAP
    ======================================================== */
    function createHeatmap(points) {
        if (heatLayer) {
            map.removeLayer(heatLayer);
        }

        const heatPoints = points.map(point => {
            const lat = Number(point.lat);
            const lng = Number(point.lng);
            const intensity = Number(point.intensity ?? 0.5);

            if (Number.isNaN(lat) || Number.isNaN(lng)) {
                return null;
            }

            return [
                lat,
                lng,
                Math.max(0.15, Math.min(intensity, 1))
            ];
        }).filter(Boolean);

        if (typeof L.heatLayer === "function" && heatPoints.length) {
            heatLayer = L.heatLayer(heatPoints, {
                radius: 35,
                blur: 25,
                maxZoom: 12,
                minOpacity: 0.35,
                gradient: {
                    0.20: "#ffd429",
                    0.40: "#22d66f",
                    0.70: "#ff8c00",
                    1.00: "#ff2633"
                }
            }).addTo(map);
        }
    }

    /* ========================================================
       CLEAR MARKERS
    ======================================================== */
    function clearTrafficMarkers() {
        trafficMarkers.forEach(marker => {
            map.removeLayer(marker);
        });
        trafficMarkers = [];
    }

    /* ========================================================
       TRAFFIC LIST PANEL UPDATE
    ======================================================== */
    function updateTrafficList(points) {
        const list = document.getElementById("trafficList");
        if (!list) return;

        if (!points.length) {
            list.innerHTML = `
                <div style="color:#72838b;font-size:11px;">
                    No traffic points available.
                </div>
            `;
            return;
        }

        list.innerHTML = points.slice(0, 30).map((point, index) => {
            const intensity = Number(point.intensity ?? 0);
            const level = point.level || trafficLevel(intensity);

            let badgeClass = "badge-low";
            if (level.toUpperCase() === "HEAVY") {
                badgeClass = "badge-heavy";
            } else if (level.toUpperCase() === "MODERATE") {
                badgeClass = "badge-moderate";
            }

            return `
                <div class="traffic-item" data-index="${index}">
                    <div class="d-flex justify-content-between">
                        <span class="traffic-road">
                            ${escapeHtml(point.road || point.name || "Traffic Zone")}
                        </span>
                        <span class="level-badge ${badgeClass}">
                            ${level}
                        </span>
                    </div>
                    <div class="traffic-info">
                        <span>Vehicles: ${point.vehicle_count ?? "--"}</span>
                        <span>Speed: ${point.speed ?? "--"}</span>
                    </div>
                </div>
            `;
        }).join("");

        document.querySelectorAll(".traffic-item").forEach(item => {
            item.addEventListener("click", function () {
                const index = Number(this.dataset.index);
                const point = points[index];
                if (!point) return;

                const lat = Number(point.lat);
                const lng = Number(point.lng);

                map.setView([lat, lng], 14);
                selectTrafficPoint(point);
            });
        });
    }

    /* ========================================================
       SELECT TRAFFIC POINT
    ======================================================== */
    function selectTrafficPoint(point) {
        const intensity = Number(point.intensity ?? 0);
        const level = point.level || trafficLevel(intensity);

        const placeEl = document.getElementById("selectedPlace");
        const latEl = document.getElementById("selectedLat");
        const lngEl = document.getElementById("selectedLng");
        const statusEl = document.getElementById("trafficStatus");
        const vehicleEl = document.getElementById("vehicleCount");
        const speedEl = document.getElementById("averageSpeed");
        const congestionEl = document.getElementById("congestionValue");

        if (placeEl) placeEl.textContent = point.road || point.name || "Traffic Location";
        if (latEl) latEl.textContent = Number(point.lat).toFixed(5);
        if (lngEl) lngEl.textContent = Number(point.lng).toFixed(5);
        if (statusEl) statusEl.textContent = level;
        if (vehicleEl) vehicleEl.textContent = point.vehicle_count ?? "--";
        if (speedEl) speedEl.textContent = point.speed ?? "--";
        if (congestionEl) congestionEl.textContent = Math.round(intensity * 100) + "%";

        generateAdvice(point, level, intensity);
    }

    /* ========================================================
       AI ADVISORY
    ======================================================== */
    function generateAdvice(point, level, intensity) {
        const advice = document.getElementById("aiAdvice");
        if (!advice) return;

        if (level.toUpperCase() === "HEAVY") {
            advice.innerHTML = `
                <div class="advice">
                    <div class="advice-title">Critical</div>
                    <div class="advice-heading">Persistent congestion</div>
                    <div class="advice-text">
                        Heavy traffic detected at ${escapeHtml(point.road || "selected location")}.
                        Consider alternate routes and traffic signal optimization.
                    </div>
                </div>
            `;
        } else if (level.toUpperCase() === "MODERATE") {
            advice.innerHTML = `
                <div class="advice">
                    <div class="advice-title">Advisory</div>
                    <div class="advice-heading">Moderate traffic</div>
                    <div class="advice-text">
                        Traffic is currently moderate. Continue monitoring vehicle density and average speed.
                    </div>
                </div>
            `;
        } else {
            advice.innerHTML = `
                <div class="advice">
                    <div class="advice-title">Normal</div>
                    <div class="advice-heading">Traffic flowing normally</div>
                    <div class="advice-text">
                        Low congestion detected. Current route conditions appear favorable.
                    </div>
                </div>
            `;
        }
    }

    /* ========================================================
       SEARCH OPENSTREETMAP / NOMINATIM
    ======================================================== */
    let searchTimer = null;

    if (searchInput) {
        searchInput.addEventListener("input", function () {
            const query = this.value.trim();
            clearTimeout(searchTimer);

            if (query.length < 3) {
                if (suggestions) suggestions.style.display = "none";
                return;
            }

            searchTimer = setTimeout(() => {
                getSuggestions(query);
            }, 400);
        });
    }

    async function getSuggestions(query) {
        try {
            const url = "https://nominatim.openstreetmap.org/search?" + new URLSearchParams({
                q: query,
                format: "json",
                addressdetails: "1",
                limit: "6",
                "accept-language": "en"
            });

            const response = await fetch(url, {
                headers: { "Accept": "application/json" }
            });

            if (!response.ok) throw new Error("Nominatim error");

            const results = await response.json();
            if (!suggestions) return;

            suggestions.innerHTML = "";
            if (!results.length) {
                suggestions.style.display = "none";
                return;
            }

            results.forEach(result => {
                const div = document.createElement("div");
                div.className = "suggestion";
                div.textContent = result.display_name;

                div.addEventListener("click", function () {
                    searchInput.value = result.display_name;
                    suggestions.style.display = "none";
                    showLocation(Number(result.lat), Number(result.lon), result.display_name);
                });

                suggestions.appendChild(div);
            });

            suggestions.style.display = "block";
        } catch (error) {
            console.error("Location search error:", error);
        }
    }

    /* ========================================================
       SEARCH BUTTON
    ======================================================== */
    if (searchBtn) {
        searchBtn.addEventListener("click", performSearch);
    }

    if (searchInput) {
        searchInput.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                performSearch();
            }
        });
    }

    async function performSearch() {
        if (!searchInput) return;
        const query = searchInput.value.trim();

        if (!query) {
            alert("Please enter a city, road, place or location.");
            return;
        }

        if (suggestions) suggestions.style.display = "none";
        if (searchBtn) {
            searchBtn.disabled = true;
            searchBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Searching';
        }

        try {
            const url = "https://nominatim.openstreetmap.org/search?" + new URLSearchParams({
                q: query,
                format: "json",
                addressdetails: "1",
                limit: "1"
            });

            const response = await fetch(url, {
                headers: { "Accept": "application/json" }
            });

            const results = await response.json();

            if (!results.length) {
                alert("Location not found. Try another city, road or place.");
                return;
            }

            const result = results[0];
            showLocation(Number(result.lat), Number(result.lon), result.display_name);
        } catch (error) {
            console.error(error);
            alert("Unable to search location.");
        } finally {
            if (searchBtn) {
                searchBtn.disabled = false;
                searchBtn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Search';
            }
        }
    }

    /* ========================================================
       SHOW SEARCHED LOCATION
    ======================================================== */
    function showLocation(lat, lng, name) {
        map.setView([lat, lng], 13);

        if (selectedLocationMarker) {
            map.removeLayer(selectedLocationMarker);
        }

        selectedLocationMarker = L.marker([lat, lng])
            .addTo(map)
            .bindPopup(`<b>${escapeHtml(name)}</b>`)
            .openPopup();

        const placeEl = document.getElementById("selectedPlace");
        const latEl = document.getElementById("selectedLat");
        const lngEl = document.getElementById("selectedLng");

        if (placeEl) placeEl.textContent = name;
        if (latEl) latEl.textContent = lat.toFixed(5);
        if (lngEl) lngEl.textContent = lng.toFixed(5);

        loadTrafficDataForLocation(lat, lng);
    }

    /* ========================================================
       LOAD TRAFFIC AROUND SEARCHED LOCATION
    ======================================================== */
    async function loadTrafficDataForLocation(lat, lng) {
        try {
            const response = await fetch("/heatmap/points");
            if (response.ok) {
                const data = await response.json();
                let points = normalizeHeatmapData(data);

                if (points.length) {
                    const nearby = points.filter(p =>
                        distanceKm(lat, lng, Number(p.lat), Number(p.lng)) <= 100
                    );

                    if (nearby.length) {
                        clearTrafficMarkers();
                        nearby.forEach(createTrafficMarker);
                        createHeatmap(nearby);
                        updateTrafficList(nearby);
                        return;
                    }
                }
            }
        } catch (error) {
            console.log("No location-specific backend traffic data.");
        }

        showDemoTraffic(lat, lng);
    }

    function normalizeHeatmapData(rawData) {
        if (Array.isArray(rawData)) return rawData;
        if (rawData && Array.isArray(rawData.points)) {
            return rawData.points.map(p => {
                if (Array.isArray(p)) {
                    return {
                        lat: p[0],
                        lng: p[1],
                        intensity: p[2],
                        level: trafficLevel(p[2]),
                        vehicle_count: Math.round(50 + p[2] * 300),
                        speed: Math.round(45 - p[2] * 35) + " km/h",
                        road: "Traffic Zone"
                    };
                }
                return p;
            });
        }
        return [];
    }

    /* ========================================================
       DEMO TRAFFIC GENERATOR
    ======================================================== */
    function showDemoTraffic(centerLat, centerLng) {
        clearTrafficMarkers();

        const locations = [
            { lat: centerLat + 0.015, lng: centerLng + 0.010, intensity: 0.90, level: "HEAVY", vehicle_count: 220, speed: "12 km/h", road: "Major Junction" },
            { lat: centerLat - 0.010, lng: centerLng + 0.018, intensity: 0.58, level: "MODERATE", vehicle_count: 130, speed: "28 km/h", road: "Main Road" },
            { lat: centerLat + 0.006, lng: centerLng - 0.020, intensity: 0.28, level: "LOW", vehicle_count: 65, speed: "45 km/h", road: "Local Road" },
            { lat: centerLat - 0.020, lng: centerLng - 0.012, intensity: 0.78, level: "HEAVY", vehicle_count: 185, speed: "15 km/h", road: "Ring Road" },
            { lat: centerLat + 0.022, lng: centerLng - 0.008, intensity: 0.43, level: "MODERATE", vehicle_count: 105, speed: "31 km/h", road: "City Connector" }
        ];

        locations.forEach(createTrafficMarker);
        createHeatmap(locations);
        updateTrafficList(locations);
        selectTrafficPoint(locations[0]);
    }

    if (refreshBtn) {
        refreshBtn.addEventListener("click", function () {
            loadTrafficData();
        });
    }

    function distanceKm(lat1, lon1, lat2, lon2) {
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    }

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    document.addEventListener("click", function (event) {
        if (!event.target.closest(".search-wrapper")) {
            if (suggestions) suggestions.style.display = "none";
        }
    });

    setTimeout(function () {
        map.invalidateSize();
        loadTrafficData();
    }, 500);
});