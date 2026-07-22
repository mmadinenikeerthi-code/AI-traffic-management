# ==========================================================
# app/routers/detect.py
# AI Traffic Management & Congestion Detection System
# ==========================================================

import os
from pathlib import Path
from datetime import datetime

import cv2
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException,
    status
)
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
import supervision as sv
from ultralytics import YOLO

from app import models
from app import auth
from app import utils
from app import config
from app.database import get_db
from app.utils import (
    congestion_level,
    density_percentage,
    recommendation,
    signal_time
)

router = APIRouter()

# ==========================================================
# LOAD AI MODEL & TRACKER
# ==========================================================

model = YOLO(str(config.MODEL_PATH))
tracker = sv.ByteTrack()
box_annotator = sv.BoxAnnotator()
label_annotator = sv.LabelAnnotator()

# Vehicle IDs already counted
counted_ids = set()
# ==========================================================
# LIVE CAMERA VARIABLES
# ==========================================================

live_camera = None
live_running = False

latest_vehicle_data = {
    "cars": 0,
    "bikes": 0,
    "buses": 0,
    "trucks": 0,
    "auto_rickshaw": 0,
    "ambulance": 0,
    "persons": 0,
    "total": 0
}
def connect_rtsp():

    global live_camera

    live_camera = cv2.VideoCapture(config.RTSP_URL)

    if not live_camera.isOpened():
        raise Exception("Unable to connect to RTSP Camera")

    return live_camera

# ==========================================================
# PART 1: Video Upload & Validation
# ==========================================================

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    if file.filename is None or file.filename.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )

    if not utils.allowed_video(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Only MP4, AVI, MOV and MKV videos are allowed."
        )

    filename, filepath = utils.save_uploaded_video(file)

    video = models.UploadedVideo(
        filename=filename,
        filepath=filepath,
        processed=False,
        uploaded_by=current_user.id,
        upload_time=datetime.utcnow()
    )

    db.add(video)
    db.commit()
    db.refresh(video)

    return {
        "message": "Video uploaded successfully.",
        "video_id": video.id,
        "filename": filename,
        "uploaded_by": current_user.username,
        "processed": False
    }


@router.get("/videos")
def uploaded_videos(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    videos = db.query(
        models.UploadedVideo
    ).order_by(
        models.UploadedVideo.upload_time.desc()
    ).all()
    return videos


@router.get("/video/{video_id}")
def video_details(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    video = db.query(
        models.UploadedVideo
    ).filter(
        models.UploadedVideo.id == video_id
    ).first()

    if video is None:
        raise HTTPException(
            status_code=404,
            detail="Video not found."
        )
    return video


@router.delete("/video/{video_id}")
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.admin_required)
):
    video = db.query(
        models.UploadedVideo
    ).filter(
        models.UploadedVideo.id == video_id
    ).first()

    if video is None:
        raise HTTPException(
            status_code=404,
            detail="Video not found."
        )

    path = Path(video.filepath)
    if path.exists():
        path.unlink()

    db.delete(video)
    db.commit()
    return {
        "message": "Video deleted successfully."
    }


# ==========================================================
# PART 2: YOLOv8 + ByteTrack Vehicle Tracking
# ==========================================================

