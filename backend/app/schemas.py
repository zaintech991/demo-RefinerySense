"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SensorReadingCreate(BaseModel):
    """Schema for creating sensor readings."""
    asset_id: int
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    vibration: Optional[float] = None
    flow: Optional[float] = None
    rpm: Optional[float] = None


class SensorReadingResponse(BaseModel):
    """Schema for sensor reading responses."""
    id: int
    asset_id: int
    timestamp: datetime
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    vibration: Optional[float] = None
    flow: Optional[float] = None
    rpm: Optional[float] = None
    
    class Config:
        from_attributes = True


class AssetCreate(BaseModel):
    """Schema for creating assets."""
    name: str
    asset_type: str
    location: Optional[str] = None


class AssetResponse(BaseModel):
    """Schema for asset responses."""
    id: int
    name: str
    asset_type: str
    location: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DigitalTwinStateResponse(BaseModel):
    """Schema for digital twin state responses."""
    id: int
    asset_id: int
    timestamp: datetime
    expected_temperature: Optional[float] = None
    expected_pressure: Optional[float] = None
    expected_vibration: Optional[float] = None
    expected_flow: Optional[float] = None
    expected_rpm: Optional[float] = None
    deviation_score: Optional[float] = None
    
    class Config:
        from_attributes = True


class HealthScoreResponse(BaseModel):
    """Schema for health score responses."""
    id: int
    asset_id: int
    timestamp: datetime
    health_index: float
    twin_deviation_score: Optional[float] = None
    anomaly_score: Optional[float] = None
    rul_days: Optional[float] = None
    failure_risk_score: Optional[float] = None
    
    class Config:
        from_attributes = True


class PredictionResponse(BaseModel):
    """Schema for prediction responses."""
    id: int
    asset_id: int
    timestamp: datetime
    prediction_type: str
    predicted_value: Optional[float] = None
    confidence: Optional[float] = None
    forecast_horizon_hours: Optional[int] = None
    metadata_json: Optional[str] = None
    
    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    """Schema for alert responses."""
    id: int
    asset_id: int
    timestamp: datetime
    alert_type: str
    severity: str
    message: str
    resolved: bool
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AssetMetricsResponse(BaseModel):
    """Schema for combined asset metrics."""
    asset: AssetResponse
    latest_reading: Optional[SensorReadingResponse] = None
    latest_health: Optional[HealthScoreResponse] = None
    latest_twin_state: Optional[DigitalTwinStateResponse] = None
    active_alerts: List[AlertResponse] = []


class ChatMessage(BaseModel):
    """Schema for chat messages."""
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Schema for chat responses."""
    response: str
    conversation_id: str

