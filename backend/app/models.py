"""Database models for the application."""
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime
from typing import Optional


class Asset(Base):
    """Asset model representing refinery equipment."""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    asset_type = Column(String, nullable=False)  # pump, compressor, heat_exchanger, etc.
    location = Column(String, nullable=True)
    status = Column(String, default="operational")  # operational, maintenance, critical
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SensorReading(Base):
    """Sensor reading model for time-series data."""
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, index=True, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), index=True, nullable=False)
    temperature = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)
    vibration = Column(Float, nullable=True)
    flow = Column(Float, nullable=True)
    rpm = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class DigitalTwinState(Base):
    """Digital twin state model for expected behavior curves."""
    __tablename__ = "digital_twin_states"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, index=True, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), index=True, nullable=False)
    expected_temperature = Column(Float, nullable=True)
    expected_pressure = Column(Float, nullable=True)
    expected_vibration = Column(Float, nullable=True)
    expected_flow = Column(Float, nullable=True)
    expected_rpm = Column(Float, nullable=True)
    deviation_score = Column(Float, nullable=True)  # 0-100, higher = more deviation


class HealthScore(Base):
    """Health score model for asset health tracking."""
    __tablename__ = "health_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, index=True, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), index=True, nullable=False)
    health_index = Column(Float, nullable=False)  # 0-100, higher = healthier
    twin_deviation_score = Column(Float, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    rul_days = Column(Float, nullable=True)  # Remaining Useful Life in days
    failure_risk_score = Column(Float, nullable=True)  # 0-100, higher = more risk


class Prediction(Base):
    """Prediction model for ML forecasts."""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, index=True, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), index=True, nullable=False)
    prediction_type = Column(String, nullable=False)  # forecast, anomaly, rul
    predicted_value = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    forecast_horizon_hours = Column(Integer, nullable=True)
    metadata_json = Column(Text, nullable=True)  # JSON string for additional data


class Alert(Base):
    """Alert model for threshold and ML-based alerts."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, index=True, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), index=True, nullable=False)
    alert_type = Column(String, nullable=False)  # threshold, anomaly, health, rul
    severity = Column(String, nullable=False)  # info, warning, critical
    message = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

