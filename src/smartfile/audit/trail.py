"""Audit trail system with multiple output formats."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .database import Database


class AuditTrail:
    """Multi-format audit trail manager."""
    
    def __init__(self, organizer_dir: Path, database: Database):
        """Initialize audit trail.
        
        Args:
            organizer_dir: .organizer directory path
            database: Database instance
        """
        self.organizer_dir = organizer_dir
        self.database = database
        
        # JSON Lines audit file
        self.jsonl_path = organizer_dir / "audit.jsonl"
        
        # Human-readable log file
        self.log_path = organizer_dir / "operations.log"
        
        # Setup logging
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup human-readable logger."""
        logger = logging.getLogger("smartfile.audit")
        logger.setLevel(logging.INFO)
        
        # File handler
        handler = logging.FileHandler(self.log_path)
        handler.setLevel(logging.INFO)
        
        # Format: [2025-12-31 10:00:00] ACTION: details
        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
        # Also log to console in debug mode
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def _write_jsonl(self, entry: Dict[str, Any]) -> None:
        """Write entry to JSON Lines file.
        
        Args:
            entry: Audit entry
        """
        with open(self.jsonl_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def log_scan(self, path: str, file_count: int) -> int:
        """Log scan operation.
        
        Args:
            path: Scanned path
            file_count: Number of files found
            
        Returns:
            Scan ID
        """
        timestamp = datetime.now().isoformat()
        
        # SQLite
        scan_id = self.database.add_scan(path, file_count)
        
        # JSON Lines
        self._write_jsonl({
            "timestamp": timestamp,
            "action": "scan",
            "path": path,
            "file_count": file_count,
            "scan_id": scan_id
        })
        
        # Human-readable log
        self.logger.info(f"SCAN: {path} → {file_count} files discovered")
        
        return scan_id
    
    def log_propose(self, scan_id: int, plan: str, confidence: float) -> int:
        """Log proposal generation.
        
        Args:
            scan_id: Associated scan ID
            plan: Organization plan (JSON string)
            confidence: AI confidence score
            
        Returns:
            Proposal ID
        """
        timestamp = datetime.now().isoformat()
        
        # SQLite
        proposal_id = self.database.add_proposal(scan_id, plan, confidence)
        
        # JSON Lines
        self._write_jsonl({
            "timestamp": timestamp,
            "action": "propose",
            "scan_id": scan_id,
            "proposal_id": proposal_id,
            "confidence": confidence
        })
        
        # Human-readable log
        self.logger.info(f"PROPOSE: AI generated plan (confidence: {confidence:.0%})")
        
        return proposal_id
    
    def log_approval(self, proposal_id: int, approved: bool) -> None:
        """Log user approval/rejection.
        
        Args:
            proposal_id: Proposal ID
            approved: Whether user approved
        """
        timestamp = datetime.now().isoformat()
        
        # SQLite
        self.database.update_proposal_approval(proposal_id, approved)
        
        # JSON Lines
        self._write_jsonl({
            "timestamp": timestamp,
            "action": "approval",
            "proposal_id": proposal_id,
            "approved": approved
        })
        
        # Human-readable log
        status = "APPROVED" if approved else "REJECTED"
        self.logger.info(f"{status}: Proposal {proposal_id}")
    
    def log_execute(self, proposal_id: int, files_moved: int, success: bool) -> None:
        """Log execution of proposal.
        
        Args:
            proposal_id: Proposal ID
            files_moved: Number of files moved
            success: Whether execution succeeded
        """
        timestamp = datetime.now().isoformat()
        
        # JSON Lines
        self._write_jsonl({
            "timestamp": timestamp,
            "action": "execute",
            "proposal_id": proposal_id,
            "files_moved": files_moved,
            "success": success
        })
        
        # Human-readable log
        if success:
            self.logger.info(f"EXECUTE: Moved {files_moved} files successfully")
        else:
            self.logger.error(f"EXECUTE: Failed to move files")
    
    def log_move(self, proposal_id: int, original_path: str, new_path: str) -> int:
        """Log individual file move.
        
        Args:
            proposal_id: Associated proposal ID
            original_path: Original file path
            new_path: New file path
            
        Returns:
            Move ID
        """
        # SQLite
        move_id = self.database.add_move(proposal_id, original_path, new_path)
        
        # Human-readable log (at debug level to avoid spam)
        logging.debug(f"MOVE: {original_path} → {new_path}")
        
        return move_id
    
    def log_rollback(self, proposal_id: int, files_restored: int) -> None:
        """Log rollback operation.
        
        Args:
            proposal_id: Proposal ID
            files_restored: Number of files restored
        """
        timestamp = datetime.now().isoformat()
        
        # SQLite
        self.database.mark_proposal_rolled_back(proposal_id)
        
        # JSON Lines
        self._write_jsonl({
            "timestamp": timestamp,
            "action": "rollback",
            "proposal_id": proposal_id,
            "files_restored": files_restored
        })
        
        # Human-readable log
        self.logger.info(f"ROLLBACK: Restored {files_restored} files from proposal {proposal_id}")
    
    def log_learning(self, file_type: str, target_folder: str, approved: bool) -> None:
        """Log learning data.
        
        Args:
            file_type: File type/pattern
            target_folder: Target folder
            approved: Whether user approved
        """
        # SQLite
        self.database.add_learning_data(file_type, target_folder, approved)
        
        # Debug log only
        logging.debug(f"LEARNING: {file_type} → {target_folder} (approved: {approved})")
