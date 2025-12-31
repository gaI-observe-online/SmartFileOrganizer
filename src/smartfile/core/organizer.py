"""Core organization engine."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..core.config import Config
from ..core.database import Database
from ..audit.trail import AuditTrail
from ..analysis.scanner import Scanner, FileInfo
from ..analysis.categorizer import Categorizer
from ..ai.ollama_provider import OllamaProvider
from ..ai.prompts import ORGANIZATION_SYSTEM_PROMPT, ORGANIZATION_USER_PROMPT


logger = logging.getLogger(__name__)


class OrganizationProposal:
    """Proposal for organizing files."""
    
    def __init__(
        self,
        files: List[Tuple[FileInfo, Path]],
        confidence: float = 0.0,
        reasoning: str = ""
    ):
        """Initialize proposal.
        
        Args:
            files: List of (FileInfo, destination_path) tuples
            confidence: Overall confidence (0-1)
            reasoning: AI reasoning for the proposal
        """
        self.files = files
        self.confidence = confidence
        self.reasoning = reasoning
        self.proposal_id: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "files": [
                {
                    "source": str(f[0].path),
                    "destination": str(f[1]),
                    "risk_score": f[0].risk_score,
                    "risk_level": f[0]._get_risk_level()
                }
                for f in self.files
            ],
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }


class Organizer:
    """Main file organization engine."""
    
    def __init__(
        self,
        config: Config,
        database: Database,
        audit_trail: AuditTrail,
        scanner: Scanner,
        categorizer: Categorizer,
        ai_provider: Optional[OllamaProvider] = None
    ):
        """Initialize organizer.
        
        Args:
            config: Configuration instance
            database: Database instance
            audit_trail: Audit trail instance
            scanner: Scanner instance
            categorizer: Categorizer instance
            ai_provider: Optional AI provider
        """
        self.config = config
        self.database = database
        self.audit_trail = audit_trail
        self.scanner = scanner
        self.categorizer = categorizer
        self.ai_provider = ai_provider
    
    def scan_directory(self, directory: Path, recursive: bool = False) -> Tuple[int, List[FileInfo]]:
        """Scan directory for files to organize.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan recursively
            
        Returns:
            Tuple of (scan_id, files)
        """
        files = self.scanner.scan(directory, recursive)
        scan_id = self.audit_trail.log_scan(str(directory), len(files))
        
        return scan_id, files
    
    def generate_proposal(
        self,
        scan_id: int,
        files: List[FileInfo],
        base_dir: Path
    ) -> OrganizationProposal:
        """Generate organization proposal.
        
        Args:
            scan_id: Scan ID
            files: List of FileInfo objects
            base_dir: Base directory for organization
            
        Returns:
            OrganizationProposal
        """
        # Try AI-based organization first
        if self.ai_provider and self.ai_provider.available:
            proposal = self._generate_ai_proposal(files, base_dir)
        else:
            # Fallback to rule-based organization
            logger.info("Using rule-based organization (AI not available)")
            proposal = self._generate_rule_based_proposal(files, base_dir)
        
        # Save proposal to database
        plan_json = json.dumps(proposal.to_dict())
        proposal_id = self.audit_trail.log_propose(scan_id, plan_json, proposal.confidence)
        proposal.proposal_id = proposal_id
        
        return proposal
    
    def _generate_ai_proposal(
        self,
        files: List[FileInfo],
        base_dir: Path
    ) -> OrganizationProposal:
        """Generate AI-based organization proposal.
        
        Args:
            files: List of FileInfo objects
            base_dir: Base directory
            
        Returns:
            OrganizationProposal
        """
        # Prepare file list for AI
        file_list = [f.to_dict() for f in files]
        
        # Get AI suggestions
        result = self.ai_provider.analyze_files(
            file_list,
            ORGANIZATION_SYSTEM_PROMPT,
            ORGANIZATION_USER_PROMPT
        )
        
        if not result:
            logger.warning("AI analysis failed, falling back to rule-based")
            return self._generate_rule_based_proposal(files, base_dir)
        
        # Parse AI suggestions and build proposal
        suggestions = result.get('suggestions', [])
        overall_confidence = result.get('overall_confidence', 50) / 100.0
        
        file_moves = []
        for i, file_info in enumerate(files):
            # Find matching suggestion
            suggestion = None
            for s in suggestions:
                if Path(s['file']).name == file_info.path.name:
                    suggestion = s
                    break
            
            if suggestion:
                dest_path = base_dir / suggestion['destination'] / file_info.path.name
            else:
                # Fallback to rule-based for this file
                dest_path = self._get_rule_based_destination(file_info, base_dir)
            
            file_moves.append((file_info, dest_path))
        
        return OrganizationProposal(
            files=file_moves,
            confidence=overall_confidence,
            reasoning="AI-generated organization plan"
        )
    
    def _generate_rule_based_proposal(
        self,
        files: List[FileInfo],
        base_dir: Path
    ) -> OrganizationProposal:
        """Generate rule-based organization proposal.
        
        Args:
            files: List of FileInfo objects
            base_dir: Base directory
            
        Returns:
            OrganizationProposal
        """
        file_moves = []
        
        for file_info in files:
            dest_path = self._get_rule_based_destination(file_info, base_dir)
            file_moves.append((file_info, dest_path))
        
        return OrganizationProposal(
            files=file_moves,
            confidence=0.75,
            reasoning="Rule-based organization"
        )
    
    def _get_rule_based_destination(self, file_info: FileInfo, base_dir: Path) -> Path:
        """Get rule-based destination for a file.
        
        Args:
            file_info: FileInfo object
            base_dir: Base directory
            
        Returns:
            Destination path
        """
        level1, level2, level3, level4 = file_info.categories
        dest_dir = self.categorizer.build_path(base_dir, level1, level2, level3, level4)
        return dest_dir / file_info.path.name
    
    def execute_proposal(
        self,
        proposal: OrganizationProposal,
        dry_run: bool = False
    ) -> Tuple[bool, int]:
        """Execute organization proposal.
        
        Args:
            proposal: OrganizationProposal to execute
            dry_run: If True, don't actually move files
            
        Returns:
            Tuple of (success, files_moved)
        """
        if dry_run:
            logger.info("DRY RUN: Would move %d files", len(proposal.files))
            return True, len(proposal.files)
        
        files_moved = 0
        backup_enabled = self.config.get('backup.enabled', True)
        backup_dir = self.config.organizer_dir / "backups" / str(proposal.proposal_id)
        
        try:
            for file_info, dest_path in proposal.files:
                source = file_info.path
                
                # Create destination directory
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Backup if enabled
                if backup_enabled:
                    self._backup_file(source, backup_dir, file_info.size)
                
                # Move file
                shutil.move(str(source), str(dest_path))
                
                # Log the move
                self.audit_trail.log_move(proposal.proposal_id, str(source), str(dest_path))
                
                files_moved += 1
                logger.debug(f"Moved: {source} → {dest_path}")
            
            # Log execution success
            self.audit_trail.log_execute(proposal.proposal_id, files_moved, True)
            
            return True, files_moved
        
        except Exception as e:
            logger.error(f"Error executing proposal: {e}")
            self.audit_trail.log_execute(proposal.proposal_id, files_moved, False)
            return False, files_moved
    
    def _backup_file(self, source: Path, backup_dir: Path, file_size: int) -> None:
        """Backup file before moving.
        
        Args:
            source: Source file path
            backup_dir: Backup directory
            file_size: File size in bytes
        """
        skip_large = self.config.get('backup.skip_large_files_mb', 500) * 1024 * 1024
        
        if file_size >= skip_large:
            # Metadata-only backup for large files
            logger.debug(f"Skipping physical backup for large file: {source}")
            return
        
        # Full physical backup
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / source.name
        
        shutil.copy2(str(source), str(backup_path))
        logger.debug(f"Backed up: {source} → {backup_path}")
