"""WebSocket routes for real-time data streaming."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from starlette.websockets import WebSocketState
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asset, SensorReading
from app.services.data_simulator import simulator
from app.services.data_pipeline import DataPipeline
from app.services.digital_twin import digital_twin
from app.services.ml.anomaly_detection import anomaly_detection_service
from app.services.ml.rul_estimation import rul_estimation_service
from app.services.health_score import health_score_engine
from app.services.alerts import alerts_service
import json
import asyncio

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@router.websocket("/ws/sensors/{asset_id}")
async def websocket_sensor_stream(websocket: WebSocket, asset_id: int):
    """WebSocket endpoint for real-time sensor data streaming."""
    await manager.connect(websocket)
    
    try:
        # Get asset
        from app.database import SessionLocal
        db = SessionLocal()
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        
        if not asset:
            await websocket.send_json({"error": "Asset not found"})
            await manager.disconnect(websocket)
            return
        
        # Start streaming
        async for reading in simulator.stream_readings(
            asset_id=asset_id,
            asset_type=asset.asset_type,
            interval_seconds=3.0
        ):
            # Process reading through pipeline
            stored, error = DataPipeline.process_reading(db, reading)
            
            if stored:
                # Create twin state
                actual_reading = {
                    "temperature": stored.temperature,
                    "pressure": stored.pressure,
                    "vibration": stored.vibration,
                    "flow": stored.flow,
                    "rpm": stored.rpm,
                }
                twin_state = digital_twin.create_twin_state(db, asset_id, actual_reading)
                
                # Anomaly detection
                recent_readings = db.query(SensorReading).filter(
                    SensorReading.asset_id == asset_id
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
                
                anomaly_result = anomaly_detection_service.detect_anomaly_multi_param(
                    recent_dicts, actual_reading
                )
                
                # Simplified RUL (would need health history)
                rul_result = rul_estimation_service.estimate_rul(
                    asset.asset_type,
                    [],  # health_scores
                    [],  # health_timestamps
                    recent_dicts,
                    [r.timestamp for r in recent_readings]
                )
                
                # Health score
                health_score = health_score_engine.create_health_score(
                    db,
                    asset_id,
                    twin_state.deviation_score or 0.0,
                    anomaly_result["anomaly_score"],
                    rul_result["rul_days"],
                    rul_result["risk_score"]
                )
                
                # Check alerts
                alerts_service.check_threshold_alerts(db, asset_id, actual_reading)
                alerts_service.check_health_alerts(db, asset_id, health_score.health_index)
                alerts_service.check_anomaly_alerts(db, asset_id, anomaly_result["anomaly_score"])
                alerts_service.check_rul_alerts(db, asset_id, rul_result["rul_days"])
                
                # Send to client
                await websocket.send_json({
                    "type": "sensor_reading",
                    "data": {
                        "reading": {
                            "id": stored.id,
                            "asset_id": stored.asset_id,
                            "timestamp": stored.timestamp.isoformat(),
                            "temperature": stored.temperature,
                            "pressure": stored.pressure,
                            "vibration": stored.vibration,
                            "flow": stored.flow,
                            "rpm": stored.rpm,
                        },
                        "twin_state": {
                            "expected_temperature": twin_state.expected_temperature,
                            "expected_pressure": twin_state.expected_pressure,
                            "deviation_score": twin_state.deviation_score,
                        },
                        "health": {
                            "health_index": health_score.health_index,
                            "anomaly_score": anomaly_result["anomaly_score"],
                            "rul_days": health_score.rul_days,
                            "risk_score": health_score.failure_risk_score,
                        }
                    }
                })
            
            await asyncio.sleep(3.0)  # Stream interval
        
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        # Only send error if connection is still open
        try:
            # Check if websocket is still connected before sending
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json({"error": str(e)})
        except (Exception, AttributeError):
            # Connection already closed or state check failed, ignore
            pass
        finally:
            manager.disconnect(websocket)
    finally:
        db.close()

