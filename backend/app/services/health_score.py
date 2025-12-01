"""Health Score Engine that combines all scores."""
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.models import HealthScore
from app.services.digital_twin import digital_twin
from app.services.ml.anomaly_detection import anomaly_detection_service
from app.services.ml.rul_estimation import rul_estimation_service


class HealthScoreEngine:
    """Health Score Engine combining twin deviation, anomalies, and RUL."""
    
    def calculate_health_index(
        self,
        twin_deviation_score: float,
        anomaly_score: float,
        rul_days: Optional[float],
        failure_risk_score: float
    ) -> float:
        """Calculate overall health index from component scores.
        
        Args:
            twin_deviation_score: Deviation from expected behavior (0-100)
            anomaly_score: Anomaly detection score (0-100)
            rul_days: Remaining Useful Life in days
            failure_risk_score: Failure risk score (0-100)
        
        Returns:
            Health index (0-100, higher = healthier)
        """
        # Normalize scores (invert so higher = better)
        twin_health = max(0.0, 100.0 - twin_deviation_score)
        anomaly_health = max(0.0, 100.0 - anomaly_score)
        risk_health = max(0.0, 100.0 - failure_risk_score)
        
        # RUL-based health (convert days to health score)
        if rul_days is not None:
            if rul_days <= 7:
                rul_health = 20.0
            elif rul_days <= 30:
                rul_health = 40.0
            elif rul_days <= 90:
                rul_health = 60.0
            elif rul_days <= 180:
                rul_health = 80.0
            else:
                rul_health = 95.0
        else:
            rul_health = 70.0  # Default if no RUL estimate
        
        # Weighted combination
        weights = {
            "twin": 0.3,
            "anomaly": 0.3,
            "rul": 0.25,
            "risk": 0.15,
        }
        
        health_index = (
            twin_health * weights["twin"] +
            anomaly_health * weights["anomaly"] +
            rul_health * weights["rul"] +
            risk_health * weights["risk"]
        )
        
        return round(max(0.0, min(100.0, health_index)), 2)
    
    def create_health_score(
        self,
        db: Session,
        asset_id: int,
        twin_deviation_score: float,
        anomaly_score: float,
        rul_days: Optional[float],
        failure_risk_score: float
    ) -> HealthScore:
        """Create and store a health score.
        
        Args:
            db: Database session
            asset_id: ID of the asset
            twin_deviation_score: Twin deviation score
            anomaly_score: Anomaly score
            rul_days: RUL in days
            failure_risk_score: Failure risk score
        
        Returns:
            Created HealthScore object
        """
        health_index = self.calculate_health_index(
            twin_deviation_score,
            anomaly_score,
            rul_days,
            failure_risk_score
        )
        
        health_score = HealthScore(
            asset_id=asset_id,
            timestamp=datetime.utcnow(),
            health_index=health_index,
            twin_deviation_score=round(twin_deviation_score, 2),
            anomaly_score=round(anomaly_score, 2),
            rul_days=round(rul_days, 2) if rul_days is not None else None,
            failure_risk_score=round(failure_risk_score, 2),
        )
        
        db.add(health_score)
        db.commit()
        db.refresh(health_score)
        
        return health_score


# Global health score engine instance
health_score_engine = HealthScoreEngine()

