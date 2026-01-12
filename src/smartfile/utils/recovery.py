"""State recovery and crash detection system.

This module provides functionality to:
- Detect interrupted scans
- Recover from crashes
- Reconstruct what happened during incidents
- Provide safe mode / recovery mode
"""

import json
import logging
import os
import tempfile
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
        self.lock_file = state_dir / "organizer.lock"
        
        self.recovery_mode = RecoveryState.NORMAL
    
    def _atomic_write_json(self, file_path: Path, data: Dict[str, Any]):
        """Write JSON atomically to prevent corruption.
        
        Uses write-to-temp-then-rename pattern for atomicity.
        
        Args:
            file_path: Target file path
            data: Data to write
        """
        try:
            # Write to temp file first
            temp_fd, temp_path = tempfile.mkstemp(
                dir=file_path.parent,
                prefix=f".{file_path.name}.",
                suffix=".tmp"
            )
            
            try:
                with os.fdopen(temp_fd, 'w') as f:
                    json.dump(data, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                
                # Atomic rename
                os.replace(temp_path, file_path)
                
            except Exception:
                # Clean up temp file on error
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
                raise
        
        except Exception as e:
            logger.error(f"Error writing {file_path} atomically: {e}")
            raise
    
    def _try_acquire_lock(self) -> bool:
        """Try to acquire process lock.
        
        Returns:
            True if lock acquired, False if another process has it
        """
        try:
            if self.lock_file.exists():
                # Check if the process is still running
                try:
                    with open(self.lock_file, 'r') as f:
                        pid = int(f.read().strip())
                    
                    # Try to check if process exists (Unix-like systems)
                    try:
                        os.kill(pid, 0)  # Signal 0 just checks existence
                        return False  # Process still running
                    except OSError:
                        # Process doesn't exist, remove stale lock
                        logger.warning(f"Removing stale lock file (PID {pid})")
                        self.lock_file.unlink()
                except (ValueError, IOError):
                    # Corrupted lock file, remove it
                    logger.warning("Removing corrupted lock file")
                    self.lock_file.unlink()
            
            # Create lock file with our PID
            with open(self.lock_file, 'w') as f:
                f.write(str(os.getpid()))
            
            return True
        
        except Exception as e:
            logger.error(f"Error acquiring lock: {e}")
            return False
    
    def _release_lock(self):
        """Release process lock."""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except Exception as e:
            logger.error(f"Error releasing lock: {e}")
    
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
            
            except json.JSONDecodeError as e:
                # Corrupted state file - archive it
                logger.error(f"State file corrupted: {e}")
                self._archive_corrupted_file(self.current_scan_file)
                return True
            
            except Exception as e:
                logger.error(f"Error checking for crash: {e}")
                return True
        
        return False
    
    def _archive_corrupted_file(self, file_path: Path):
        """Archive a corrupted state file.
        
        Args:
            file_path: Path to corrupted file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_path = file_path.with_suffix(f".corrupt.{timestamp}.json")
            file_path.rename(archive_path)
            logger.info(f"Archived corrupted file to {archive_path}")
        except Exception as e:
            logger.error(f"Failed to archive corrupted file: {e}")
    
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
            self._atomic_write_json(self.current_scan_file, scan_state.to_dict())
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
            
            self._atomic_write_json(self.current_scan_file, data)
        
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
                
                self._atomic_write_json(self.current_scan_file, data)
                
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
    
    def record_crash(self, error: Exception, redact_paths: bool = True):
        """Record crash information.
        
        Args:
            error: Exception that caused the crash
            redact_paths: Whether to redact sensitive paths
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
            scan_dict = scan_state.to_dict()
            # Redact path if requested
            if redact_paths:
                scan_dict["path"] = self._redact_path(scan_dict["path"])
            crash_info["interrupted_scan"] = scan_dict
        
        # Redact paths in traceback and error message if requested
        if redact_paths:
            crash_info["traceback"] = self._redact_paths_in_text(crash_info["traceback"])
            crash_info["error_message"] = self._redact_paths_in_text(crash_info["error_message"])
        
        try:
            # Write each crash as a separate JSON line (JSON Lines format)
            with open(self.crash_log_file, 'a') as f:
                f.write(json.dumps(crash_info) + "\n")
            
            logger.info(f"Recorded crash information to {self.crash_log_file}")
        
        except Exception as e:
            logger.error(f"Error recording crash: {e}")
    
    def _redact_path(self, path: str) -> str:
        """Redact sensitive parts of a path.
        
        Args:
            path: Path to redact
            
        Returns:
            Redacted path
        """
        from pathlib import Path
        try:
            p = Path(path)
            # Replace home directory with ~
            home = Path.home()
            if str(p).startswith(str(home)):
                return str(p).replace(str(home), "~", 1)
            # Replace username in path
            parts = p.parts
            if len(parts) > 2:
                # Keep first 2 and last 2 parts, hash the middle
                import hashlib
                middle = "/".join(parts[2:-2]) if len(parts) > 4 else "/".join(parts[2:-1])
                hashed = hashlib.sha256(middle.encode()).hexdigest()[:8]
                return f"{parts[0]}/{parts[1]}/...{hashed}.../{parts[-1]}"
            return path
        except Exception:
            return "<redacted>"
    
    def _redact_paths_in_text(self, text: str) -> str:
        """Redact paths in text content.
        
        Args:
            text: Text to redact
            
        Returns:
            Redacted text
        """
        import re
        from pathlib import Path
        
        try:
            home = str(Path.home())
            # Replace home directory references
            text = text.replace(home, "~")
            
            # Redact common path patterns (Unix and Windows)
            # /home/username/... or C:\Users\username\...
            text = re.sub(r'/home/[^/]+', '/home/<user>', text)
            text = re.sub(r'C:\\Users\\[^\\]+', r'C:\\Users\\<user>', text)
            text = re.sub(r'/Users/[^/]+', '/Users/<user>', text)
            
            return text
        except Exception:
            return text
    
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
            # Read JSON Lines format (one JSON object per line)
            with open(self.crash_log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        crash = json.loads(line)
                        crashes.append(crash)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse crash log line: {e}")
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
    
    def reconstruct_incident(self, scan_state: ScanState, redact_paths: bool = True) -> str:
        """Reconstruct what happened during an incident.
        
        Args:
            scan_state: Scan state to reconstruct
            redact_paths: Whether to redact sensitive paths (default: True)
            
        Returns:
            Human-readable incident reconstruction
        """
        # Redact path if requested (default)
        display_path = self._redact_path(scan_state.path) if redact_paths else scan_state.path
        
        lines = [
            "📋 Incident Reconstruction",
            "=" * 50,
            "",
            f"Scan ID: {scan_state.scan_id}",
            f"Path: {display_path}",
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
            error_msg = crash.get('error_message', 'No message')
            # Redact error message if requested
            if redact_paths:
                error_msg = self._redact_paths_in_text(error_msg)
            
            lines.extend([
                "",
                "Last Error:",
                f"  Type: {crash.get('error_type', 'Unknown')}",
                f"  Message: {error_msg}",
                f"  Time: {crash.get('timestamp', 'Unknown')}",
            ])
        
        lines.extend([
            "",
            "Recovery Options:",
            "  1. Resume scan from where it left off",
            "  2. Start a new scan",
            "  3. Enter safe mode for diagnostics",
        ])
        
        # Add note about full paths if redacted
        if redact_paths:
            lines.extend([
                "",
                "💡 Paths are redacted for privacy. Use --show-technical-details to see full paths.",
            ])
        
        return "\n".join(lines)
