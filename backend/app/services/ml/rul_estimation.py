"""Remaining Useful Life (RUL) estimation service."""
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression


class RULEstimationService:
    """Remaining Useful Life estimation using degradation modeling."""
    
    def __init__(self):
        """Initialize RUL estimation service."""
        self.degradation_models = {}
        self.failure_thresholds = {
            "pump": {
                "temperature": 100.0,
                "pressure": 4.5,
                "vibration": 8.0,
                "health_index": 30.0,
            },
            "compressor": {
                "temperature": 130.0,
                "pressure": 15.0,
                "vibration": 10.0,
                "health_index": 30.0,
            },
            "heat_exchanger": {
                "temperature": 150.0,
                "pressure": 8.0,
                "vibration": 6.0,
                "health_index": 30.0,
            },
        }
    
    def estimate_rul_health_based(
        self,
        health_scores: List[float],
        timestamps: List[datetime],
        failure_threshold: float = 30.0
    ) -> Optional[float]:
        """Estimate RUL based on health score degradation trend.
        
        Args:
            health_scores: Historical health scores
            timestamps: Historical timestamps
            failure_threshold: Health score threshold for failure
        
        Returns:
            Estimated RUL in days, or None if insufficient data
        """
        if not health_scores or len(health_scores) < 3:
            return None
        
        # Filter to recent data (last 30 days worth)
        if len(health_scores) > 100:
            health_scores = health_scores[-100:]
            timestamps = timestamps[-100:]
        
        # Convert timestamps to days since first timestamp
        first_ts = timestamps[0]
        days_since_start = [
            (ts - first_ts).total_seconds() / 86400.0
            for ts in timestamps
        ]
        
        # Fit linear regression to degradation trend
        X = np.array(days_since_start).reshape(-1, 1)
        y = np.array(health_scores)
        
        try:
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict when health will reach failure threshold
            current_health = health_scores[-1]
            current_days = days_since_start[-1]
            
            if model.coef_[0] >= 0:  # Health is improving or stable
                return None  # No failure predicted
            
            # Solve: threshold = intercept + slope * days_to_failure
            if model.coef_[0] != 0:
                days_to_failure = (failure_threshold - model.intercept_) / model.coef_[0]
                rul_days = max(0.0, days_to_failure - current_days)
            else:
                return None
            
            return rul_days
            
        except Exception:
            return None
    
    def estimate_rul_parameter_based(
        self,
        param_values: List[float],
        timestamps: List[datetime],
        failure_threshold: float,
        param_name: str
    ) -> Optional[float]:
        """Estimate RUL based on parameter degradation.
        
        Args:
            param_values: Historical parameter values
            timestamps: Historical timestamps
            failure_threshold: Threshold value for failure
            param_name: Name of parameter
        
        Returns:
            Estimated RUL in days, or None if insufficient data
        """
        if not param_values or len(param_values) < 3:
            return None
        
        # Determine if parameter is increasing or decreasing toward failure
        # For temperature/pressure/vibration: increasing is bad
        # For flow: decreasing might be bad
        is_increasing_toward_failure = param_name in ["temperature", "pressure", "vibration"]
        
        current_value = param_values[-1]
        
        if is_increasing_toward_failure:
            if current_value >= failure_threshold:
                return 0.0  # Already at failure
            if current_value < failure_threshold * 0.7:
                return None  # Too far from threshold, unreliable prediction
        else:
            if current_value <= failure_threshold:
                return 0.0
            if current_value > failure_threshold * 1.3:
                return None
        
        # Convert timestamps to days
        first_ts = timestamps[0]
        days_since_start = [
            (ts - first_ts).total_seconds() / 86400.0
            for ts in timestamps
        ]
        
        # Fit trend
        X = np.array(days_since_start).reshape(-1, 1)
        y = np.array(param_values)
        
        try:
            model = LinearRegression()
            model.fit(X, y)
            
            current_days = days_since_start[-1]
            
            if is_increasing_toward_failure:
                if model.coef_[0] <= 0:  # Not trending toward failure
                    return None
                # Solve for when value reaches threshold
                if model.coef_[0] != 0:
                    days_to_failure = (failure_threshold - model.intercept_) / model.coef_[0]
                    rul_days = max(0.0, days_to_failure - current_days)
                else:
                    return None
            else:
                if model.coef_[0] >= 0:  # Not trending toward failure
                    return None
                if model.coef_[0] != 0:
                    days_to_failure = (failure_threshold - model.intercept_) / model.coef_[0]
                    rul_days = max(0.0, days_to_failure - current_days)
                else:
                    return None
            
            return rul_days
            
        except Exception:
            return None
    
    def estimate_rul(
        self,
        asset_type: str,
        health_scores: List[float],
        health_timestamps: List[datetime],
        sensor_readings: List[Dict],
        reading_timestamps: List[datetime]
    ) -> Dict:
        """Main RUL estimation method combining multiple approaches.
        
        Args:
            asset_type: Type of asset
            health_scores: Historical health scores
            health_timestamps: Health score timestamps
            sensor_readings: Historical sensor readings
            reading_timestamps: Reading timestamps
        
        Returns:
            Dictionary with RUL estimates
        """
        if asset_type not in self.failure_thresholds:
            asset_type = "pump"
        
        thresholds = self.failure_thresholds[asset_type]
        
        # Method 1: Health-based RUL
        health_rul = self.estimate_rul_health_based(
            health_scores,
            health_timestamps,
            thresholds["health_index"]
        )
        
        # Method 2: Parameter-based RULs
        param_ruls = {}
        for param in ["temperature", "pressure", "vibration"]:
            if param not in thresholds:
                continue
            
            param_values = []
            param_timestamps = []
            
            for i, reading in enumerate(sensor_readings):
                if param in reading and reading[param] is not None:
                    param_values.append(reading[param])
                    param_timestamps.append(reading_timestamps[i])
            
            if len(param_values) >= 3:
                param_rul = self.estimate_rul_parameter_based(
                    param_values,
                    param_timestamps,
                    thresholds[param],
                    param
                )
                if param_rul is not None:
                    param_ruls[param] = param_rul
        
        # Combine estimates (take minimum as conservative estimate)
        all_ruls = []
        if health_rul is not None:
            all_ruls.append(health_rul)
        all_ruls.extend(param_ruls.values())
        
        if not all_ruls:
            # Default: estimate based on current health if available
            if health_scores:
                current_health = health_scores[-1]
                if current_health < 50.0:
                    # Rough estimate: assume linear degradation
                    estimated_rul = (current_health - thresholds["health_index"]) * 2.0
                    estimated_rul = max(1.0, estimated_rul)  # At least 1 day
                else:
                    estimated_rul = None
            else:
                estimated_rul = None
        else:
            estimated_rul = min(all_ruls)
        
        # Calculate failure risk score (0-100)
        if estimated_rul is not None:
            if estimated_rul <= 7:
                risk_score = 90.0
            elif estimated_rul <= 30:
                risk_score = 70.0
            elif estimated_rul <= 90:
                risk_score = 50.0
            else:
                risk_score = 30.0
        else:
            risk_score = 20.0  # Low risk if no failure predicted
        
        return {
            "rul_days": round(estimated_rul, 1) if estimated_rul is not None else None,
            "risk_score": round(risk_score, 2),
            "health_based_rul": round(health_rul, 1) if health_rul is not None else None,
            "param_based_ruls": {k: round(v, 1) for k, v in param_ruls.items()},
        }


# Global RUL estimation service instance
rul_estimation_service = RULEstimationService()

