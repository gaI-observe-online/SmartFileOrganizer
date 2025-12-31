"""FastAPI server for SmartFileOrganizer Web UI."""

import json
import logging
import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import uuid
from datetime import datetime

# Add src to path so we can import smartfile
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import SmartFileOrganizer components
from smartfile.core.config import Config
from smartfile.core.database import Database
from smartfile.audit.trail import AuditTrail
from smartfile.analysis.scanner import Scanner
from smartfile.analysis.extractor import ContentExtractor
from smartfile.analysis.categorizer import Categorizer
from smartfile.analysis.risk import RiskAssessor
from smartfile.utils.redaction import SensitiveDataRedactor
from smartfile.ai.ollama_provider import OllamaProvider
from smartfile.core.organizer import Organizer
from smartfile.core.rollback import RollbackManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SmartFileOrganizer",
    description="AI-Powered File Organization with Privacy First",
    version="2.0.0"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001", "http://127.0.0.1:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components (initialized on startup)
config: Optional[Config] = None
database: Optional[Database] = None
audit_trail: Optional[AuditTrail] = None
organizer: Optional[Organizer] = None
rollback_manager: Optional[RollbackManager] = None

# Pydantic models for API
class ScanRequest(BaseModel):
    root_path: str
    dry_run: bool = True
    recursive: bool = False

class PlanResponse(BaseModel):
    id: str
    root_path: str
    file_count: int
    reclaimable_mb: float
    risk_level: str
    status: str
    timestamp: str
    confidence: float


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    global config, database, audit_trail, organizer, rollback_manager
    
    logger.info("Starting SmartFileOrganizer API server...")
    
    # Initialize configuration
    config = Config()
    config.ensure_organizer_dir()
    
    # Initialize database
    organizer_dir = config.organizer_dir
    db_path = organizer_dir / "audit.db"
    database = Database(db_path)
    
    # Initialize audit trail
    audit_trail = AuditTrail(organizer_dir, database)
    
    # Initialize analysis components
    extractor = ContentExtractor()
    categorizer = Categorizer(config)
    redactor = SensitiveDataRedactor(config.get('privacy.redact_sensitive_in_logs', True))
    risk_assessor = RiskAssessor(redactor)
    scanner = Scanner(config, extractor, categorizer, risk_assessor)
    
    # Initialize AI provider
    ai_config = config.get('ai.models.ollama', {})
    ai_provider = OllamaProvider(
        endpoint=ai_config.get('endpoint', 'http://localhost:11434'),
        model=ai_config.get('model', 'llama3.3'),
        fallback_model=ai_config.get('fallback_model', 'qwen2.5'),
        timeout=ai_config.get('timeout', 30)
    )
    
    # Initialize organizer
    organizer = Organizer(config, database, audit_trail, scanner, categorizer, ai_provider)
    
    # Initialize rollback manager
    rollback_manager = RollbackManager(config, database, audit_trail)
    
    logger.info("SmartFileOrganizer API server started successfully")


# Serve static files
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"Serving static files from {static_dir}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI."""
    static_index = static_dir / "index.html"
    if static_index.exists():
        with open(static_index, 'r', encoding='utf-8') as f:
            return f.read()
    
    return HTMLResponse(
        content="""
        <html>
            <head><title>SmartFileOrganizer</title></head>
            <body>
                <h1>SmartFileOrganizer</h1>
                <p>Web UI not found. Please run install.sh to set up the web interface.</p>
                <p>API is available at <a href="/docs">/docs</a></p>
            </body>
        </html>
        """,
        status_code=200
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "ai_available": organizer.ai_provider.available if organizer and organizer.ai_provider else False
    }


