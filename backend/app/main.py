"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import assets, sensors, health, alerts, chat, websocket

# Initialize FastAPI app
app = FastAPI(
    title="RefinerySense API",
    description="Digital Twin + Predictive Maintenance System API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(assets.router)
app.include_router(sensors.router)
app.include_router(health.router)
app.include_router(alerts.router)
app.include_router(chat.router)
app.include_router(websocket.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    print("Database initialized")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "RefinerySense API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

