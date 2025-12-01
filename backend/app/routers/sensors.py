"""API routes for sensor readings."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import SensorReading, Asset
from app.schemas import SensorReadingCreate, SensorReadingResponse
from app.services.data_pipeline import DataPipeline
from app.services.digital_twin import digital_twin
from app.services.ml.anomaly_detection import anomaly_detection_service
from app.services.ml.rul_estimation import rul_estimation_service
from app.services.health_score import health_score_engine
from app.services.alerts import alerts_service

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


@router.post("/readings", response_model=SensorReadingResponse)
def create_reading(reading: SensorReadingCreate, db: Session = Depends(get_db)):
    """Create a new sensor reading."""
    # Process through pipeline
    stored, error = DataPipeline.process_reading(db, reading.dict())
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    # Get asset for type
    asset = db.query(Asset).filter(Asset.id == reading.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Create digital twin state
    actual_reading = {
        "temperature": reading.temperature,
        "pressure": reading.pressure,
        "vibration": reading.vibration,
        "flow": reading.flow,
        "rpm": reading.rpm,
    }
    twin_state = digital_twin.create_twin_state(db, reading.asset_id, actual_reading)
    
    # Anomaly detection
    # Get recent readings for context
    recent_readings = db.query(SensorReading).filter(
        SensorReading.asset_id == reading.asset_id
    ).order_by(SensorReading.timestamp.desc()).limit(50).all()
    
    recent_dicts = [
        {
            "temperature": r.temperature,
            "pressure": r.pressure,
            "vibration": r.vibration,
            "flow": r.flow,
            "rpm": r.rpm,
        }
        for r in recent_readings
    ]
    
    anomaly_result = anomaly_detection_service.detect_anomaly_multi_param(
        recent_dicts, actual_reading
    )
    
    # RUL estimation
    from app.models import HealthScore
    health_scores = db.query(HealthScore).filter(
        HealthScore.asset_id == reading.asset_id
    ).order_by(HealthScore.timestamp.asc()).all()
    
    health_scores_list = [h.health_index for h in health_scores]
    health_timestamps = [h.timestamp for h in health_scores]
    sensor_readings_list = recent_dicts
    reading_timestamps = [r.timestamp for r in recent_readings]
    
    rul_result = rul_estimation_service.estimate_rul(
        asset.asset_type,
        health_scores_list,
        health_timestamps,
        sensor_readings_list,
        reading_timestamps
    )
    
    # Health score
    health_score = health_score_engine.create_health_score(
        db,
        reading.asset_id,
        twin_state.deviation_score or 0.0,
        anomaly_result["anomaly_score"],
        rul_result["rul_days"],
        rul_result["risk_score"]
    )
    
    # Check alerts
    alerts_service.check_threshold_alerts(db, reading.asset_id, actual_reading)
    alerts_service.check_health_alerts(db, reading.asset_id, health_score.health_index)
    alerts_service.check_anomaly_alerts(db, reading.asset_id, anomaly_result["anomaly_score"])
    alerts_service.check_rul_alerts(db, reading.asset_id, rul_result["rul_days"])
    
    return stored


@router.get("/readings", response_model=List[SensorReadingResponse])
def get_readings(
    asset_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get sensor readings."""
    query = db.query(SensorReading)
    
    if asset_id:
        query = query.filter(SensorReading.asset_id == asset_id)
    
    readings = query.order_by(SensorReading.timestamp.desc()).limit(limit).all()
    return readings


@router.get("/readings/{reading_id}", response_model=SensorReadingResponse)
def get_reading(reading_id: int, db: Session = Depends(get_db)):
    """Get a specific sensor reading."""
    reading = db.query(SensorReading).filter(SensorReading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    return reading