@app.get("/api/plans")
async def get_plans() -> List[Dict]:
    """Get all organization plans."""
    try:
        # Get recent scans with their proposals
        cursor = database.conn.cursor()
        cursor.execute("""
            SELECT 
                p.id,
                p.scan_id,
                p.plan,
                p.confidence,
                p.timestamp,
                p.user_approved,
                p.rolled_back,
                s.path as root_path
            FROM proposals p
            JOIN scans s ON p.scan_id = s.id
            ORDER BY p.timestamp DESC
            LIMIT 100
        """)
        
        plans = []
        for row in cursor.fetchall():
            plan_data = json.loads(row['plan'])
            
            # Calculate metrics
            file_count = len(plan_data.get('files', []))
            total_size_mb = 0
            risk_scores = []
            
            for file in plan_data.get('files', []):
                # Estimate size (not stored in plan, use 0 for now)
                risk_scores.append(file.get('risk_score', 0))
            
            avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
            risk_level = "Low" if avg_risk < 30 else "Medium" if avg_risk < 70 else "High"
            
            # Determine status
            if row['rolled_back']:
                status = "rolled_back"
            elif row['user_approved']:
                # Check if executed (has moves)
                cursor.execute("SELECT COUNT(*) as count FROM moves WHERE proposal_id = ?", (row['id'],))
                move_count = cursor.fetchone()['count']
                status = "executed" if move_count > 0 else "approved"
            else:
                status = "pending"
            
            plans.append({
                "id": str(row['id']),
                "root_path": row['root_path'],
                "file_count": file_count,
                "reclaimable_mb": total_size_mb,  # Placeholder
                "risk_level": risk_level,
                "status": status,
                "timestamp": row['timestamp'],
                "confidence": row['confidence']
            })
        
        return plans
    
    except Exception as e:
        logger.error(f"Error getting plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/plans")
