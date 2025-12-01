"""API routes for assets."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Asset, SensorReading, HealthScore, DigitalTwinState, Alert
from app.schemas import (
    AssetCreate, AssetResponse, AssetMetricsResponse,
    SensorReadingResponse, HealthScoreResponse, DigitalTwinStateResponse, AlertResponse
)

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.post("/", response_model=AssetResponse)
def create_asset(asset: AssetCreate, db: Session = Depends(get_db)):
    """Create a new asset."""
    db_asset = Asset(**asset.dict())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset


@router.get("/", response_model=List[AssetResponse])
def get_assets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all assets."""
    assets = db.query(Asset).offset(skip).limit(limit).all()
    return assets


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    """Get a specific asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.get("/{asset_id}/metrics", response_model=AssetMetricsResponse)
def get_asset_metrics(asset_id: int, db: Session = Depends(get_db)):
    """Get comprehensive metrics for an asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Latest reading
    latest_reading = db.query(SensorReading).filter(
        SensorReading.asset_id == asset_id
    ).order_by(SensorReading.timestamp.desc()).first()
    
    # Latest health score
    latest_health = db.query(HealthScore).filter(
        HealthScore.asset_id == asset_id
    ).order_by(HealthScore.timestamp.desc()).first()
    
    # Latest twin state
    latest_twin = db.query(DigitalTwinState).filter(
        DigitalTwinState.asset_id == asset_id
    ).order_by(DigitalTwinState.timestamp.desc()).first()
    
    # Active alerts
    active_alerts = db.query(Alert).filter(
        Alert.asset_id == asset_id,
        Alert.resolved == False
    ).order_by(Alert.timestamp.desc()).all()
    
    return AssetMetricsResponse(
        asset=asset,
        latest_reading=latest_reading,
        latest_health=latest_health,
        latest_twin_state=latest_twin,
        active_alerts=active_alerts,
    )

