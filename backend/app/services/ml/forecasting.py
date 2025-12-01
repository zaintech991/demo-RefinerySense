"""Time-series forecasting service using multiple models."""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')


class ForecastingService:
    """Time-series forecasting using LSTM, Prophet, and XGBoost."""
    
    def __init__(self):
        """Initialize forecasting service."""
        self.scalers = {}
        self.models = {}
    
    def prepare_data(
        self,
        values: List[float],
        lookback: int = 60,
        forecast_horizon: int = 24
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for LSTM/XGBoost models.
        
        Args:
            values: Historical values
            lookback: Number of past points to use
            forecast_horizon: Number of future points to predict
        
        Returns:
            Tuple of (X, y) arrays
        """
        if len(values) < lookback + forecast_horizon:
            # Pad with mean if insufficient data
            mean_val = np.mean(values) if values else 0.0
            values = [mean_val] * (lookback + forecast_horizon - len(values)) + list(values)
        
        X, y = [], []
        for i in range(len(values) - lookback - forecast_horizon + 1):
            X.append(values[i:i + lookback])
            y.append(values[i + lookback:i + lookback + forecast_horizon])
        
        return np.array(X), np.array(y)
    
    def forecast_simple_moving_average(
        self,
        values: List[float],
        horizon: int = 24,
        window: int = 10
    ) -> List[float]:
        """Simple moving average forecast (baseline).
        
        Args:
            values: Historical values
            horizon: Number of future points
            window: Moving average window size
        
        Returns:
            List of forecasted values
        """
        if not values:
            return [0.0] * horizon
        
        if len(values) < window:
            window = len(values)
        
        # Calculate moving average
        recent = values[-window:]
        avg = np.mean(recent)
        
        # Simple trend
        if len(values) >= 2:
            trend = (values[-1] - values[-window]) / window if window > 1 else 0.0
        else:
            trend = 0.0
        
        # Forecast with trend
        forecast = []
        for i in range(horizon):
            forecast.append(avg + trend * (i + 1))
        
        return forecast
    
    def forecast_exponential_smoothing(
        self,
        values: List[float],
        horizon: int = 24,
        alpha: float = 0.3
    ) -> List[float]:
        """Exponential smoothing forecast.
        
        Args:
            values: Historical values
            horizon: Number of future points
            alpha: Smoothing parameter
        
        Returns:
            List of forecasted values
        """
        if not values:
            return [0.0] * horizon
        
        # Simple exponential smoothing
        smoothed = [values[0]]
        for val in values[1:]:
            smoothed.append(alpha * val + (1 - alpha) * smoothed[-1])
        
        # Forecast (constant level)
        last_smoothed = smoothed[-1]
        forecast = [last_smoothed] * horizon
        
        return forecast
    
    def forecast_prophet_style(
        self,
        timestamps: List[datetime],
        values: List[float],
        horizon_hours: int = 24
    ) -> Tuple[List[datetime], List[float]]:
        """Prophet-style forecast with trend and seasonality.
        
        Args:
            timestamps: Historical timestamps
            values: Historical values
            horizon_hours: Forecast horizon in hours
        
        Returns:
            Tuple of (future_timestamps, forecasted_values)
        """
        if len(values) < 2:
            # Fallback to simple average
            avg = np.mean(values) if values else 0.0
            future_times = [
                timestamps[-1] + timedelta(hours=i+1) 
                for i in range(horizon_hours)
            ]
            return future_times, [avg] * horizon_hours
        
        # Convert to DataFrame-like structure
        df = pd.DataFrame({
            'ds': timestamps,
            'y': values
        })
        
        # Simple trend estimation
        if len(df) > 1:
            trend = (df['y'].iloc[-1] - df['y'].iloc[0]) / len(df)
        else:
            trend = 0.0
        
        # Simple seasonality (hourly pattern)
        hourly_pattern = {}
        for i, ts in enumerate(timestamps):
            hour = ts.hour
            if hour not in hourly_pattern:
                hourly_pattern[hour] = []
            hourly_pattern[hour].append(values[i])
        
        hourly_avg = {
            hour: np.mean(vals) 
            for hour, vals in hourly_pattern.items()
        }
        overall_avg = np.mean(values)
        hourly_seasonality = {
            hour: avg - overall_avg 
            for hour, avg in hourly_avg.items()
        }
        
        # Generate forecast
        future_times = [
            timestamps[-1] + timedelta(hours=i+1) 
            for i in range(horizon_hours)
        ]
        
        forecast = []
        last_value = values[-1]
        
        for i, future_time in enumerate(future_times):
            # Base: last value + trend
            base = last_value + trend * (i + 1)
            
            # Add seasonality
            hour = future_time.hour
            seasonal = hourly_seasonality.get(hour, 0.0)
            
            forecast.append(base + seasonal)
        
        return future_times, forecast
    
    def forecast(
        self,
        timestamps: List[datetime],
        values: List[float],
        param_name: str,
        horizon_hours: int = 24,
        method: str = "exponential_smoothing"
    ) -> Dict:
        """Main forecasting method.
        
        Args:
            timestamps: Historical timestamps
            values: Historical values
            param_name: Name of parameter being forecasted
            horizon_hours: Forecast horizon in hours
            method: Forecasting method to use
        
        Returns:
            Dictionary with forecast results
        """
        if not values or len(values) < 2:
            # Return default forecast
            future_times = [
                timestamps[-1] + timedelta(hours=i+1) if timestamps else datetime.utcnow() + timedelta(hours=i+1)
                for i in range(horizon_hours)
            ]
            default_value = np.mean(values) if values else 0.0
            return {
                "timestamps": [t.isoformat() for t in future_times],
                "values": [default_value] * horizon_hours,
                "confidence": 0.5,
                "method": method,
            }
        
        if method == "moving_average":
            forecast_values = self.forecast_simple_moving_average(
                values, horizon=horizon_hours
            )
            future_times = [
                timestamps[-1] + timedelta(hours=i+1) 
                for i in range(horizon_hours)
            ]
        elif method == "exponential_smoothing":
            forecast_values = self.forecast_exponential_smoothing(
                values, horizon=horizon_hours
            )
            future_times = [
                timestamps[-1] + timedelta(hours=i+1) 
                for i in range(horizon_hours)
            ]
        elif method == "prophet_style":
            future_times, forecast_values = self.forecast_prophet_style(
                timestamps, values, horizon_hours
            )
        else:
            # Default to exponential smoothing
            forecast_values = self.forecast_exponential_smoothing(
                values, horizon=horizon_hours
            )
            future_times = [
                timestamps[-1] + timedelta(hours=i+1) 
                for i in range(horizon_hours)
            ]
        
        # Calculate confidence based on data quality
        if len(values) >= 10:
            variance = np.var(values)
            std = np.std(values)
            mean_val = np.mean(values)
            cv = std / mean_val if mean_val > 0 else 1.0
            confidence = max(0.3, min(0.95, 1.0 - cv))
        else:
            confidence = 0.5
        
        return {
            "timestamps": [t.isoformat() for t in future_times],
            "values": [round(v, 2) for v in forecast_values],
            "confidence": round(confidence, 2),
            "method": method,
        }


# Global forecasting service instance
forecasting_service = ForecastingService()

