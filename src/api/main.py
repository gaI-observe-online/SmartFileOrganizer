"""Main FastAPI application for SmartFileOrganizer web UI."""

import os
import logging
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .routes import health, scan, files, settings
from .websocket import router as websocket_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    web_build_dir = Path(__file__).parent.parent.parent / "web" / "dist"
    logger.info("SmartFileOrganizer API starting up...")
    logger.info(f"Web UI directory: {web_build_dir}")
    logger.info(f"Web UI built: {web_build_dir.exists()}")
    
    yield
    
    # Shutdown
    logger.info("SmartFileOrganizer API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="SmartFileOrganizer API",
    description="REST API for SmartFileOrganizer web interface",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "http://localhost:3000",  # For development
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(scan.router, prefix="/api", tags=["scan"])
app.include_router(files.router, prefix="/api", tags=["files"])
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(websocket_router, tags=["websocket"])

# Serve static files (built React app)
web_build_dir = Path(__file__).parent.parent.parent / "web" / "dist"
if web_build_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_build_dir / "static")), name="static")
    
    @app.get("/")
    async def serve_spa():
        """Serve the React SPA."""
        index_file = web_build_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Web UI not built. Run: cd src/web && npm run build")
    
    @app.get("/{full_path:path}")
    async def serve_spa_routes(full_path: str):
        """Serve React SPA for all routes (client-side routing)."""
        # Don't intercept API or WebSocket routes
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404)
        
        index_file = web_build_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Web UI not built")
