"""Script to initialize demo data for the application."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, init_db
from app.models import Asset
from app.services.data_simulator import simulator
from app.services.data_pipeline import DataPipeline
from app.services.digital_twin import digital_twin
from app.services.ml.anomaly_detection import anomaly_detection_service
from app.services.ml.rul_estimation import rul_estimation_service
from app.services.health_score import health_score_engine
from datetime import datetime, timedelta, timezone
import random


def create_demo_assets(db):
    """Create demo assets."""
    assets_data = [
        {"name": "Main Pump A", "asset_type": "pump", "location": "Refinery Unit 1"},
        {"name": "Main Pump B", "asset_type": "pump", "location": "Refinery Unit 1"},
        {"name": "Compressor X", "asset_type": "compressor", "location": "Refinery Unit 2"},
        {"name": "Compressor Y", "asset_type": "compressor", "location": "Refinery Unit 2"},
        {"name": "Heat Exchanger 1", "asset_type": "heat_exchanger", "location": "Refinery Unit 3"},
        {"name": "Heat Exchanger 2", "asset_type": "heat_exchanger", "location": "Refinery Unit 3"},
    ]
    
    assets = []
    for data in assets_data:
        # Check if asset already exists
        existing = db.query(Asset).filter(Asset.name == data["name"]).first()
        if existing:
            print(f"  Asset '{data['name']}' already exists, skipping creation")
            assets.append(existing)
        else:
            asset = Asset(**data)
            db.add(asset)
            assets.append(asset)
    
    db.commit()
    
    for asset in assets:
        db.refresh(asset)
    
    return assets


def generate_historical_data(db, assets, days=7):
    """Generate historical sensor data for the past N days."""
    print(f"Generating {days} days of historical data...")
    
    for asset in assets:
        print(f"  Generating data for {asset.name}...")
        
        # Generate readings every 5 minutes for the past N days
        from datetime import timezone
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(days=days)
        
        current_time = start_time
        readings_count = 0
        
        while current_time < now:
            # Generate reading
            reading_dict = simulator.generate_reading(
                asset.id,
                asset.asset_type,
                inject_anomaly=random.random() < 0.02,  # 2% chance of anomaly
                anomaly_severity=random.uniform(0.3, 0.8)
            )
            reading_dict["asset_id"] = asset.id
            reading_dict["timestamp"] = current_time.isoformat()
            
            # Process through pipeline
            stored, error = DataPipeline.process_reading(db, reading_dict)
            
            if stored:
                # Create twin state
                actual_reading = {
                    "temperature": stored.temperature,
                    "pressure": stored.pressure,
                    "vibration": stored.vibration,
                    "flow": stored.flow,
                    "rpm": stored.rpm,
                }
                twin_state = digital_twin.create_twin_state(db, asset.id, actual_reading)
                
                # Get recent readings for anomaly detection
                from app.models import SensorReading
                recent_readings = db.query(SensorReading).filter(
                    SensorReading.asset_id == asset.id
                ).order_by(SensorReading.timestamp.desc()).limit(50).all()
                
                recent_dicts = [
                    {
                        "temperature": r.temperature,
                        "pressure": r.pressure,
                        "vibration": r.vibration,
                        "flow": r.flow,
                        "rpm": r.rpm,
                    }
                    for r in recent_readings
                ]
                
                if len(recent_dicts) >= 3:
                    anomaly_result = anomaly_detection_service.detect_anomaly_multi_param(
                        recent_dicts, actual_reading
                    )
                    
                    # Get health scores for RUL
                    from app.models import HealthScore
                    health_scores = db.query(HealthScore).filter(
                        HealthScore.asset_id == asset.id
                    ).order_by(HealthScore.timestamp.asc()).all()
                    
                    health_scores_list = [h.health_index for h in health_scores]
                    health_timestamps = [h.timestamp for h in health_scores]
                    
                    rul_result = rul_estimation_service.estimate_rul(
                        asset.asset_type,
                        health_scores_list,
                        health_timestamps,
                        recent_dicts,
                        [r.timestamp for r in recent_readings]
                    )
                    
                    # Create health score
                    health_score_engine.create_health_score(
                        db,
                        asset.id,
                        twin_state.deviation_score or 0.0,
                        anomaly_result["anomaly_score"],
                        rul_result["rul_days"],
                        rul_result["risk_score"]
                    )
                
                readings_count += 1
            
            # Move to next interval (5 minutes)
            current_time += timedelta(minutes=5)
        
        print(f"    Generated {readings_count} readings for {asset.name}")
    
    print("Historical data generation complete!")


def main():
    """Main function to initialize demo data."""
    print("Initializing database...")
    init_db()
    
    db = SessionLocal()
    try:
        print("Creating demo assets...")
        assets = create_demo_assets(db)
        existing_count = len([a for a in assets if a.id])  # Assets that already existed
        new_count = len(assets) - existing_count
        if new_count > 0:
            print(f"Created {new_count} new assets")
        if existing_count > 0:
            print(f"Found {existing_count} existing assets")
        print(f"Total assets: {len(assets)}")
        
        print("\nGenerating historical data...")
        generate_historical_data(db, assets, days=7)
        
        print("\nDemo data initialization complete!")
        print(f"\nTotal assets: {len(assets)} with historical data")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

