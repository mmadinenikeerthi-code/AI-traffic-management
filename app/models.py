# ==========================================================
# app/models.py
# AI Traffic Management & Congestion Detection System
# ==========================================================

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)

from sqlalchemy.orm import relationship

from app.database import Base


# ==========================================================
# USER
# ==========================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    fullname = Column(
        String(100),
        nullable=False
    )

    username = Column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    email = Column(
        String(100),
        unique=True,
        index=True,
        nullable=False
    )

    password = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(30),
        default="Traffic Officer"
    )

    phone = Column(
        String(20),
        nullable=True
    )

    status = Column(
        String(20),
        default="Active"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationships
    reports = relationship(
        "TrafficReport",
        back_populates="user"
    )

    videos = relationship(
        "UploadedVideo",
        back_populates="user"
    )


# ==========================================================
# UPLOADED VIDEO
# ==========================================================

class UploadedVideo(Base):
    __tablename__ = "uploaded_videos"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    filename = Column(
        String(255),
        nullable=False
    )

    filepath = Column(
        String(500),
        nullable=False
    )

    upload_time = Column(
        DateTime,
        default=datetime.utcnow
    )

    processed = Column(
        Boolean,
        default=False
    )

    uploaded_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    user = relationship(
        "User",
        back_populates="videos"
    )


# ==========================================================
# VEHICLE COUNT
# ==========================================================

class VehicleCount(Base):
    __tablename__ = "vehicle_counts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    cars = Column(
        Integer,
        default=0
    )

    bikes = Column(
        Integer,
        default=0
    )

    buses = Column(
        Integer,
        default=0
    )

    trucks = Column(
        Integer,
        default=0
    )

    auto_rickshaw = Column(
        Integer,
        default=0
    )

    ambulance = Column(
        Integer,
        default=0
    )

    total = Column(
        Integer,
        default=0
    )

    frame_number = Column(
        Integer,
        default=0
    )

    detected_time = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )


# ==========================================================
# CONGESTION
# ==========================================================

class Congestion(Base):
    __tablename__ = "congestion"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    vehicle_count = Column(
        Integer,
        default=0
    )

    density = Column(
        Float,
        default=0.0
    )

    congestion_level = Column(
        String(50),
        nullable=False
    )

    average_speed = Column(
        Float,
        default=0.0
    )

    signal_time = Column(
        Integer,
        default=30
    )

    recommendation = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )


# ==========================================================
# TRAFFIC HISTORY
# ==========================================================

class TrafficHistory(Base):
    __tablename__ = "traffic_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    location = Column(
        String,
        nullable=False,
        default="Junction A"
    )

    vehicle_count = Column(
        Integer,
        default=0
    )

    density = Column(
        String,
        default="Low"
    )

    signal_time = Column(
        Integer,
        default=30
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ==========================================================
# TRAFFIC LOG
# ==========================================================

class TrafficLog(Base):
    __tablename__ = "traffic_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    location = Column(
        String(255),
        nullable=False
    )

    lat = Column(
        Float,
        nullable=False
    )

    lng = Column(
        Float,
        nullable=False
    )

    vehicle_count = Column(
        Integer,
        nullable=False
    )

    density_status = Column(
        String(50),
        nullable=False
    )

    avg_speed_kmh = Column(
        Float,
        default=40.0
    )

    has_accident = Column(
        Boolean,
        default=False
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )


# ==========================================================
# TRAFFIC REPORT
# ==========================================================

class TrafficReport(Base):
    __tablename__ = "traffic_reports"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    report_name = Column(
        String(200)
    )

    total_vehicles = Column(
        Integer,
        default=0
    )

    cars = Column(
        Integer,
        default=0
    )

    bikes = Column(
        Integer,
        default=0
    )

    buses = Column(
        Integer,
        default=0
    )

    trucks = Column(
        Integer,
        default=0
    )

    auto_rickshaw = Column(
        Integer,
        default=0
    )

    ambulance = Column(
        Integer,
        default=0
    )

    congestion_level = Column(
        String(100)
    )

    recommendation = Column(
        Text
    )

    remarks = Column(
        Text,
        nullable=True
    )

    generated_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    generated_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    user = relationship(
        "User",
        back_populates="reports"
    )


# ==========================================================
# ALERT
# ==========================================================

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(200),
        nullable=True
    )

    description = Column(
        Text,
        nullable=True
    )

    location = Column(
        String(255),
        nullable=True,
        default="Junction A"
    )

    alert_type = Column(
        String(100),
        nullable=True
    )

    severity = Column(
        String(30),
        default="High"
    )

    message = Column(
        Text,
        nullable=True
    )

    status = Column(
        String(20),
        default="Active"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ==========================================================
# SYSTEM LOG
# ==========================================================

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String(100)
    )

    action = Column(
        String(255)
    )

    ip_address = Column(
        String(100)
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ==========================================================
# TRAFFIC ZONE
# ==========================================================
# Added because your recommendation endpoint was querying
# the "traffic_zones" table, which was missing from the model
# definitions you previously provided.

class TrafficZone(Base):
    __tablename__ = "traffic_zones"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    road_name = Column(
        String(255),
        nullable=False
    )

    density = Column(
        Float,
        default=0.0
    )

    avg_speed = Column(
        Float,
        default=0.0
    )

    vehicle_count = Column(
        Integer,
        default=0
    )

    has_accident = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )