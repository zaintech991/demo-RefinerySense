"""Alerts system for threshold and ML-based alerts."""
from sqlalchemy.orm import Session
from typing import Dict, Optional, List
from datetime import datetime
from app.models import Alert, Asset, SensorReading, HealthScore
from app.schemas import AlertResponse


class AlertsService:
    """Service for generating and managing alerts."""
    
    def __init__(self):
        """Initialize alerts service with thresholds."""
        self.thresholds = {
            "pump": {
                "temperature": {"warning": 75.0, "critical": 85.0},
                "pressure": {"warning": 3.2, "critical": 3.8},
                "vibration": {"warning": 4.0, "critical": 6.0},
                "flow": {"warning": 100.0, "critical": 80.0},  # Low flow is bad
                "health_index": {"warning": 60.0, "critical": 40.0},
            },
            "compressor": {
                "temperature": {"warning": 100.0, "critical": 115.0},
                "pressure": {"warning": 10.0, "critical": 12.0},
                "vibration": {"warning": 5.5, "critical": 8.0},
                "flow": {"warning": 200.0, "critical": 150.0},
                "health_index": {"warning": 60.0, "critical": 40.0},
            },
            "heat_exchanger": {
                "temperature": {"warning": 110.0, "critical": 125.0},
                "pressure": {"warning": 5.5, "critical": 6.5},
                "vibration": {"warning": 3.0, "critical": 5.0},
                "flow": {"warning": 150.0, "critical": 120.0},
                "health_index": {"warning": 60.0, "critical": 40.0},
            },
        }
    
    def check_threshold_alerts(
        self,
        db: Session,
        asset_id: int,
        reading: Dict
    ) -> List[Alert]:
        """Check for threshold-based alerts.
        
        Args:
            db: Database session
            asset_id: ID of the asset
            reading: Current sensor reading
        
        Returns:
            List of created alerts
        """
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return []
        
        asset_type = asset.asset_type
        if asset_type not in self.thresholds:
            asset_type = "pump"
        
        thresholds = self.thresholds[asset_type]
        alerts = []
        
        # Check each parameter
        for param, limits in thresholds.items():
            if param == "health_index":
                continue  # Handled separately
            
            if param not in reading or reading[param] is None:
                continue
            
            value = reading[param]
            
            # For flow, low values are bad
            if param == "flow":
                if value <= limits["critical"]:
                    severity = "critical"
                    message = f"{param.capitalize()} critically low: {value} (threshold: {limits['critical']})"
                elif value <= limits["warning"]:
                    severity = "warning"
                    message = f"{param.capitalize()} low: {value} (threshold: {limits['warning']})"
                else:
                    continue
            else:
                # For others, high values are bad
                if value >= limits["critical"]:
                    severity = "critical"
                    message = f"{param.capitalize()} critically high: {value} (threshold: {limits['critical']})"
                elif value >= limits["warning"]:
                    severity = "warning"
                    message = f"{param.capitalize()} high: {value} (threshold: {limits['warning']})"
                else:
                    continue
            
            # Check if similar alert already exists (avoid duplicates)
            recent_alert = db.query(Alert).filter(
                Alert.asset_id == asset_id,
                Alert.alert_type == "threshold",
                Alert.message.like(f"%{param}%"),
                Alert.resolved == False
            ).first()
            
            if not recent_alert:
                alert = Alert(
                    asset_id=asset_id,
                    timestamp=datetime.utcnow(),
                    alert_type="threshold",
                    severity=severity,
                    message=message,
                    resolved=False,
                )
                db.add(alert)
                alerts.append(alert)
        
        if alerts:
            db.commit()
            for alert in alerts:
                db.refresh(alert)
        
        return alerts
    
    def check_health_alerts(
        self,
        db: Session,
        asset_id: int,
        health_index: float
    ) -> Optional[Alert]:
        """Check for health-based alerts.
        
        Args:
            db: Database session
            asset_id: ID of the asset
            health_index: Current health index
        
        Returns:
            Created alert or None
        """
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return None
        
        asset_type = asset.asset_type
        if asset_type not in self.thresholds:
            asset_type = "pump"
        
        limits = self.thresholds[asset_type]["health_index"]
        
        if health_index <= limits["critical"]:
            severity = "critical"
            message = f"Health index critically low: {health_index:.1f}"
        elif health_index <= limits["warning"]:
            severity = "warning"
            message = f"Health index low: {health_index:.1f}"
        else:
            return None
        
        # Check for existing alert
        recent_alert = db.query(Alert).filter(
            Alert.asset_id == asset_id,
            Alert.alert_type == "health",
            Alert.resolved == False
        ).first()
        
        if recent_alert:
            return None
        
        alert = Alert(
            asset_id=asset_id,
            timestamp=datetime.utcnow(),
            alert_type="health",
            severity=severity,
            message=message,
            resolved=False,
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        return alert
    
    def check_anomaly_alerts(
        self,
        db: Session,
        asset_id: int,
        anomaly_score: float
    ) -> Optional[Alert]:
        """Check for anomaly-based alerts.
        
        Args:
            db: Database session
            asset_id: ID of the asset
            anomaly_score: Current anomaly score
        
        Returns:
            Created alert or None
        """
        if anomaly_score < 70.0:
            return None
        
        severity = "critical" if anomaly_score >= 85.0 else "warning"
        message = f"Anomaly detected: score {anomaly_score:.1f}"
        
        # Check for existing alert
        recent_alert = db.query(Alert).filter(
            Alert.asset_id == asset_id,
            Alert.alert_type == "anomaly",
            Alert.resolved == False
        ).first()
        
        if recent_alert:
            return None
        
        alert = Alert(
            asset_id=asset_id,
            timestamp=datetime.utcnow(),
            alert_type="anomaly",
            severity=severity,
            message=message,
            resolved=False,
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        return alert
    
    def check_rul_alerts(
        self,
        db: Session,
        asset_id: int,
        rul_days: Optional[float]
    ) -> Optional[Alert]:
        """Check for RUL-based alerts.
        
        Args:
            db: Database session
            asset_id: ID of the asset
            rul_days: Remaining Useful Life in days
        
        Returns:
            Created alert or None
        """
        if rul_days is None:
            return None
        
        if rul_days <= 7:
            severity = "critical"
            message = f"Critical: Estimated RUL only {rul_days:.1f} days remaining"
        elif rul_days <= 30:
            severity = "warning"
            message = f"Warning: Estimated RUL {rul_days:.1f} days remaining"
        else:
            return None
        
        # Check for existing alert
        recent_alert = db.query(Alert).filter(
            Alert.asset_id == asset_id,
            Alert.alert_type == "rul",
            Alert.resolved == False
        ).first()
        
        if recent_alert:
            return None
        
        alert = Alert(
            asset_id=asset_id,
            timestamp=datetime.utcnow(),
            alert_type="rul",
            severity=severity,
            message=message,
            resolved=False,
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        return alert


# Global alerts service instance
alerts_service = AlertsService()

