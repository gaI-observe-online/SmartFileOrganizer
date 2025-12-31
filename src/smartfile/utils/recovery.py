"""State recovery and crash detection system.

This module provides functionality to:
- Detect interrupted scans
- Recover from crashes
- Reconstruct what happened during incidents
- Provide safe mode / recovery mode
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


logger = logging.getLogger(__name__)


class RecoveryState(Enum):
    """Recovery state."""
    
    NORMAL = "normal"  # Normal operation
    SAFE_MODE = "safe_mode"  # Safe mode (minimal functionality)
    RECOVERY = "recovery"  # Recovery mode (restoring state)


class ScanState:
    """State of a scan operation."""
    
    def __init__(
        self,
        scan_id: int,
        path: str,
        started_at: datetime,
        total_files: int = 0,
        processed_files: int = 0,
        completed: bool = False
    ):
        """Initialize scan state.
        
        Args:
            scan_id: Scan ID
            path: Path being scanned
            started_at: Start timestamp
            total_files: Total files to process
            processed_files: Files processed so far
            completed: Whether scan completed
        """
        self.scan_id = scan_id
        self.path = path
        self.started_at = started_at
        self.total_files = total_files
        self.processed_files = processed_files
        self.completed = completed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scan_id": self.scan_id,
            "path": self.path,
            "started_at": self.started_at.isoformat(),
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "completed": self.completed,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScanState':
        """Create from dictionary."""
        return cls(
            scan_id=data["scan_id"],
            path=data["path"],
            started_at=datetime.fromisoformat(data["started_at"]),
            total_files=data.get("total_files", 0),
            processed_files=data.get("processed_files", 0),
            completed=data.get("completed", False),
        )


class StateRecoveryManager:
    """Manage state recovery and crash detection."""
    
    def __init__(self, state_dir: Path):
        """Initialize state recovery manager.
        
        Args:
            state_dir: Directory for state files
        """
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_scan_file = state_dir / "current_scan.json"
        self.crash_log_file = state_dir / "crash.log"
        self.recovery_state_file = state_dir / "recovery_state.json"
        
        self.recovery_mode = RecoveryState.NORMAL
    
    def detect_crash(self) -> bool:
        """Detect if previous session crashed.
        
        Returns:
            True if crash detected
        """
        # Check if there's an incomplete scan
        if self.current_scan_file.exists():
            try:
                with open(self.current_scan_file, 'r') as f:
                    data = json.load(f)
                    scan_state = ScanState.from_dict(data)
                    
                    if not scan_state.completed:
                        logger.warning(
                            f"Detected incomplete scan #{scan_state.scan_id} "
                            f"({scan_state.processed_files}/{scan_state.total_files} files)"
                        )
                        return True
            
            except Exception as e:
                logger.error(f"Error checking for crash: {e}")
                return True
        
        return False
    
    def get_interrupted_scan(self) -> Optional[ScanState]:
        """Get interrupted scan state if any.
        
        Returns:
            ScanState if interrupted scan found, None otherwise
        """
        if not self.current_scan_file.exists():
            return None
        
        try:
            with open(self.current_scan_file, 'r') as f:
                data = json.load(f)
                scan_state = ScanState.from_dict(data)
                
                if not scan_state.completed:
                    return scan_state
        
        except Exception as e:
            logger.error(f"Error reading interrupted scan state: {e}")
        
        return None
    
    def start_scan(self, scan_id: int, path: str, total_files: int):
        """Record scan start.
        
        Args:
            scan_id: Scan ID
            path: Path being scanned
            total_files: Total files to process
        """
        scan_state = ScanState(
            scan_id=scan_id,
            path=path,
            started_at=datetime.now(),
            total_files=total_files,
            processed_files=0,
            completed=False
        )
        
        try:
            with open(self.current_scan_file, 'w') as f:
                json.dump(scan_state.to_dict(), f, indent=2)
            
            logger.debug(f"Recorded scan start: {scan_id}")
        
        except Exception as e:
            logger.error(f"Error recording scan start: {e}")
    
    def update_scan_progress(self, scan_id: int, processed_files: int):
        """Update scan progress.
        
        Args:
            scan_id: Scan ID
            processed_files: Number of files processed
        """
        if not self.current_scan_file.exists():
            return
        
        try:
            with open(self.current_scan_file, 'r') as f:
                data = json.load(f)
            
            data["processed_files"] = processed_files
            
            with open(self.current_scan_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error updating scan progress: {e}")
    
    def complete_scan(self, scan_id: int):
        """Mark scan as completed.
        
        Args:
            scan_id: Scan ID
        """
        try:
            if self.current_scan_file.exists():
                with open(self.current_scan_file, 'r') as f:
                    data = json.load(f)
                
                data["completed"] = True
                
                with open(self.current_scan_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                logger.debug(f"Marked scan {scan_id} as completed")
        
        except Exception as e:
            logger.error(f"Error completing scan: {e}")
    
    def clear_scan_state(self):
        """Clear current scan state."""
        try:
            if self.current_scan_file.exists():
                self.current_scan_file.unlink()
                logger.debug("Cleared scan state")
        
        except Exception as e:
            logger.error(f"Error clearing scan state: {e}")
    
    def record_crash(self, error: Exception):
        """Record crash information.
        
        Args:
            error: Exception that caused the crash
        """
        import traceback
        
        crash_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
        }
        
        # Add scan state if available
        scan_state = self.get_interrupted_scan()
        if scan_state:
            crash_info["interrupted_scan"] = scan_state.to_dict()
        
        try:
            with open(self.crash_log_file, 'a') as f:
                f.write(json.dumps(crash_info, indent=2) + "\n")
            
            logger.info(f"Recorded crash information to {self.crash_log_file}")
        
        except Exception as e:
            logger.error(f"Error recording crash: {e}")
    
    def get_crash_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent crash history.
        
        Args:
            limit: Maximum number of crashes to return
            
        Returns:
            List of crash information dictionaries
        """
        if not self.crash_log_file.exists():
            return []
        
        crashes = []
        
        try:
            with open(self.crash_log_file, 'r') as f:
                content = f.read()
                # Split by JSON object boundaries
                lines = content.strip().split('\n}\n')
                
                for line in lines:
                    if not line.strip():
                        continue
                    
                    # Re-add closing brace if it was split
                    if not line.strip().endswith('}'):
                        line = line + '}'
                    
                    try:
                        crash = json.loads(line)
                        crashes.append(crash)
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            logger.error(f"Error reading crash history: {e}")
        
        # Return most recent crashes
        return crashes[-limit:]
    
    def enter_safe_mode(self):
        """Enter safe mode."""
        self.recovery_mode = RecoveryState.SAFE_MODE
        
        state = {
            "mode": self.recovery_mode.value,
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            with open(self.recovery_state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info("Entered safe mode")
        
        except Exception as e:
            logger.error(f"Error entering safe mode: {e}")
    
    def exit_safe_mode(self):
        """Exit safe mode."""
        self.recovery_mode = RecoveryState.NORMAL
        
        try:
            if self.recovery_state_file.exists():
                self.recovery_state_file.unlink()
            
            logger.info("Exited safe mode")
        
        except Exception as e:
            logger.error(f"Error exiting safe mode: {e}")
    
    def is_safe_mode(self) -> bool:
        """Check if in safe mode.
        
        Returns:
            True if in safe mode
        """
        if self.recovery_state_file.exists():
            try:
                with open(self.recovery_state_file, 'r') as f:
                    state = json.load(f)
                    return state.get("mode") == RecoveryState.SAFE_MODE.value
            except Exception:
                pass
        
        return self.recovery_mode == RecoveryState.SAFE_MODE
    
    def reconstruct_incident(self, scan_state: ScanState) -> str:
        """Reconstruct what happened during an incident.
        
        Args:
            scan_state: Scan state to reconstruct
            
        Returns:
            Human-readable incident reconstruction
        """
        lines = [
            "📋 Incident Reconstruction",
            "=" * 50,
            "",
            f"Scan ID: {scan_state.scan_id}",
            f"Path: {scan_state.path}",
            f"Started: {scan_state.started_at}",
            f"Progress: {scan_state.processed_files}/{scan_state.total_files} files",
            "",
        ]
        
        # Calculate progress percentage
        if scan_state.total_files > 0:
            progress = (scan_state.processed_files / scan_state.total_files) * 100
            lines.append(f"Completion: {progress:.1f}%")
        
        # Check for recent crashes
        crashes = self.get_crash_history(limit=1)
        if crashes:
            crash = crashes[0]
            lines.extend([
                "",
                "Last Error:",
                f"  Type: {crash.get('error_type', 'Unknown')}",
                f"  Message: {crash.get('error_message', 'No message')}",
                f"  Time: {crash.get('timestamp', 'Unknown')}",
            ])
        
        lines.extend([
            "",
            "Recovery Options:",
            "  1. Resume scan from where it left off",
            "  2. Start a new scan",
            "  3. Enter safe mode for diagnostics",
        ])
        
        return "\n".join(lines)
