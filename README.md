# 🚦 AI-Driven Traffic Management & Route Optimization System

An intelligent, interactive WebGIS application designed for dynamic route finding, traffic congestion prediction, and intelligent travel time estimation across both rural (villages/towns) and urban areas.

---

## 🚀 Key Features & Milestones

### 1. 🤖 Traffic Prediction Engine
* Uses road classification networks and speed limit profiles to forecast real-time traffic flow.
* Analyzes speed variations and bottleneck points along primary, secondary, and rural road infrastructure.

### 2. 📉 Congestion Forecasting Workflows
* Evaluates dynamic delay factors and potential traffic bottlenecks.
* Calculates alternative delay indices across multiple potential corridors simultaneously.

### 3. 📊 Route & Traffic Prediction Reports
* Dynamic left-side analytics panel displaying interactive **Route Cards**.
* Summarizes route options with real-time distance calculations, route segment highlights, and travel time breakdowns.

### 4. 🗺️ Map & Traffic API Integrations
* Integrated with **Leaflet.js** for high-performance interactive map tile rendering.
* Leverages **OSRM (Open Source Routing Machine) API** for routing graph computations and alternative path discovery.
* Uses **OpenStreetMap Nominatim Geocoding API** for place name and village lookups.

### 5. 🔀 Alternate Route Recommendation Workflows
* Computes and visualizes primary and secondary bypass routes using color-coded interactive polylines.
* Features interactive route selection: clicking any alternate polyline or route card instantly highlights the selected path on the map.

### 6. ⏱️ Advanced Travel Time Estimation
* Calculates precise duration estimates automatically formatted into readable **hours and minutes** (e.g., `1 hr 25 mins` or `45 mins`).

---

## 🛠️ Tech Stack

* **Frontend:** HTML5, CSS3, JavaScript (ES6+)
* **Mapping Framework:** [Leaflet.js](https://leafletjs.com/)
* **Routing Engine:** [Leaflet Routing Machine](https://www.mapquest.com/) / [OSRM API](http://project-osrm.org/)
* **Geocoding & Location Search:** [OpenStreetMap Nominatim](https://nominatim.org/)
* **UI Components:** FontAwesome Icons, Custom Responsive Floating Control Panel

---

## 🚀 Getting Started

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/mmadinenikeerthi-code/AI-traffic-management.git](https://github.com/mmadinenikeerthi-code/AI-traffic-management.git)
   cd AI-traffic-management