@router.post("/process/{video_id}")
def process_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    video = db.query(models.UploadedVideo).filter(
        models.UploadedVideo.id == video_id
    ).first()

    if video is None:
        raise HTTPException(
            status_code=404,
            detail="Video not found."
        )

    capture = cv2.VideoCapture(video.filepath)
    if not capture.isOpened():
        raise HTTPException(
            status_code=500,
            detail="Cannot open video."
        )

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS)

    output_video = config.OUTPUT_FOLDER / f"processed_{video.filename}"
    writer = cv2.VideoWriter(
        str(output_video),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height)
    )

    cars = 0
    bikes = 0
    buses = 0
    trucks = 0
    auto = 0
    ambulance = 0
    persons = 0
    frame_count = 0
    counted_ids.clear()

    while True:
        success, frame = capture.read()
        if not success:
            break

        frame_count += 1
        results = model(frame, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(results)
        detections = tracker.update_with_detections(detections)

        labels = []
        for i in range(len(detections)):
            tracker_id = detections.tracker_id[i]
            class_id = detections.class_id[i]
            confidence = detections.confidence[i]
            class_name = model.names[class_id]

            labels.append(f"{tracker_id} {class_name} {confidence:.2f}")

            if tracker_id not in counted_ids:
                counted_ids.add(tracker_id)
                if class_name == "car":
                    cars += 1
                elif class_name == "motorcycle":
                    bikes += 1
                elif class_name == "bus":
                    buses += 1
                elif class_name == "truck":
                    trucks += 1
                elif class_name == "person":
                    persons += 1
                elif class_name == "ambulance":
                    ambulance += 1
                elif class_name == "auto":
                    auto += 1

        annotated = frame.copy()
        annotated = box_annotator.annotate(scene=annotated, detections=detections)
        annotated = label_annotator.annotate(scene=annotated, detections=detections, labels=labels)
        writer.write(annotated)

    capture.release()
    writer.release()

    total = cars + bikes + buses + trucks + auto + ambulance

    vehicle = models.VehicleCount(
        cars=cars,
        bikes=bikes,
        buses=buses,
        trucks=trucks,
        auto_rickshaw=auto,
        ambulance=ambulance,
        total=total,
        frame_number=frame_count
    )

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    video.processed = True
    db.commit()

    return {
        "status": "Success",
        "video": video.filename,
        "processed_video": str(output_video),
        "frames": frame_count,
        "cars": cars,
        "bikes": bikes,
        "buses": buses,
        "trucks": trucks,
        "auto_rickshaw": auto,
        "ambulance": ambulance,
        "persons": persons,
        "total_vehicles": total
    }


# ==========================================================
# PART 3: Congestion Analysis & AI Recommendation
# ==========================================================

@router.post("/analyse/{vehicle_id}")
def analyse_congestion(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    vehicle = db.query(models.VehicleCount).filter(
        models.VehicleCount.id == vehicle_id
    ).first()

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle record not found."
        )

    total = vehicle.total
    level, green_time, message = congestion_level(total)
    density = density_percentage(total)
    avg_speed = utils.average_speed(level)
    advice = recommendation(level)

    congestion = models.Congestion(
    vehicle_count=total,
    density=density,
    congestion_level=level,
    signal_time=green_time,
    recommendation=advice,
    average_speed=avg_speed
)


    db.add(congestion)
    db.commit()
    db.refresh(congestion)

    return {
        "status": "Success",
        "vehicle_count": total,
        "density": density,
        "congestion_level": level,
        "average_speed": avg_speed,
        "green_signal_time": green_time,
        "recommendation": advice,
        "message": message
    }


@router.get("/congestion/latest")
def latest_congestion(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    congestion = db.query(
        models.Congestion
    ).order_by(
        models.Congestion.created_at.desc()
    ).first()

    if congestion is None:
        return {
            "message": "No congestion record found."
        }
    return congestion


@router.get("/congestion/history")
def congestion_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    history = db.query(
        models.Congestion
    ).order_by(
        models.Congestion.created_at.desc()
    ).all()
    return history


@router.get("/live-dashboard")
def live_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    vehicle = db.query(
        models.VehicleCount
    ).order_by(
        models.VehicleCount.id.desc()
    ).first()

    congestion = db.query(
        models.Congestion
    ).order_by(
        models.Congestion.id.desc()
    ).first()

    if vehicle is None:
        return {
            "status": "No Data"
        }

    return {
        "cars": vehicle.cars,
        "bikes": vehicle.bikes,
        "buses": vehicle.buses,
        "trucks": vehicle.trucks,
        "auto_rickshaw": vehicle.auto_rickshaw,
        "ambulance": vehicle.ambulance,
        "total_vehicles": vehicle.total,
        "congestion_level": congestion.congestion_level if congestion else "LOW",
        "signal_time": congestion.signal_time if congestion else 30,
        "density": congestion.density if congestion else 0,
        "average_speed": congestion.average_speed if congestion else 60,
        "recommendation": congestion.recommendation if congestion else "Traffic Normal"
    }


@router.get("/statistics")
def statistics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    total_videos = db.query(models.UploadedVideo).count()
    processed = db.query(models.UploadedVideo).filter(models.UploadedVideo.processed == True).count()
    total_records = db.query(models.VehicleCount).count()
    total_congestion = db.query(models.Congestion).count()

    return {
        "uploaded_videos": total_videos,
        "processed_videos": processed,
        "vehicle_records": total_records,
        "congestion_records": total_congestion
    }


# ==========================================================
# PART 4: Reports, Analytics & Download
# ==========================================================

@router.get("/download/video/{video_id}")
def download_processed_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    video = db.query(models.UploadedVideo).filter(
        models.UploadedVideo.id == video_id
    ).first()

    if video is None:
        raise HTTPException(
            status_code=404,
            detail="Video not found."
        )

    output_path = config.OUTPUT_FOLDER / f"processed_{video.filename}"
    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Processed video not found."
        )

    return FileResponse(
        path=str(output_path),
        filename=output_path.name,
        media_type="video/mp4"
    )


@router.get("/history")
def detection_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    history = db.query(
        models.VehicleCount
    ).order_by(
        models.VehicleCount.id.desc()
    ).all()
    return history


@router.get("/analytics/daily")
def daily_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    total = db.query(func.sum(models.VehicleCount.total)).scalar() or 0
    records = db.query(models.VehicleCount).count()
    average = round(total / records, 2) if records else 0

    return {
        "date": datetime.now().strftime("%d-%m-%Y"),
        "total_vehicles": total,
        "records": records,
        "average_per_record": average
    }


@router.get("/analytics/classes")
def class_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    records = db.query(models.VehicleCount).all()
    return {
        "cars": sum(r.cars for r in records),
        "bikes": sum(r.bikes for r in records),
        "buses": sum(r.buses for r in records),
        "trucks": sum(r.trucks for r in records),
        "auto_rickshaw": sum(r.auto_rickshaw for r in records),
        "ambulance": sum(r.ambulance for r in records)
    }


@router.delete("/record/{record_id}")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.admin_required)
):
    record = db.query(
        models.VehicleCount
    ).filter(
        models.VehicleCount.id == record_id
    ).first()

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Record not found."
        )

    db.delete(record)
    db.commit()
    return {
        "message": "Detection record deleted successfully."
    }


@router.get("/performance")
def system_performance(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.officer_required)
):
    processed = db.query(models.UploadedVideo).filter(models.UploadedVideo.processed == True).count()
    pending = db.query(models.UploadedVideo).filter(models.UploadedVideo.processed == False).count()

    return {
        "processed_videos": processed,
        "pending_videos": pending,
        "ai_model": "YOLOv8 + ByteTrack",
        "tracking": "Enabled",
        "status": "Running"
    }


@router.get("/health")
def health():
    return {
        "status": "Healthy",
        "module": "Vehicle Detection",
        "ai_engine": "YOLOv8",
        "tracker": "ByteTrack"
    }
@router.get("/live/test")
def live_test(
    current_user: models.User = Depends(auth.officer_required)
):

    cap = connect_rtsp()

    success, frame = cap.read()

    cap.release()

    if not success:
        return {
            "status": "Failed"
        }

    return {
        "status": "Camera Connected",
        "width": frame.shape[1],
        "height": frame.shape[0]
    }