"""Digital Twin service for expected behavior modeling and deviation scoring."""
import numpy as np
from sqlalchemy.orm import Session
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from app.models import DigitalTwinState, SensorReading, Asset
from app.schemas import DigitalTwinStateResponse


class DigitalTwin:
    """Digital Twin model for asset expected behavior."""
    
    def __init__(self):
        """Initialize digital twin with baseline models."""
        # Expected behavior profiles (can be learned from historical data)
        self.baseline_profiles = {
            "pump": {
                "temperature": {"mean": 65.0, "std": 5.0},
                "pressure": {"mean": 2.5, "std": 0.3},
                "vibration": {"mean": 2.5, "std": 0.5},
                "flow": {"mean": 120.0, "std": 15.0},
                "rpm": {"mean": 1450.0, "std": 50.0},
            },
            "compressor": {
                "temperature": {"mean": 85.0, "std": 8.0},
                "pressure": {"mean": 8.5, "std": 1.2},
                "vibration": {"mean": 3.5, "std": 0.8},
                "flow": {"mean": 250.0, "std": 30.0},
                "rpm": {"mean": 3600.0, "std": 100.0},
            },
            "heat_exchanger": {
                "temperature": {"mean": 95.0, "std": 10.0},
                "pressure": {"mean": 4.2, "std": 0.5},
                "vibration": {"mean": 1.8, "std": 0.4},
                "flow": {"mean": 180.0, "std": 20.0},
                "rpm": {"mean": 0.0, "std": 0.0},
            },
        }
    
    def get_expected_values(
        self,
        asset_type: str,
        load_factor: float = 1.0,
        time_of_day: Optional[float] = None
    ) -> Dict[str, float]:
        """Get expected sensor values for an asset under given conditions.
        
        Args:
            asset_type: Type of asset
            load_factor: Load multiplier (1.0 = normal, 1.5 = high load, etc.)
            time_of_day: Optional time of day factor for cyclic patterns
        
        Returns:
            Dictionary of expected sensor values
        """
        if asset_type not in self.baseline_profiles:
            asset_type = "pump"
        
        profile = self.baseline_profiles[asset_type]
        expected = {}
        
        # Time-based variation (simulate daily cycles)
        time_factor = 1.0
        if time_of_day is not None:
            # Simulate higher load during day hours
            hour = int(time_of_day) % 24
            if 8 <= hour <= 18:
                time_factor = 1.1
            else:
                time_factor = 0.95
        
        for param, stats in profile.items():
            if param == "rpm" and stats["mean"] == 0.0:
                expected[param] = 0.0
            else:
                # Expected value with load and time factors
                expected[param] = stats["mean"] * load_factor * time_factor
        
        return expected
    
    def calculate_deviation_score(
        self,
        actual: Dict[str, Optional[float]],
        expected: Dict[str, float],
        asset_type: str
    ) -> float:
        """Calculate deviation score between actual and expected values.
        
        Args:
            actual: Actual sensor readings
            expected: Expected sensor readings
            asset_type: Type of asset
        
        Returns:
            Deviation score (0-100, higher = more deviation)
        """
        if asset_type not in self.baseline_profiles:
            asset_type = "pump"
        
        profile = self.baseline_profiles[asset_type]
        deviations = []
        
        for param in ["temperature", "pressure", "vibration", "flow", "rpm"]:
            if param not in actual or actual[param] is None:
                continue
            if param not in expected:
                continue
            if param == "rpm" and profile[param]["mean"] == 0.0:
                continue
            
            actual_val = actual[param]
            expected_val = expected[param]
            std = profile[param]["std"]
            
            if std > 0:
                # Z-score based deviation
                z_score = abs(actual_val - expected_val) / std
                # Convert to 0-100 scale (3 sigma = 100)
                deviation = min(100.0, (z_score / 3.0) * 100.0)
                deviations.append(deviation)
        
        if not deviations:
            return 0.0
        
        # Weighted average (temperature and pressure are more critical)
        weights = {
            "temperature": 0.3,
            "pressure": 0.3,
            "vibration": 0.2,
            "flow": 0.15,
            "rpm": 0.05,
        }
        
        # Build a map of parameter to deviation
        param_deviations = {}
        deviation_idx = 0
        
        for param in ["temperature", "pressure", "vibration", "flow", "rpm"]:
            if param not in actual or actual[param] is None:
                continue
            if param not in expected:
                continue
            if param == "rpm" and profile[param]["mean"] == 0.0:
                continue
            
            # This parameter was processed, so it has a deviation
            if deviation_idx < len(deviations):
                param_deviations[param] = deviations[deviation_idx]
                deviation_idx += 1
        
        # Calculate weighted average using the mapped deviations
        weighted_sum = 0.0
        total_weight = 0.0
        
        for param, deviation in param_deviations.items():
            weight = weights.get(param, 0.2)
            weighted_sum += deviation * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def create_twin_state(
        self,
        db: Session,
        asset_id: int,
        actual_reading: Dict[str, Optional[float]],
        load_factor: float = 1.0
    ) -> DigitalTwinState:
        """Create and store a digital twin state.
        
        Args:
            db: Database session
            asset_id: ID of the asset
            actual_reading: Actual sensor reading
            load_factor: Current load factor
        
        Returns:
            Created DigitalTwinState object
        """
        # Get asset type
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")
        
        asset_type = asset.asset_type
        
        # Get expected values
        time_of_day = datetime.utcnow().hour + datetime.utcnow().minute / 60.0
        expected = self.get_expected_values(asset_type, load_factor, time_of_day)
        
        # Calculate deviation
        deviation_score = self.calculate_deviation_score(actual_reading, expected, asset_type)
        
        # Store twin state
        twin_state = DigitalTwinState(
            asset_id=asset_id,
            timestamp=datetime.utcnow(),
            expected_temperature=expected.get("temperature"),
            expected_pressure=expected.get("pressure"),
            expected_vibration=expected.get("vibration"),
            expected_flow=expected.get("flow"),
            expected_rpm=expected.get("rpm"),
            deviation_score=round(deviation_score, 2),
        )
        
        db.add(twin_state)
        db.commit()
        db.refresh(twin_state)
        
        return twin_state
    
    def simulate_what_if(
        self,
        asset_type: str,
        scenario: str,
        base_load: float = 1.0
    ) -> Dict[str, float]:
        """Simulate 'what-if' scenarios.
        
        Args:
            asset_type: Type of asset
            scenario: Scenario name (e.g., "load_increase", "temp_spike", "pressure_drop")
            base_load: Base load factor
        
        Returns:
            Expected values under the scenario
        """
        load_factor = base_load
        
        if scenario == "load_increase":
            load_factor = base_load * 1.5
        elif scenario == "load_decrease":
            load_factor = base_load * 0.7
        elif scenario == "temp_spike":
            # This would affect expected temperature specifically
            expected = self.get_expected_values(asset_type, base_load)
            expected["temperature"] *= 1.3
            return expected
        elif scenario == "pressure_drop":
            expected = self.get_expected_values(asset_type, base_load)
            expected["pressure"] *= 0.8
            return expected
        
        return self.get_expected_values(asset_type, load_factor)


# Global digital twin instance
digital_twin = DigitalTwin()