async def create_plan(request: ScanRequest) -> Dict:
    """Create an organization plan by scanning a directory."""
    try:
        start_time = datetime.now()
        root_path = Path(request.root_path).expanduser()
        
        if not root_path.exists():
            raise HTTPException(status_code=400, detail=f"Path does not exist: {request.root_path}")
        
        if not root_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.root_path}")
        
        # Scan directory with performance monitoring
        scan_id, files = organizer.scan_directory(root_path, request.recursive)
        scan_duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        if not files:
            return {
                "id": str(scan_id),
                "root_path": str(root_path),
                "file_count": 0,
                "reclaimable_mb": 0,
                "risk_level": "Low",
                "status": "empty",
                "message": "No files found to organize",
                "scan_duration_ms": scan_duration_ms
            }
        
        # Generate proposal with immutable plan artifact
        proposal = organizer.generate_proposal(scan_id, files, root_path)
        
        # Calculate metrics
        total_size = sum(f[0].size for f in proposal.files)
        risk_scores = [f[0].risk_score for f in proposal.files]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        risk_level = "Low" if avg_risk < 30 else "Medium" if avg_risk < 70 else "High"
        
        # Log performance metrics (observability)
        logger.info(f"Scan completed: {len(files)} files in {scan_duration_ms}ms")
        logger.info(f"Plan {proposal.proposal_id}: {len(files)} files, {total_size/(1024*1024):.2f}MB, risk={risk_level}")
        
        return {
            "id": str(proposal.proposal_id),
            "root_path": str(root_path),
            "file_count": len(files),
            "reclaimable_mb": round(total_size / (1024 * 1024), 2),
            "risk_level": risk_level,
            "status": "pending",
            "confidence": proposal.confidence,
            "scan_duration_ms": scan_duration_ms
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auto-scan")
async def auto_scan() -> Dict:
    """Auto-scan common folders (Downloads, Documents, Desktop)."""
    try:
        home = Path.home()
        common_folders = []
        
        # Detect OS and set common folders
        for folder_name in ["Downloads", "Documents", "Desktop", "Pictures"]:
            folder_path = home / folder_name
            if folder_path.exists() and folder_path.is_dir():
                common_folders.append(folder_path)
        
        if not common_folders:
            return {
                "scanned": 0,
                "plans_created": 0,
                "message": "No common folders found"
            }
        
        plans_created = 0
        for folder in common_folders:
            try:
                # Scan directory
                scan_id, files = organizer.scan_directory(folder, recursive=False)
                
                if files:
                    # Generate proposal
                    proposal = organizer.generate_proposal(scan_id, files, folder)
                    plans_created += 1
                    logger.info(f"Created plan for {folder}: {len(files)} files")
            
            except Exception as e:
                logger.error(f"Error scanning {folder}: {e}")
                continue
        
        return {
            "scanned": len(common_folders),
            "plans_created": plans_created,
            "message": f"Scanned {len(common_folders)} folders, created {plans_created} plans"
        }
    
    except Exception as e:
        logger.error(f"Error in auto-scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/plans/{plan_id}/approve")
async def approve_plan(plan_id: str) -> Dict:
    """Approve an organization plan."""
    try:
        proposal_id = int(plan_id)
        
        # Check if proposal exists
        proposal = database.get_proposal_by_id(proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
        
        # Update approval status
        database.update_proposal_approval(proposal_id, True)
        
        return {
            "id": plan_id,
            "status": "approved",
            "message": "Plan approved successfully"
        }
    
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    except Exception as e:
        logger.error(f"Error approving plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/plans/{plan_id}/execute")
async def execute_plan(plan_id: str) -> Dict:
    """Execute an organization plan."""
    try:
        proposal_id = int(plan_id)
        
        # Get proposal
        proposal_data = database.get_proposal_by_id(proposal_id)
        if not proposal_data:
            raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
        
        # Parse the plan
        plan_json = json.loads(proposal_data['plan'])
        
        # Reconstruct proposal object (simplified - just for execution)
        # In production, we'd need to reconstruct FileInfo objects
        # For now, we'll execute the moves directly
        
        files_moved = 0
        backup_dir = config.organizer_dir / "backups" / str(proposal_id)
        
        for file_data in plan_json.get('files', []):
            source = Path(file_data['source'])
            dest = Path(file_data['destination'])
            
            if not source.exists():
                logger.warning(f"Source file not found: {source}")
                continue
            
            try:
                # Create destination directory
                dest.parent.mkdir(parents=True, exist_ok=True)
                
                # Backup if enabled
                if config.get('backup.enabled', True):
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    # Use timestamp to avoid name collisions in backup
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    backup_filename = f"{source.stem}_{timestamp}{source.suffix}"
                    backup_path = backup_dir / backup_filename
                    shutil.copy2(str(source), str(backup_path))
                
                # Move file
                shutil.move(str(source), str(dest))
                
                # Log the move
                database.add_move(proposal_id, str(source), str(dest))
                files_moved += 1
            
            except Exception as e:
                logger.error(f"Error moving {source}: {e}")
                continue
        
        # Mark as approved if not already
        if not proposal_data['user_approved']:
            database.update_proposal_approval(proposal_id, True)
        
        return {
            "id": plan_id,
            "status": "executed",
            "files_moved": files_moved,
            "message": f"Successfully moved {files_moved} files"
        }
    
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    except Exception as e:
        logger.error(f"Error executing plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/plans/{plan_id}/rollback")
async def rollback_plan(plan_id: str) -> Dict:
    """Rollback an executed plan."""
    try:
        proposal_id = int(plan_id)
        
        # Execute rollback
        success, files_restored = rollback_manager.rollback_proposal(proposal_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Rollback failed")
        
        return {
            "id": plan_id,
            "status": "rolled_back",
            "files_restored": files_restored,
            "message": f"Successfully restored {files_restored} files"
        }
    
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    except Exception as e:
        logger.error(f"Error rolling back plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics")
async def get_metrics() -> Dict:
    """Get performance and usage metrics (observability)."""
    try:
        cursor = database.conn.cursor()
        
        # Get scan statistics
        cursor.execute("""
            SELECT COUNT(*) as total_scans,
                   AVG(file_count) as avg_files_per_scan
            FROM scans
        """)
        scan_stats = cursor.fetchone()
        
        # Get proposal statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_plans,
                SUM(CASE WHEN user_approved = 1 THEN 1 ELSE 0 END) as approved_plans,
                SUM(CASE WHEN rolled_back = 1 THEN 1 ELSE 0 END) as rolled_back_plans
            FROM proposals
        """)
        plan_stats = cursor.fetchone()
        
        # Get move statistics
        cursor.execute("""
            SELECT COUNT(*) as total_moves
            FROM moves
        """)
        move_stats = cursor.fetchone()
        
        return {
            "scans_total": scan_stats['total_scans'] or 0,
            "avg_files_per_scan": round(scan_stats['avg_files_per_scan'] or 0, 1),
            "plans_created": plan_stats['total_plans'] or 0,
            "plans_approved": plan_stats['approved_plans'] or 0,
            "plans_rolled_back": plan_stats['rolled_back_plans'] or 0,
            "files_organized_total": move_stats['total_moves'] or 0,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
