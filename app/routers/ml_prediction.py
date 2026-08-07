# ==========================================================
# app/routers/ml_prediction.py
# Module 2: Advanced ML Traffic Prediction Engine (XGBoost / Random Forest)
# ==========================================================

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sklearn.ensemble import RandomForestRegressor

from app import models, auth
from app.database import get_db

router = APIRouter(prefix="/ml", tags=["ML Traffic Prediction"])

class PredictionInput(BaseModel):
    road_name: str = Field(..., description="Name of the road or junction")
    current_vehicle_count: int = Field(..., description="Current detected vehicle count")
    current_density: float = Field(..., description="Current traffic density percentage (0-100)")
    hour_of_day: int = Field(..., ge=0, le=23, description="Current hour (0-23)")

# Simple in-memory or dynamically trained lightweight model simulator for demonstration
# In production, this loads a serialized joblib/pickle model file (.pkl)
class TrafficMLPredictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=50, random_state=42)
        self._is_trained = False
        self._train_dummy_model()

    def _train_dummy_model(self):
        """Trains a baseline model on synthetic spatiotemporal traffic features."""
        np.random.seed(42)
        X_train = np.random.rand(200, 3) # [vehicle_count, density, hour_of_day]
        X_train[:, 0] *= 100  # Vehicles 0-100
        X_train[:, 1] *= 100  # Density 0-100%
        X_train[:, 2] *= 24   # Hour 0-24
        
        # Target: future density shift
        y_train = np.clip(X_train[:, 1] + (X_train[:, 2] % 6 - 3) * 2 + np.random.normal(0, 5, 200), 0, 100)
        self.model.fit(X_train, y_train)
        self._is_trained = True

    def predict_future(self, vehicle_count: int, density: float, hour: int):
        """Predicts density horizons for +15m, +30m, and +60m."""
        features_15 = np.array([[vehicle_count, density, hour]])
        features_30 = np.array([[int(vehicle_count * 1.05), min(100.0, density * 1.08), (hour) % 24]])
        features_60 = np.array([[int(vehicle_count * 1.12), min(100.0, density * 1.15), (hour + 1) % 24]])

        pred_15 = float(self.model.predict(features_15)[0])
        pred_30 = float(self.model.predict(features_30)[0])
        pred_60 = float(self.model.predict(features_60)[0])

        return {
            "horizon_15min": {"predicted_density": round(pred_15, 2), "level": self._get_level(pred_15)},
            "horizon_30min": {"predicted_density": round(pred_30, 2), "level": self._get_level(pred_30)},
            "horizon_60min": {"predicted_density": round(pred_60, 2), "level": self._get_level(pred_60)},
        }

    def _get_level(self, density: float) -> str:
        if density >= 75:
            return "HEAVY"
        elif density >= 45:
            return "MEDIUM"
        return "LOW"

predictor = TrafficMLPredictor()

@router.post("/predict-traffic")
def get_ml_traffic_forecast(
    payload: PredictionInput,
    db: Session = Depends(get_db)
):
    """
    Executes machine learning regression forecasting using Random Forest / XGBoost logic
    to predict congestion changes over 15 min, 30 min, and 1 hour intervals.
    """
    forecast = predictor.predict_future(
        vehicle_count=payload.current_vehicle_count,
        density=payload.current_density,
        hour=payload.hour_of_day
    )

    return {
        "status": "success",
        "road_name": payload.road_name,
        "algorithm_used": "RandomForestRegressor (ML Ensemble)",
        "current_metrics": {
            "vehicle_count": payload.current_vehicle_count,
            "density": payload.current_density
        },
        "forecast": forecast
    }