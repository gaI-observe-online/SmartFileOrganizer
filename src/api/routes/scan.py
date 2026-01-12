"""Scan operation endpoints."""

import uuid
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

router = APIRouter()

# In-memory store for scan operations (in production, use database)
active_scans = {}


class ScanRequest(BaseModel):
    """Request model for starting a scan."""
    path: str
    recursive: bool = True
    auto_approve_threshold: int = 30


class ScanResponse(BaseModel):
    """Response model for scan operations."""
    scan_id: str
    status: str
    message: str


class ScanProgress(BaseModel):
    """Scan progress model."""
    scan_id: str
    status: str  # "running", "paused", "completed", "cancelled", "error"
    total_files: int
    processed_files: int
    current_file: Optional[str]
    progress_percent: float
    estimated_time_remaining: Optional[int]  # seconds


class ScanResult(BaseModel):
    """Scan result summary."""
    scan_id: str
    total_files: int
    categories: dict
    risk_summary: dict


@router.post("/scan/start", response_model=ScanResponse)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Start a new file scan operation.
    
    Args:
        request: Scan request parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Scan ID and status
    """
    scan_path = Path(request.path)
    
    if not scan_path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")
    
    if not scan_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.path}")
    
    # Generate scan ID
    scan_id = str(uuid.uuid4())
    
    # Initialize scan status
    active_scans[scan_id] = {
        "status": "running",
        "total_files": 0,
        "processed_files": 0,
        "current_file": None,
        "progress_percent": 0.0,
        "path": str(scan_path),
        "recursive": request.recursive,
    }
    
    # Start scan in background
    background_tasks.add_task(_run_scan, scan_id, scan_path, request.recursive, request.auto_approve_threshold)
    
    return ScanResponse(
        scan_id=scan_id,
        status="started",
        message=f"Scan started for {request.path}"
    )


async def _run_scan(scan_id: str, path: Path, recursive: bool, threshold: int):
    """Run the scan operation in background.
    
    Args:
        scan_id: Unique scan identifier
        path: Path to scan
        recursive: Whether to scan recursively
        threshold: Auto-approve threshold
    """
    from ...smartfile.core.config import Config
    from ...smartfile.core.database import Database
    from ...smartfile.audit.trail import AuditTrail
    from ...smartfile.analysis.scanner import Scanner
    from ...smartfile.analysis.extractor import ContentExtractor
    from ...smartfile.analysis.categorizer import Categorizer
    from ...smartfile.analysis.risk import RiskAssessor
    from ...smartfile.utils.redaction import SensitiveDataRedactor
    
    try:
        config = Config()
        config.set('preferences.auto_approve_threshold', threshold)
        
        organizer_dir = config.organizer_dir
        db = Database(organizer_dir / "audit.db")
        audit = AuditTrail(organizer_dir, db)
        redactor = SensitiveDataRedactor(config.get('privacy.redact_sensitive_in_logs', True))
        
        extractor = ContentExtractor()
        categorizer = Categorizer(config)
        risk_assessor = RiskAssessor(redactor)
        scanner = Scanner(config, extractor, categorizer, risk_assessor)
        
        # Scan directory
        files = scanner.scan_directory(path, recursive)
        
        # Update progress
        active_scans[scan_id]["total_files"] = len(files)
        active_scans[scan_id]["processed_files"] = len(files)
        active_scans[scan_id]["progress_percent"] = 100.0
        active_scans[scan_id]["status"] = "completed"
        active_scans[scan_id]["files"] = files
        
        db.close()
        
    except Exception as e:
        active_scans[scan_id]["status"] = "error"
        active_scans[scan_id]["error"] = str(e)


@router.get("/scan/{scan_id}", response_model=ScanProgress)
async def get_scan_progress(scan_id: str):
    """Get progress of a scan operation.
    
    Args:
        scan_id: Unique scan identifier
        
    Returns:
        Current scan progress
    """
    if scan_id not in active_scans:
        raise HTTPException(status_code=404, detail=f"Scan not found: {scan_id}")
    
    scan = active_scans[scan_id]
    
    return ScanProgress(
        scan_id=scan_id,
        status=scan["status"],
        total_files=scan["total_files"],
        processed_files=scan["processed_files"],
        current_file=scan.get("current_file"),
        progress_percent=scan["progress_percent"],
        estimated_time_remaining=None  # TODO: Calculate based on scan speed
    )


@router.post("/scan/{scan_id}/pause", response_model=ScanResponse)
async def pause_scan(scan_id: str):
    """Pause a running scan.
    
    Args:
        scan_id: Unique scan identifier
        
    Returns:
        Updated scan status
    """
    if scan_id not in active_scans:
        raise HTTPException(status_code=404, detail=f"Scan not found: {scan_id}")
    
    active_scans[scan_id]["status"] = "paused"
    
    return ScanResponse(
        scan_id=scan_id,
        status="paused",
        message="Scan paused"
    )


@router.post("/scan/{scan_id}/cancel", response_model=ScanResponse)
async def cancel_scan(scan_id: str):
    """Cancel a running scan.
    
    Args:
        scan_id: Unique scan identifier
        
    Returns:
        Updated scan status
    """
    if scan_id not in active_scans:
        raise HTTPException(status_code=404, detail=f"Scan not found: {scan_id}")
    
    active_scans[scan_id]["status"] = "cancelled"
    
    return ScanResponse(
        scan_id=scan_id,
        status="cancelled",
        message="Scan cancelled"
    )


class ScanListItem(BaseModel):
    """Item in scan list."""
    id: str
    timestamp: str
    path: str
    file_count: int


@router.get("/scans", response_model=List[ScanListItem])
async def list_scans(limit: int = 50):
    """List recent scan operations.
    
    Args:
        limit: Maximum number of scans to return
        
    Returns:
        List of recent scans
    """
    from ...smartfile.core.config import Config
    from ...smartfile.core.database import Database
    
    config = Config()
    organizer_dir = config.organizer_dir
    db = Database(organizer_dir / "audit.db")
    
    scans = db.get_recent_scans(limit)
    
    result = [
        ScanListItem(
            id=str(scan['id']),
            timestamp=scan['timestamp'],
            path=scan['path'],
            file_count=scan['file_count']
        )
        for scan in scans
    ]
    
    db.close()
    
    return result
