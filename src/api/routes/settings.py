"""Settings endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class SettingsResponse(BaseModel):
    """Settings response model."""
    ai_endpoint: str
    ai_model: str
    database_path: str
    auto_approve_threshold: int
    port: int
    help_base_url: str


class SettingsUpdate(BaseModel):
    """Settings update model."""
    ai_endpoint: str | None = None
    ai_model: str | None = None
    auto_approve_threshold: int | None = None
    help_base_url: str | None = None


@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """Get current settings.
    
    Returns:
        Current system settings
    """
    from ...smartfile.core.config import Config
    import os
    
    config = Config()
    organizer_dir = config.organizer_dir
    
    return SettingsResponse(
        ai_endpoint=config.get('ai.models.ollama.endpoint', 'http://localhost:11434'),
        ai_model=config.get('ai.models.ollama.model', 'llama3.3'),
        database_path=str(organizer_dir / "audit.db"),
        auto_approve_threshold=config.get('preferences.auto_approve_threshold', 30),
        port=int(os.getenv('SMARTFILE_PORT', '8001')),
        help_base_url=os.getenv('SMARTFILE_HELP_BASE_URL', 'https://github.com/gaI-observe-online/SmartFileOrganizer/tree/main/docs')
    )


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(settings: SettingsUpdate):
    """Update settings.
    
    Args:
        settings: Settings to update
        
    Returns:
        Updated settings
    """
    from ...smartfile.core.config import Config
    
    config = Config()
    
    # Update settings
    if settings.ai_endpoint is not None:
        config.set('ai.models.ollama.endpoint', settings.ai_endpoint)
    
    if settings.ai_model is not None:
        config.set('ai.models.ollama.model', settings.ai_model)
    
    if settings.auto_approve_threshold is not None:
        config.set('preferences.auto_approve_threshold', settings.auto_approve_threshold)
    
    if settings.help_base_url is not None:
        # Store in environment or config
        import os
        os.environ['SMARTFILE_HELP_BASE_URL'] = settings.help_base_url
    
    # Return updated settings
    return await get_settings()


class DiagnosticsResponse(BaseModel):
    """Diagnostics export response."""
    success: bool
    file_path: str
    message: str


@router.post("/diagnostics/export", response_model=DiagnosticsResponse)
async def export_diagnostics():
    """Export diagnostic bundle.
    
    Returns:
        Path to exported diagnostics bundle
    """
    from ...smartfile.core.config import Config
    import tempfile
    import zipfile
    import shutil
    from datetime import datetime
    
    config = Config()
    organizer_dir = config.organizer_dir
    
    # Create temporary directory for diagnostics
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = Path(tempfile.gettempdir()) / f"smartfile_diagnostics_{timestamp}"
    temp_dir.mkdir(exist_ok=True)
    
    # Copy relevant files (redacted)
    try:
        # Copy config (if exists)
        if config.config_path.exists():
            shutil.copy(config.config_path, temp_dir / "config.json")
        
        # Copy logs (if they exist)
        log_file = organizer_dir / "operations.log"
        if log_file.exists():
            shutil.copy(log_file, temp_dir / "operations.log")
        
        # Create system info file
        import platform
        import psutil
        
        with open(temp_dir / "system_info.txt", "w") as f:
            f.write(f"Platform: {platform.platform()}\n")
            f.write(f"Python: {platform.python_version()}\n")
            f.write(f"CPU: {psutil.cpu_count()} cores\n")
            f.write(f"Memory: {psutil.virtual_memory().total / (1024**3):.2f} GB\n")
            f.write(f"Disk: {psutil.disk_usage('/').free / (1024**3):.2f} GB free\n")
        
        # Create ZIP file
        zip_path = temp_dir.parent / f"smartfile_diagnostics_{timestamp}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in temp_dir.rglob('*'):
                if file.is_file():
                    zipf.write(file, file.relative_to(temp_dir))
        
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        
        return DiagnosticsResponse(
            success=True,
            file_path=str(zip_path),
            message=f"Diagnostics exported to {zip_path}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export diagnostics: {str(e)}")
