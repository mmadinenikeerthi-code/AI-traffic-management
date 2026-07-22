# app/models.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(30), default="Traffic Officer")
    phone = Column(String(20), nullable=True)
    status = Column(String(20), default="Active")
    created_at = Column(DateTime, default=datetime.utcnow)

    reports = relationship("TrafficReport", back_populates="user")
    videos = relationship("UploadedVideo", back_populates="user")


class UploadedVideo(Base):
    __tablename__ = "uploaded_videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="videos")


class VehicleCount(Base):
    __tablename__ = "vehicle_counts"

    id = Column(Integer, primary_key=True, index=True)
    cars = Column(Integer, default=0)
    bikes = Column(Integer, default=0)
    buses = Column(Integer, default=0)
    trucks = Column(Integer, default=0)
    auto_rickshaw = Column(Integer, default=0)
    ambulance = Column(Integer, default=0)
    total = Column(Integer, default=0)
    frame_number = Column(Integer, default=0)
    detected_time = Column(DateTime, default=datetime.utcnow)


class Congestion(Base):
    __tablename__ = "congestion"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_count = Column(Integer, default=0)
    density = Column(Float, default=0.0)
    congestion_level = Column(String(50), nullable=False)
    average_speed = Column(Float, default=0.0)
    signal_time = Column(Integer, default=30)
    recommendation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrafficReport(Base):
    __tablename__ = "traffic_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_name = Column(String(200))
    total_vehicles = Column(Integer, default=0)
    cars = Column(Integer, default=0)
    bikes = Column(Integer, default=0)
    buses = Column(Integer, default=0)
    trucks = Column(Integer, default=0)
    auto_rickshaw = Column(Integer, default=0)
    ambulance = Column(Integer, default=0)
    congestion_level = Column(String(100))
    recommendation = Column(Text)
    remarks = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", back_populates="reports")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    description = Column(Text)
    severity = Column(String(30))
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100))
    action = Column(String(255))
    ip_address = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
