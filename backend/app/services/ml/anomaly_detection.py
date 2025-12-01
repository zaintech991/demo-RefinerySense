"""Anomaly detection service using Isolation Forest and statistical methods."""
import numpy as np
from typing import List, Dict, Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime


class AnomalyDetectionService:
    """Anomaly detection using Isolation Forest and statistical methods."""
    
    def __init__(self):
        """Initialize anomaly detection service."""
        self.isolation_forests = {}
        self.scalers = {}
        self.baseline_stats = {}
    
    def calculate_statistical_anomaly_score(
        self,
        values: List[float],
        current_value: float
    ) -> float:
        """Calculate anomaly score using statistical methods (Z-score).
        
        Args:
            values: Historical values
            current_value: Current value to check
        
        Returns:
            Anomaly score (0-100, higher = more anomalous)
        """
        if not values or len(values) < 3:
            return 0.0
        
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if std_val == 0:
            return 0.0
        
        # Z-score
        z_score = abs(current_value - mean_val) / std_val
        
        # Convert to 0-100 scale (3 sigma = 100)
        anomaly_score = min(100.0, (z_score / 3.0) * 100.0)
        
        return anomaly_score
    
    def detect_isolation_forest(
        self,
        feature_matrix: np.ndarray,
        contamination: float = 0.1
    ) -> tuple[np.ndarray, IsolationForest]:
        """Detect anomalies using Isolation Forest.
        
        Args:
            feature_matrix: Feature matrix (n_samples, n_features)
            contamination: Expected proportion of anomalies
        
        Returns:
            Tuple of (anomaly_labels, fitted_model)
        """
        if len(feature_matrix) < 2:
            return np.array([0]), None
        
        # Fit Isolation Forest
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        
        # Scale features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(feature_matrix)
        
        # Fit and predict
        predictions = iso_forest.fit_predict(scaled_features)
        
        # Convert to binary (1 = normal, -1 = anomaly)
        anomaly_labels = (predictions == -1).astype(int)
        
        return anomaly_labels, iso_forest
    
    def detect_anomaly_multi_param(
        self,
        readings: List[Dict],
        current_reading: Dict
    ) -> Dict:
        """Detect anomalies across multiple parameters.
        
        Args:
            readings: Historical readings
            current_reading: Current reading to check
        
        Returns:
            Dictionary with anomaly detection results
        """
        if not readings or len(readings) < 3:
            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "anomalous_params": [],
            }
        
        # Extract parameter values
        params = ["temperature", "pressure", "vibration", "flow", "rpm"]
        param_values = {param: [] for param in params}
        
        for reading in readings:
            for param in params:
                if param in reading and reading[param] is not None:
                    param_values[param].append(reading[param])
        
        # Calculate anomaly scores per parameter
        anomaly_scores = {}
        anomalous_params = []
        
        for param in params:
            if param not in current_reading or current_reading[param] is None:
                continue
            if len(param_values[param]) < 3:
                continue
            
            score = self.calculate_statistical_anomaly_score(
                param_values[param],
                current_reading[param]
            )
            anomaly_scores[param] = score
            
            if score > 70.0:  # Threshold for anomaly
                anomalous_params.append(param)
        
        # Overall anomaly score (weighted average)
        if anomaly_scores:
            # Weight critical parameters more
            weights = {
                "temperature": 0.3,
                "pressure": 0.3,
                "vibration": 0.2,
                "flow": 0.15,
                "rpm": 0.05,
            }
            
            weighted_sum = sum(
                score * weights.get(param, 0.2)
                for param, score in anomaly_scores.items()
            )
            total_weight = sum(
                weights.get(param, 0.2)
                for param in anomaly_scores.keys()
            )
            
            overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        else:
            overall_score = 0.0
        
        is_anomaly = overall_score > 70.0 or len(anomalous_params) > 0
        
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(overall_score, 2),
            "anomalous_params": anomalous_params,
            "param_scores": anomaly_scores,
        }
    
    def detect_anomaly_isolation_forest(
        self,
        readings: List[Dict],
        current_reading: Dict
    ) -> Dict:
        """Detect anomalies using Isolation Forest on feature matrix.
        
        Args:
            readings: Historical readings
            current_reading: Current reading to check
        
        Returns:
            Dictionary with anomaly detection results
        """
        if not readings or len(readings) < 5:
            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "method": "isolation_forest",
            }
        
        # Build feature matrix
        params = ["temperature", "pressure", "vibration", "flow", "rpm"]
        features = []
        
        for reading in readings + [current_reading]:
            feature_vector = []
            for param in params:
                if param in reading and reading[param] is not None:
                    feature_vector.append(reading[param])
                else:
                    feature_vector.append(0.0)
            features.append(feature_vector)
        
        feature_matrix = np.array(features)
        
        # Detect anomalies
        anomaly_labels, model = self.detect_isolation_forest(feature_matrix)
        
        if model is None:
            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "method": "isolation_forest",
            }
        
        # Check if current reading is anomalous
        current_is_anomaly = anomaly_labels[-1] == 1
        
        # Calculate anomaly score based on distance to decision boundary
        # (simplified: use proportion of anomalies in recent window)
        recent_window = min(20, len(anomaly_labels))
        recent_anomalies = np.sum(anomaly_labels[-recent_window:])
        anomaly_score = (recent_anomalies / recent_window) * 100.0
        
        return {
            "is_anomaly": current_is_anomaly,
            "anomaly_score": round(anomaly_score, 2),
            "method": "isolation_forest",
        }


# Global anomaly detection service instance
anomaly_detection_service = AnomalyDetectionService()

