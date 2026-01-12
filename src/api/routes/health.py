"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
import os
import psutil
from pathlib import Path

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    database: str
    ai_provider: str
    disk_space_gb: float
    memory_usage_percent: float


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check endpoint.
    
    Returns:
        System health status including database, AI provider, and resources
    """
    from ...smartfile.core.config import Config
    from ...smartfile.core.database import Database
    
    config = Config()
    organizer_dir = config.organizer_dir
    
    # Check database
    db_path = organizer_dir / "audit.db"
    db_status = "connected" if db_path.exists() else "not_found"
    
    # Check AI provider (simplified - just check if Ollama endpoint is configured)
    ai_endpoint = config.get('ai.models.ollama.endpoint', 'http://localhost:11434')
    ai_status = "configured" if ai_endpoint else "not_configured"
    
    # Get disk space
    disk_usage = psutil.disk_usage('/')
    disk_space_gb = disk_usage.free / (1024 ** 3)
    
    # Get memory usage
    memory = psutil.virtual_memory()
    memory_usage_percent = memory.percent
    
    return HealthResponse(
        status="healthy",
        database=db_status,
        ai_provider=ai_status,
        disk_space_gb=round(disk_space_gb, 2),
        memory_usage_percent=memory_usage_percent
    )


class StatusResponse(BaseModel):
    """AI provider status response."""
    ai_connected: bool
    ai_endpoint: str
    ai_model: str
    database_path: str


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get AI provider and system status.
    
    Returns:
        Current status of AI provider and database
    """
    from ...smartfile.core.config import Config
    import requests
    
    config = Config()
    organizer_dir = config.organizer_dir
    
    ai_endpoint = config.get('ai.models.ollama.endpoint', 'http://localhost:11434')
    ai_model = config.get('ai.models.ollama.model', 'llama3.3')
    
    # Try to connect to Ollama
    ai_connected = False
    try:
        response = requests.get(f"{ai_endpoint}/api/tags", timeout=2)
        ai_connected = response.status_code == 200
    except Exception:
        pass
    
    return StatusResponse(
        ai_connected=ai_connected,
        ai_endpoint=ai_endpoint,
        ai_model=ai_model,
        database_path=str(organizer_dir / "audit.db")
    )
