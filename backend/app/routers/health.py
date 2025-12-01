"""API routes for health scores and predictions."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import HealthScore, Prediction, SensorReading
from app.schemas import HealthScoreResponse, PredictionResponse
from app.services.ml.forecasting import forecasting_service

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/scores", response_model=List[HealthScoreResponse])
def get_health_scores(
    asset_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get health scores."""
    query = db.query(HealthScore)
    
    if asset_id:
        query = query.filter(HealthScore.asset_id == asset_id)
    
    scores = query.order_by(HealthScore.timestamp.desc()).limit(limit).all()
    return scores


@router.get("/scores/{asset_id}/latest", response_model=HealthScoreResponse)
def get_latest_health_score(asset_id: int, db: Session = Depends(get_db)):
    """Get latest health score for an asset."""
    score = db.query(HealthScore).filter(
        HealthScore.asset_id == asset_id
    ).order_by(HealthScore.timestamp.desc()).first()
    
    if not score:
        raise HTTPException(status_code=404, detail="Health score not found")
    
    return score


@router.get("/predictions", response_model=List[PredictionResponse])
def get_predictions(
    asset_id: Optional[int] = None,
    prediction_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get predictions."""
    query = db.query(Prediction)
    
    if asset_id:
        query = query.filter(Prediction.asset_id == asset_id)
    
    if prediction_type:
        query = query.filter(Prediction.prediction_type == prediction_type)
    
    predictions = query.order_by(Prediction.timestamp.desc()).limit(limit).all()
    return predictions


@router.get("/forecast/{asset_id}")
def get_forecast(
    asset_id: int,
    param: str = "temperature",
    horizon_hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get forecast for an asset parameter."""
    # Get historical readings
    readings = db.query(SensorReading).filter(
        SensorReading.asset_id == asset_id
    ).order_by(SensorReading.timestamp.asc()).limit(200).all()
    
    if not readings:
        raise HTTPException(status_code=404, detail="No readings found for asset")
    
    # Extract parameter values
    timestamps = [r.timestamp for r in readings]
    values = []
    
    for reading in readings:
        if param == "temperature":
            values.append(reading.temperature)
        elif param == "pressure":
            values.append(reading.pressure)
        elif param == "vibration":
            values.append(reading.vibration)
        elif param == "flow":
            values.append(reading.flow)
        elif param == "rpm":
            values.append(reading.rpm)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid parameter: {param}")
    
    # Filter out None values
    valid_data = [(ts, val) for ts, val in zip(timestamps, values) if val is not None]
    if not valid_data:
        raise HTTPException(status_code=400, detail=f"No valid {param} data found")
    
    timestamps, values = zip(*valid_data)
    
    # Generate forecast
    forecast = forecasting_service.forecast(
        list(timestamps),
        list(values),
        param,
        horizon_hours
    )
    
    return forecast

