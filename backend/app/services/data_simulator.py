"""Data simulator service for generating realistic sensor data."""
import asyncio
import random
import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta


class DataSimulator:
    """Simulates sensor data for refinery equipment."""
    
    def __init__(self):
        """Initialize simulator with base parameters for different asset types."""
        # Base parameters for different asset types
        self.asset_profiles = {
            "pump": {
                "temperature": {"base": 65.0, "std": 5.0, "range": (55, 85)},
                "pressure": {"base": 2.5, "std": 0.3, "range": (1.8, 3.5)},
                "vibration": {"base": 2.5, "std": 0.5, "range": (1.0, 5.0)},
                "flow": {"base": 120.0, "std": 15.0, "range": (80, 180)},
                "rpm": {"base": 1450.0, "std": 50.0, "range": (1200, 1750)},
            },
            "compressor": {
                "temperature": {"base": 85.0, "std": 8.0, "range": (70, 110)},
                "pressure": {"base": 8.5, "std": 1.2, "range": (6.0, 12.0)},
                "vibration": {"base": 3.5, "std": 0.8, "range": (1.5, 7.0)},
                "flow": {"base": 250.0, "std": 30.0, "range": (180, 350)},
                "rpm": {"base": 3600.0, "std": 100.0, "range": (3000, 4200)},
            },
            "heat_exchanger": {
                "temperature": {"base": 95.0, "std": 10.0, "range": (75, 130)},
                "pressure": {"base": 4.2, "std": 0.5, "range": (3.0, 6.0)},
                "vibration": {"base": 1.8, "std": 0.4, "range": (0.5, 4.0)},
                "flow": {"base": 180.0, "std": 20.0, "range": (120, 250)},
                "rpm": {"base": 0.0, "std": 0.0, "range": (0, 0)},  # No RPM for heat exchangers
            },
        }
        
        # Track state per asset for gradual degradation simulation
        self.asset_states: Dict[int, Dict] = {}
        self.degradation_factors: Dict[int, float] = {}
    
    def initialize_asset(self, asset_id: int, asset_type: str):
        """Initialize state tracking for an asset."""
        if asset_id not in self.asset_states:
            self.asset_states[asset_id] = {
                "asset_type": asset_type,
                "last_values": {},
                "trend": 1.0,  # Multiplier for gradual changes
            }
            self.degradation_factors[asset_id] = 1.0
    
    def generate_reading(
        self, 
        asset_id: int, 
        asset_type: str,
        inject_anomaly: bool = False,
        anomaly_severity: float = 0.5
    ) -> Dict:
        """Generate a single sensor reading for an asset.
        
        Args:
            asset_id: ID of the asset
            asset_type: Type of asset (pump, compressor, heat_exchanger)
            inject_anomaly: Whether to inject an anomaly
            anomaly_severity: Severity of anomaly (0.0 to 1.0)
        
        Returns:
            Dictionary with sensor readings
        """
        self.initialize_asset(asset_id, asset_type)
        
        if asset_type not in self.asset_profiles:
            asset_type = "pump"  # Default fallback
        
        profile = self.asset_profiles[asset_type]
        state = self.asset_states[asset_id]
        
        # Gradually increase degradation over time (simulate wear)
        if random.random() < 0.01:  # 1% chance to increase degradation
            self.degradation_factors[asset_id] = min(
                self.degradation_factors[asset_id] + 0.01, 
                1.5  # Max 50% degradation
            )
        
        degradation = self.degradation_factors[asset_id]
        
        # Generate readings with some correlation and trends
        reading = {}
        
        for param, config in profile.items():
            if param == "rpm" and config["base"] == 0.0:
                reading[param] = 0.0
                continue
            
            # Base value with degradation
            base_value = config["base"] * degradation
            
            # Add some trend/seasonality
            trend_factor = state.get("trend", 1.0)
            if random.random() < 0.1:  # Occasionally change trend
                state["trend"] = 1.0 + random.uniform(-0.1, 0.1)
            
            # Generate value with normal distribution
            value = np.random.normal(
                base_value * trend_factor,
                config["std"]
            )
            
            # Inject anomaly if requested
            if inject_anomaly:
                if param in ["temperature", "pressure", "vibration"]:
                    # Anomaly: spike in these parameters
                    anomaly_multiplier = 1.0 + (anomaly_severity * random.uniform(0.5, 2.0))
                    value *= anomaly_multiplier
                elif param == "flow":
                    # Anomaly: drop in flow
                    value *= (1.0 - anomaly_severity * random.uniform(0.2, 0.6))
            
            # Clamp to realistic range
            value = max(config["range"][0], min(config["range"][1], value))
            
            reading[param] = round(value, 2)
        
        # Store last values for next iteration
        state["last_values"] = reading.copy()
        
        return reading
    
    async def stream_readings(
        self,
        asset_id: int,
        asset_type: str,
        interval_seconds: float = 3.0,
        anomaly_probability: float = 0.05
    ):
        """Async generator that yields sensor readings at intervals.
        
        Args:
            asset_id: ID of the asset
            asset_type: Type of asset
            interval_seconds: Time between readings
            anomaly_probability: Probability of injecting an anomaly (0.0 to 1.0)
        
        Yields:
            Dictionary with sensor readings and timestamp
        """
        while True:
            inject_anomaly = random.random() < anomaly_probability
            anomaly_severity = random.uniform(0.3, 0.8) if inject_anomaly else 0.0
            
            reading = self.generate_reading(
                asset_id=asset_id,
                asset_type=asset_type,
                inject_anomaly=inject_anomaly,
                anomaly_severity=anomaly_severity
            )
            
            reading["timestamp"] = datetime.utcnow().isoformat()
            reading["asset_id"] = asset_id
            
            yield reading
            
            await asyncio.sleep(interval_seconds)


# Global simulator instance
simulator = DataSimulator()

