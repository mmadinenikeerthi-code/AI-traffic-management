# 🚦 AI Traffic Prediction & Congestion Management System

## Overview

This project is an AI-based Traffic Prediction and Congestion Management System developed to monitor traffic, detect congestion, analyze vehicle movement, and provide real-time traffic insights. The main objective of this project is to help traffic authorities monitor roads efficiently and reduce congestion using Artificial Intelligence.

The system allows users to upload traffic videos, performs vehicle detection using YOLO, generates traffic statistics, displays analytics on a dashboard, and visualizes congestion using GIS heatmaps.

---

## Features

* User Authentication (JWT)
* Role Based Access Control (Admin, Supervisor, Traffic Officer)
* Traffic Video Upload
* AI Vehicle Detection using YOLO
* Vehicle Counting
* Congestion Detection
* Live Dashboard
* Traffic Analytics
* GIS Heatmap using OpenStreetMap
* Traffic Trend Analysis
* Emergency Vehicle Detection
* Alert & Notification System
* Incident Management (Admin)
* AI Traffic Recommendation

---

## Tech Stack

### Frontend

* HTML5
* CSS3
* Bootstrap 5
* JavaScript
* Chart.js
* Leaflet.js

### Backend

* FastAPI
* Python

### Database

* SQLite
* SQLAlchemy ORM

### AI Model

* YOLOv8

### GIS

* OpenStreetMap
* Leaflet Heatmap

### Tools Used

* Visual Studio Code
* Git & GitHub
* Postman
* Uvicorn

---

## Project Structure

```
AI-Traffic-Management-System
│
├── app
│   ├── routers
│   ├── models
│   ├── schemas
│   ├── services
│   ├── static
│   ├── templates
│   ├── uploads
│   └── outputs
│
├── database.py
├── main.py
├── requirements.txt
└── README.md
```

---

## Modules

### Authentication Module

* User Registration
* Login
* JWT Authentication
* Role Based Access

### Traffic Detection Module

* Upload Traffic Video
* Vehicle Detection
* Vehicle Counting
* Congestion Detection

### Dashboard Module

* Total Vehicles
* Cars
* Bikes
* Trucks
* Buses
* Auto Rickshaws
* Ambulance Detection
* Congestion Level
* Traffic Density
* Speed Analysis

### GIS Module

* OpenStreetMap Integration
* Traffic Heatmap
* Congestion Visualization

### Analytics Module

* Traffic Trends
* Vehicle Distribution
* KPI Dashboard
* Historical Statistics

### Alert Module

* Congestion Alerts
* Emergency Vehicle Alerts
* Incident Monitoring

---

## Workflow

1. User Login
2. Upload Traffic Video
3. YOLO Detects Vehicles
4. Vehicle Counts are Generated
5. Traffic Statistics are Calculated
6. Dashboard Updates Automatically
7. Heatmap is Generated
8. Alerts are Generated if Congestion is High

---

## Installation

Clone the repository

```bash
git clone https://github.com/your-username/AI-Traffic-Management-System.git
```

Move into the project

```bash
cd AI-Traffic-Management-System
```

Create Virtual Environment

```bash
python -m venv venv
```

Activate Environment

Windows

```bash
venv\Scripts\activate
```

Install Dependencies

```bash
pip install -r requirements.txt
```

Run Backend

```bash
uvicorn main:app --reload
```

Open Browser

```
http://127.0.0.1:8000
```

---

## Screenshots

* Login Page
* Dashboard
* Video Upload
* Analytics Dashboard
* Heatmap
* Admin Panel

(Add screenshots after completing the project.)

---

## Future Improvements

* Live CCTV Camera Support
* Multi-Camera Monitoring
* Better Traffic Prediction Models
* Mobile Application
* Cloud Deployment
* SMS & Email Notifications
* Real-Time GPS Vehicle Tracking

---

## Learning Outcomes

During this project, I learned:

* FastAPI Backend Development
* REST API Development
* JWT Authentication
* Role Based Access Control
* YOLO Object Detection
* Database Management using SQLAlchemy
* JavaScript Dashboard Development
* GIS Visualization with Leaflet
* API Testing using Postman
* Git & GitHub Version Control

---

## Author

**Madineni Keerthi**

B.Tech Data Science Student

---

## License

This project is developed for academic and learning purposes.
