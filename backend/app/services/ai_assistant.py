"""AI Assistant service using Groq LLM."""
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from app.config import settings
from app.models import Asset, SensorReading, HealthScore, Alert, Prediction
from app.schemas import AssetResponse, SensorReadingResponse, HealthScoreResponse

# Try to import Groq - handle different package versions
GROQ_AVAILABLE = False
Groq = None

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except (ImportError, AttributeError) as e:
    # If import fails, try to check if package exists but has different structure
    try:
        import groq
        # Check if Groq class exists in the module
        if hasattr(groq, 'Groq'):
            Groq = groq.Groq
            GROQ_AVAILABLE = True
        else:
            # Package might be installed but incompatible version
            print(f"Warning: Groq package found but 'Groq' class not available. Error: {e}")
            print("Please reinstall groq: pip install --upgrade groq")
            GROQ_AVAILABLE = False
    except ImportError:
        # Package not installed at all
        print("Warning: Groq package not found. Install with: pip install groq")
        GROQ_AVAILABLE = False


class AIAssistant:
    """AI Assistant using Groq LLM for answering questions about assets."""
    
    def __init__(self):
        """Initialize AI assistant with Groq client."""
        self.client = None
        if settings.groq_api_key and GROQ_AVAILABLE and Groq is not None:
            try:
                self.client = Groq(api_key=settings.groq_api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Groq client: {e}")
                self.client = None
        elif settings.groq_api_key and not GROQ_AVAILABLE:
            print("Warning: Groq package is not properly installed. Please run: pip install --upgrade groq")
    
    def get_asset_context(
        self,
        db: Session,
        asset_id: Optional[int] = None
    ) -> str:
        """Get context about assets for the LLM.
        
        Args:
            db: Database session
            asset_id: Optional asset ID to focus on
        
        Returns:
            Context string for LLM
        """
        context_parts = []
        
        if asset_id:
            asset = db.query(Asset).filter(Asset.id == asset_id).first()
            if asset:
                context_parts.append(f"Asset: {asset.name} (Type: {asset.asset_type}, Status: {asset.status})")
                
                # Latest reading
                latest_reading = db.query(SensorReading).filter(
                    SensorReading.asset_id == asset_id
                ).order_by(SensorReading.timestamp.desc()).first()
                
                if latest_reading:
                    context_parts.append(f"Latest sensor reading ({(datetime.now(timezone.utc) - latest_reading.timestamp).total_seconds() / 60:.1f} min ago):")
                    if latest_reading.temperature:
                        context_parts.append(f"  Temperature: {latest_reading.temperature}°C")
                    if latest_reading.pressure:
                        context_parts.append(f"  Pressure: {latest_reading.pressure} bar")
                    if latest_reading.vibration:
                        context_parts.append(f"  Vibration: {latest_reading.vibration} mm/s")
                    if latest_reading.flow:
                        context_parts.append(f"  Flow: {latest_reading.flow} L/min")
                    if latest_reading.rpm:
                        context_parts.append(f"  RPM: {latest_reading.rpm}")
                
                # Latest health score
                latest_health = db.query(HealthScore).filter(
                    HealthScore.asset_id == asset_id
                ).order_by(HealthScore.timestamp.desc()).first()
                
                if latest_health:
                    context_parts.append(f"Health Index: {latest_health.health_index:.1f}/100")
                    if latest_health.rul_days:
                        context_parts.append(f"Estimated RUL: {latest_health.rul_days:.1f} days")
                    if latest_health.failure_risk_score:
                        context_parts.append(f"Failure Risk Score: {latest_health.failure_risk_score:.1f}/100")
                
                # Active alerts
                active_alerts = db.query(Alert).filter(
                    Alert.asset_id == asset_id,
                    Alert.resolved == False
                ).order_by(Alert.timestamp.desc()).limit(5).all()
                
                if active_alerts:
                    context_parts.append("Active Alerts:")
                    for alert in active_alerts:
                        context_parts.append(f"  [{alert.severity.upper()}] {alert.message}")
        else:
            # All assets summary
            assets = db.query(Asset).all()
            context_parts.append(f"Total Assets: {len(assets)}")
            
            for asset in assets[:10]:  # Limit to first 10
                latest_health = db.query(HealthScore).filter(
                    HealthScore.asset_id == asset.id
                ).order_by(HealthScore.timestamp.desc()).first()
                
                health_str = f"{latest_health.health_index:.1f}" if latest_health else "N/A"
                context_parts.append(f"  {asset.name} ({asset.asset_type}): Health {health_str}/100")
        
        return "\n".join(context_parts)
    
    async def answer_question(
        self,
        db: Session,
        question: str,
        asset_id: Optional[int] = None,
        conversation_id: Optional[str] = None
    ) -> Dict:
        """Answer a question using Groq LLM.
        
        Args:
            db: Database session
            question: User's question
            asset_id: Optional asset ID to focus on
            conversation_id: Optional conversation ID for context
        
        Returns:
            Dictionary with response and conversation ID
        """
        if not self.client:
            return {
                "response": "AI Assistant is not configured. Please set GROQ_API_KEY in environment variables.",
                "conversation_id": conversation_id or "default",
            }
        
        # Get context
        context = self.get_asset_context(db, asset_id)
        
        # Build prompt
        system_prompt = """You are an AI assistant for a refinery predictive maintenance system. 
You help operators understand equipment health, sensor readings, anomalies, and maintenance predictions.
Be concise, technical, and helpful. Use the provided context to answer questions accurately."""
        
        user_prompt = f"""Context about the refinery equipment:
{context}

User Question: {question}

Please provide a helpful answer based on the context above."""
        
        # Available Groq models (as of 2024-2025):
        # - llama3-8b-8192
        # - llama3-70b-8192
        # - mixtral-8x7b-32768
        # - gemma-7b-it
        # Try models in order of preference, starting with configured model from .env
        configured_model = settings.groq_model
        models_to_try = [
            configured_model,  # Use configured model from .env first
            "llama3-70b-8192",  # Fallback: Closest replacement for llama-3.1-70b-versatile
            "mixtral-8x7b-32768",  # Fallback: Alternative high-quality model
            "llama3-8b-8192",  # Fallback: Faster, smaller model
        ]
        # Remove duplicates while preserving order
        models_to_try = list(dict.fromkeys(models_to_try))
        
        last_error = None
        for model in models_to_try:
            try:
                # Call Groq API
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=model,
                    temperature=0.7,
                    max_tokens=500,
                )
                
                response = chat_completion.choices[0].message.content
                
                return {
                    "response": response,
                    "conversation_id": conversation_id or f"conv_{datetime.now(timezone.utc).timestamp()}",
                }
                
            except Exception as e:
                last_error = e
                # If it's a model-specific error, try next model
                error_str = str(e)
                if "model" in error_str.lower() or "decommissioned" in error_str.lower():
                    continue  # Try next model
                else:
                    # Other error, return it
                    return {
                        "response": f"Error calling AI service: {str(e)}",
                        "conversation_id": conversation_id or "default",
                    }
        
        # All models failed
        return {
            "response": f"Error calling AI service: {str(last_error)}. Please check available models at https://console.groq.com/docs/models",
            "conversation_id": conversation_id or "default",
        }


# Global AI assistant instance
ai_assistant = AIAssistant()

