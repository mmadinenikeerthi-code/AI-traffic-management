# app/routers/reports.py

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import auth, config, models, utils, schemas
from app.database import get_db

router = APIRouter()

# Use the centralized reports directory from your config
REPORT_FOLDER = config.REPORT_FOLDER
REPORT_FOLDER.mkdir(exist_ok=True, parents=True)

# ==========================================================
# REPORT DASHBOARD
# ==========================================================
@router.get("/")
def report_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    total_reports = db.query(models.TrafficReport).count()
    total_videos = db.query(models.UploadedVideo).count()
    processed = db.query(models.UploadedVideo).filter(
        models.UploadedVideo.processed == True
    ).count()
    total_detection = db.query(models.VehicleCount).count()
    total_congestion = db.query(models.Congestion).count()

    return {
        "reports": total_reports,
        "uploaded_videos": total_videos,
        "processed_videos": processed,
        "vehicle_records": total_detection,
        "congestion_records": total_congestion
    }


# ==========================================================
# GENERATE REPORT
# ==========================================================
@router.post("/generate", response_model=schemas.ReportResponse)
def generate_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    latest = db.query(
        models.VehicleCount
    ).order_by(
        models.VehicleCount.id.desc()
    ).first()

    congestion = db.query(
        models.Congestion
    ).order_by(
        models.Congestion.id.desc()
    ).first()

    if latest is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle data not found."
        )

    # Generate a unique timestamped report name
    report_name = utils.generate_report_name()

    report = models.TrafficReport(
        report_name=report_name,
        generated_at=datetime.utcnow(),
        total_vehicles=latest.total,
        cars=latest.cars,
        bikes=latest.bikes,
        buses=latest.buses,
        trucks=latest.trucks,
        auto_rickshaw=latest.auto_rickshaw,
        ambulance=latest.ambulance,
        congestion_level=congestion.congestion_level if congestion else "LOW",
        recommendation=congestion.recommendation if congestion else "Traffic flow is normal.",
        generated_by=current_user.id,
        remarks="Auto-generated system report."
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return report


# ==========================================================
# GET ALL REPORTS
# ==========================================================
@router.get("/all", response_model=List[schemas.ReportResponse])
def all_reports(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    reports = db.query(
        models.TrafficReport
    ).order_by(
        models.TrafficReport.generated_at.desc()
    ).all()
    return reports


# ==========================================================
# REPORT DETAILS
# ==========================================================
@router.get("/{report_id}", response_model=schemas.ReportResponse)
def report_details(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    report = db.query(
        models.TrafficReport
    ).filter(
        models.TrafficReport.id == report_id
    ).first()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found."
        )
    return report


# ==========================================================
# GENERATE PDF REPORT
# ==========================================================
@router.get("/pdf/{report_id}")
def generate_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    report = db.query(models.TrafficReport).filter(
        models.TrafficReport.id == report_id
    ).first()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found."
        )

    pdf_path = REPORT_FOLDER / f"traffic_report_{report_id}.pdf"
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(pdf_path))
    elements = []

    elements.append(Paragraph("<b>AI Traffic Management Report</b>", styles["Title"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Report ID : {report.id}", styles["Normal"]))
    elements.append(Paragraph(f"Report Name : {report.report_name}", styles["Normal"]))
    elements.append(Paragraph(f"Generated : {report.generated_at}", styles["Normal"]))
    elements.append(Paragraph(f"Total Vehicles : {report.total_vehicles}", styles["Normal"]))
    elements.append(Paragraph(f"Cars : {report.cars}", styles["Normal"]))
    elements.append(Paragraph(f"Bikes : {report.bikes}", styles["Normal"]))
    elements.append(Paragraph(f"Buses : {report.buses}", styles["Normal"]))
    elements.append(Paragraph(f"Trucks : {report.trucks}", styles["Normal"]))
    elements.append(Paragraph(f"Auto Rickshaw : {report.auto_rickshaw}", styles["Normal"]))
    elements.append(Paragraph(f"Ambulance : {report.ambulance}", styles["Normal"]))
    elements.append(Paragraph(f"Congestion : {report.congestion_level}", styles["Normal"]))
    elements.append(Paragraph(f"Recommendation : {report.recommendation}", styles["Normal"]))

    doc.build(elements)

    return FileResponse(
        str(pdf_path),
        filename=pdf_path.name,
        media_type="application/pdf"
    )


# ==========================================================
# EXPORT CSV
# ==========================================================
@router.get("/csv/all")
def export_csv(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    reports = db.query(models.TrafficReport).all()
    if not reports:
        raise HTTPException(
            status_code=404,
            detail="No reports found to export."
        )

    csv_path = REPORT_FOLDER / "all_traffic_reports.csv"
    
    with open(csv_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        # Write Headers
        writer.writerow([
            "ID", "Report Name", "Total Vehicles", "Cars", "Bikes", 
            "Buses", "Trucks", "Auto Rickshaws", "Ambulances", 
            "Congestion Level", "Recommendation", "Generated At"
        ])
        # Write Data rows
        for r in reports:
            writer.writerow([
                r.id, r.report_name, r.total_vehicles, r.cars, r.bikes,
                r.buses, r.trucks, r.auto_rickshaw, r.ambulance,
                r.congestion_level, r.recommendation, r.generated_at
            ])

    return FileResponse(
        str(csv_path),
        filename="all_traffic_reports.csv",
        media_type="text/csv"
    )