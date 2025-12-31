"""Rollback functionality for undoing operations."""

import logging
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from ..core.config import Config
from ..core.database import Database
from ..audit.trail import AuditTrail


logger = logging.getLogger(__name__)


class RollbackManager:
    """Manager for rolling back file operations."""
    
    def __init__(
        self,
        config: Config,
        database: Database,
        audit_trail: AuditTrail
    ):
        """Initialize rollback manager.
        
        Args:
            config: Configuration instance
            database: Database instance
            audit_trail: Audit trail instance
        """
        self.config = config
        self.database = database
        self.audit_trail = audit_trail
    
    def rollback_proposal(self, proposal_id: int) -> Tuple[bool, int]:
        """Rollback a specific proposal.
        
        Args:
            proposal_id: Proposal ID to rollback
            
        Returns:
            Tuple of (success, files_restored)
        """
        # Get proposal
        proposal = self.database.get_proposal_by_id(proposal_id)
        if not proposal:
            logger.error(f"Proposal {proposal_id} not found")
            return False, 0
        
        if proposal['rolled_back']:
            logger.error(f"Proposal {proposal_id} already rolled back")
            return False, 0
        
        # Get moves for this proposal
        moves = self.database.get_moves_by_proposal(proposal_id)
        if not moves:
            logger.warning(f"No moves found for proposal {proposal_id}")
            return True, 0
        
        # Restore files
        files_restored = 0
        backup_dir = self.config.organizer_dir / "backups" / str(proposal_id)
        
        for move in moves:
            original_path = Path(move['original_path'])
            new_path = Path(move['new_path'])
            
            try:
                # Check if file still exists at new location
                if new_path.exists():
                    # Create original directory
                    original_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Move back
                    shutil.move(str(new_path), str(original_path))
                    files_restored += 1
                    logger.debug(f"Restored: {new_path} → {original_path}")
                
                elif backup_dir.exists():
                    # Try to restore from backup
                    backup_file = backup_dir / original_path.name
                    if backup_file.exists():
                        original_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(backup_file), str(original_path))
                        files_restored += 1
                        logger.debug(f"Restored from backup: {original_path}")
                    else:
                        logger.warning(f"File not found for restore: {original_path}")
                else:
                    logger.warning(f"File not found for restore: {original_path}")
            
            except Exception as e:
                logger.error(f"Error restoring {original_path}: {e}")
                continue
        
        # Mark as rolled back
        self.database.mark_proposal_rolled_back(proposal_id)
        
        # Log rollback
        self.audit_trail.log_rollback(proposal_id, files_restored)
        
        return True, files_restored
    
    def rollback_last(self) -> Tuple[bool, int]:
        """Rollback the last operation.
        
        Returns:
            Tuple of (success, files_restored)
        """
        # Get last proposal
        cursor = self.database.conn.cursor()
        cursor.execute("""
            SELECT id FROM proposals
            WHERE rolled_back = 0 AND user_approved = 1
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if not row:
            logger.error("No operations to rollback")
            return False, 0
        
        proposal_id = row['id']
        return self.rollback_proposal(proposal_id)
    
    def get_rollback_history(self, limit: int = 100) -> List[dict]:
        """Get rollback history.
        
        Args:
            limit: Maximum number of records
            
        Returns:
            List of proposal records
        """
        cursor = self.database.conn.cursor()
        cursor.execute("""
            SELECT 
                p.id,
                p.timestamp,
                p.user_approved,
                p.rolled_back,
                COUNT(m.id) as file_count
            FROM proposals p
            LEFT JOIN moves m ON m.proposal_id = p.id
            WHERE p.user_approved = 1
            GROUP BY p.id
            ORDER BY p.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
