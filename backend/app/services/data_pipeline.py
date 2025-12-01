"""Data pipeline service for ingesting, validating, and storing sensor data."""
from sqlalchemy.orm import Session
from typing import Dict, Optional
from datetime import datetime
from app.models import SensorReading
from app.schemas import SensorReadingCreate


class DataPipeline:
    """Handles data ingestion, validation, normalization, and storage."""
    
    @staticmethod
    def validate_reading(reading: Dict) -> tuple[bool, Optional[str]]:
        """Validate sensor reading data.
        
        Args:
            reading: Dictionary with sensor readings
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ["asset_id"]
        
        # Check required fields
        for field in required_fields:
            if field not in reading:
                return False, f"Missing required field: {field}"
        
        # Validate numeric ranges
        validations = {
            "temperature": (-50, 200),
            "pressure": (0, 50),
            "vibration": (0, 20),
            "flow": (0, 1000),
            "rpm": (0, 10000),
        }
        
        for param, (min_val, max_val) in validations.items():
            if param in reading and reading[param] is not None:
                if not isinstance(reading[param], (int, float)):
                    return False, f"Invalid type for {param}: expected number"
                if reading[param] < min_val or reading[param] > max_val:
                    return False, f"{param} out of range: {reading[param]} not in [{min_val}, {max_val}]"
        
        return True, None
    
    @staticmethod
    def normalize_reading(reading: Dict) -> Dict:
        """Normalize sensor reading data.
        
        Args:
            reading: Raw sensor reading dictionary
        
        Returns:
            Normalized reading dictionary
        """
        normalized = reading.copy()
        
        # Round numeric values to 2 decimal places
        numeric_fields = ["temperature", "pressure", "vibration", "flow", "rpm"]
        for field in numeric_fields:
            if field in normalized and normalized[field] is not None:
                normalized[field] = round(float(normalized[field]), 2)
        
        # Ensure timestamp is present
        if "timestamp" not in normalized:
            normalized["timestamp"] = datetime.utcnow()
        elif isinstance(normalized["timestamp"], str):
            normalized["timestamp"] = datetime.fromisoformat(normalized["timestamp"].replace("Z", "+00:00"))
        
        return normalized
    
    @staticmethod
    def store_reading(db: Session, reading: Dict) -> SensorReading:
        """Store validated and normalized reading in database.
        
        Args:
            db: Database session
            reading: Normalized sensor reading dictionary
        
        Returns:
            Created SensorReading object
        """
        # Normalize timestamp
        timestamp = reading.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif timestamp is None:
            timestamp = datetime.utcnow()
        
        db_reading = SensorReading(
            asset_id=reading["asset_id"],
            timestamp=timestamp,
            temperature=reading.get("temperature"),
            pressure=reading.get("pressure"),
            vibration=reading.get("vibration"),
            flow=reading.get("flow"),
            rpm=reading.get("rpm"),
        )
        
        db.add(db_reading)
        db.commit()
        db.refresh(db_reading)
        
        return db_reading
    
    @staticmethod
    def process_reading(db: Session, reading: Dict) -> tuple[Optional[SensorReading], Optional[str]]:
        """Complete pipeline: validate, normalize, and store.
        
        Args:
            db: Database session
            reading: Raw sensor reading dictionary
        
        Returns:
            Tuple of (stored_reading, error_message)
        """
        # Validate
        is_valid, error = DataPipeline.validate_reading(reading)
        if not is_valid:
            return None, error
        
        # Normalize
        normalized = DataPipeline.normalize_reading(reading)
        
        # Store
        try:
            stored = DataPipeline.store_reading(db, normalized)
            return stored, None
        except Exception as e:
            return None, str(e)

