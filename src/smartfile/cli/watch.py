"""Watch folder mode for real-time file organization."""

import logging
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from ..core.config import Config
from ..core.database import Database
from ..audit.trail import AuditTrail
from ..analysis.scanner import Scanner
from ..analysis.extractor import ContentExtractor
from ..analysis.categorizer import Categorizer
from ..analysis.risk import RiskAssessor
from ..utils.redaction import SensitiveDataRedactor
from ..ai.ollama_provider import OllamaProvider
from ..core.organizer import Organizer


logger = logging.getLogger(__name__)


class FileEventHandler(FileSystemEventHandler):
    """Handle file system events."""
    
    def __init__(
        self,
        organizer: Organizer,
        base_dir: Path,
        mode: str = "batch",
        batch_interval: int = 300
    ):
        """Initialize event handler.
        
        Args:
            organizer: Organizer instance
            base_dir: Base directory for organization
            mode: "batch", "immediate", or "queue"
            batch_interval: Batch interval in seconds
        """
        super().__init__()
        self.organizer = organizer
        self.base_dir = base_dir
        self.mode = mode
        self.batch_interval = batch_interval
        self.pending_files = []
        self.last_process_time = datetime.now()
    
    def on_created(self, event):
        """Handle file creation event."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Skip hidden files and .organizer directory
        if file_path.name.startswith('.') or '.organizer' in file_path.parts:
            return
        
        logger.debug(f"File created: {file_path}")
        
        if self.mode == "immediate":
            self._process_file(file_path)
        else:
            # Add to pending queue
            self.pending_files.append(file_path)
            
            # Process batch if interval elapsed
            if self.mode == "batch":
                elapsed = (datetime.now() - self.last_process_time).total_seconds()
                if elapsed >= self.batch_interval:
                    self._process_batch()
    
    def _process_file(self, file_path: Path):
        """Process a single file immediately.
        
        Args:
            file_path: File to process
        """
        try:
            # Wait a bit for file to be fully written
            time.sleep(2)
            
            if not file_path.exists():
                return
            
            # Scan just this file
            scan_id, files = self.organizer.scan_directory(file_path.parent, recursive=False)
            
            # Filter to just this file
            files = [f for f in files if f.path == file_path]
            
            if not files:
                return
            
            # Generate and execute proposal
            proposal = self.organizer.generate_proposal(scan_id, files, self.base_dir)
            
            # Check risk
            file_info = files[0]
            threshold = self.organizer.config.get('preferences.auto_approve_threshold', 30)
            
            if file_info.risk_score <= threshold:
                # Auto-approve low risk
                self.organizer.audit_trail.log_approval(proposal.proposal_id, True)
                self.organizer.execute_proposal(proposal)
                logger.info(f"Auto-organized: {file_path}")
            else:
                # Queue for review
                logger.info(f"Queued for review (risk: {file_info.risk_score}): {file_path}")
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    def _process_batch(self):
        """Process batch of pending files."""
        if not self.pending_files:
            return
        
        logger.info(f"Processing batch of {len(self.pending_files)} files")
        
        try:
            # Get unique directories
            directories = set(f.parent for f in self.pending_files)
            
            for directory in directories:
                # Scan directory
                scan_id, files = self.organizer.scan_directory(directory, recursive=False)
                
                # Filter to pending files
                files = [f for f in files if f.path in self.pending_files]
                
                if not files:
                    continue
                
                # Generate proposal
                proposal = self.organizer.generate_proposal(scan_id, files, self.base_dir)
                
                # Separate by risk
                threshold = self.organizer.config.get('preferences.auto_approve_threshold', 30)
                low_risk = [(f, d) for f, d in proposal.files if f.risk_score <= threshold]
                high_risk = [(f, d) for f, d in proposal.files if f.risk_score > threshold]
                
                # Auto-approve low risk
                if low_risk:
                    from ..core.organizer import OrganizationProposal
                    auto_proposal = OrganizationProposal(
                        files=low_risk,
                        confidence=proposal.confidence,
                        reasoning="Auto-approved in watch mode"
                    )
                    auto_proposal.proposal_id = proposal.proposal_id
                    
                    self.organizer.audit_trail.log_approval(proposal.proposal_id, True)
                    self.organizer.execute_proposal(auto_proposal)
                    logger.info(f"Auto-organized {len(low_risk)} low-risk files")
                
                # Queue high risk
                if high_risk:
                    logger.info(f"Queued {len(high_risk)} high-risk files for review")
            
            # Clear pending
            self.pending_files.clear()
            self.last_process_time = datetime.now()
        
        except Exception as e:
            logger.error(f"Error processing batch: {e}")


class WatchManager:
    """Manager for watch folder mode."""
    
    def __init__(
        self,
        config: Config,
        organizer: Organizer
    ):
        """Initialize watch manager.
        
        Args:
            config: Configuration instance
            organizer: Organizer instance
        """
        self.config = config
        self.organizer = organizer
        self.observer: Optional[Observer] = None
    
    def watch(
        self,
        path: Path,
        mode: str = "batch",
        base_dir: Optional[Path] = None
    ):
        """Start watching a directory.
        
        Args:
            path: Directory to watch
            mode: "batch", "immediate", or "queue"
            base_dir: Base directory for organization
        """
        if not path.exists() or not path.is_dir():
            raise ValueError(f"Invalid directory: {path}")
        
        if base_dir is None:
            base_dir = path.parent / "Organized"
        
        # Get batch interval from config
        batch_interval = self.config.get('watch.batch_interval_seconds', 300)
        
        # Create event handler
        event_handler = FileEventHandler(
            self.organizer,
            base_dir,
            mode,
            batch_interval
        )
        
        # Create observer
        self.observer = Observer()
        self.observer.schedule(event_handler, str(path), recursive=True)
        
        # Start watching
        self.observer.start()
        logger.info(f"Watching directory: {path} (mode: {mode})")
        
        try:
            while True:
                time.sleep(1)
                
                # Process batch periodically
                if mode == "batch":
                    elapsed = (datetime.now() - event_handler.last_process_time).total_seconds()
                    if elapsed >= batch_interval and event_handler.pending_files:
                        event_handler._process_batch()
        
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop watching."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Stopped watching")
