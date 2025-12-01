"""Configuration settings for the application."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "sqlite:///./refinery_sense.db"
    
    # Groq API
    groq_api_key: Optional[str] = None
    groq_model: str = "llama3-70b-8192"  # Default model, can be overridden
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Simulation
    simulation_enabled: bool = True
    simulation_interval_seconds: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

