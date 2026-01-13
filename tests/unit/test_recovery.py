"""Tests for state recovery system."""

import pytest
import json
from pathlib import Path
from datetime import datetime

from smartfile.utils.recovery import (
    RecoveryState,
    ScanState,
    StateRecoveryManager,
)


@pytest.fixture
def temp_state_dir(tmp_path):
    """Create temporary state directory."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    return state_dir


@pytest.fixture
def recovery_manager(temp_state_dir):
    """Create StateRecoveryManager instance."""
    return StateRecoveryManager(temp_state_dir)


def test_scan_state_creation():
    """Test ScanState creation."""
    now = datetime.now()
    state = ScanState(
        scan_id=1,
        path="/test/path",
        started_at=now,
        total_files=10,
        processed_files=5,
        completed=False,
    )
    
    assert state.scan_id == 1
    assert state.path == "/test/path"
    assert state.started_at == now
    assert state.total_files == 10
    assert state.processed_files == 5
    assert not state.completed


def test_scan_state_to_dict():
    """Test ScanState serialization."""
    now = datetime.now()
    state = ScanState(
        scan_id=1,
        path="/test/path",
        started_at=now,
        total_files=10,
        processed_files=5,
    )
    
    data = state.to_dict()
    
    assert data["scan_id"] == 1
    assert data["path"] == "/test/path"
    assert data["total_files"] == 10
    assert data["processed_files"] == 5
    assert "started_at" in data


def test_scan_state_from_dict():
    """Test ScanState deserialization."""
    now = datetime.now()
    data = {
        "scan_id": 1,
        "path": "/test/path",
        "started_at": now.isoformat(),
        "total_files": 10,
        "processed_files": 5,
        "completed": False,
    }
    
    state = ScanState.from_dict(data)
    
    assert state.scan_id == 1
    assert state.path == "/test/path"
    assert state.total_files == 10
    assert state.processed_files == 5
    assert not state.completed


def test_recovery_manager_initialization(recovery_manager):
    """Test StateRecoveryManager initialization."""
    assert recovery_manager.recovery_mode == RecoveryState.NORMAL
    assert recovery_manager.state_dir.exists()


def test_no_crash_detected_initially(recovery_manager):
    """Test no crash detected on first run."""
    assert not recovery_manager.detect_crash()


def test_detect_crash_with_incomplete_scan(recovery_manager):
    """Test crash detection with incomplete scan."""
    # Create incomplete scan state
    scan_state = ScanState(
        scan_id=1,
        path="/test/path",
        started_at=datetime.now(),
        total_files=10,
        processed_files=5,
        completed=False,
    )
    
    with open(recovery_manager.current_scan_file, 'w') as f:
        json.dump(scan_state.to_dict(), f)
    
    assert recovery_manager.detect_crash()


def test_no_crash_with_completed_scan(recovery_manager):
    """Test no crash detected with completed scan."""
    scan_state = ScanState(
        scan_id=1,
        path="/test/path",
        started_at=datetime.now(),
        total_files=10,
        processed_files=10,
        completed=True,
    )
    
    with open(recovery_manager.current_scan_file, 'w') as f:
        json.dump(scan_state.to_dict(), f)
    
    assert not recovery_manager.detect_crash()


def test_get_interrupted_scan(recovery_manager):
    """Test getting interrupted scan state."""
    scan_state = ScanState(
        scan_id=1,
        path="/test/path",
        started_at=datetime.now(),
        total_files=10,
        processed_files=5,
        completed=False,
    )
    
    with open(recovery_manager.current_scan_file, 'w') as f:
        json.dump(scan_state.to_dict(), f)
    
    interrupted = recovery_manager.get_interrupted_scan()
    
    assert interrupted is not None
    assert interrupted.scan_id == 1
    assert interrupted.processed_files == 5


def test_get_interrupted_scan_none_when_completed(recovery_manager):
    """Test get_interrupted_scan returns None for completed scans."""
    scan_state = ScanState(
        scan_id=1,
        path="/test/path",
        started_at=datetime.now(),
        total_files=10,
        processed_files=10,
        completed=True,
    )
    
    with open(recovery_manager.current_scan_file, 'w') as f:
        json.dump(scan_state.to_dict(), f)
    
    interrupted = recovery_manager.get_interrupted_scan()
    
    assert interrupted is None


def test_start_scan(recovery_manager):
    """Test starting a scan."""
    recovery_manager.start_scan(
        scan_id=1,
        path="/test/path",
        total_files=10
    )
    
    assert recovery_manager.current_scan_file.exists()
    
    with open(recovery_manager.current_scan_file, 'r') as f:
        data = json.load(f)
    
    assert data["scan_id"] == 1
    assert data["path"] == "/test/path"
    assert data["total_files"] == 10
    assert data["processed_files"] == 0
    assert not data["completed"]


def test_update_scan_progress(recovery_manager):
    """Test updating scan progress."""
    recovery_manager.start_scan(1, "/test/path", 10)
    
    recovery_manager.update_scan_progress(1, 5)
    
    with open(recovery_manager.current_scan_file, 'r') as f:
        data = json.load(f)
    
    assert data["processed_files"] == 5


def test_complete_scan(recovery_manager):
    """Test completing a scan."""
    recovery_manager.start_scan(1, "/test/path", 10)
    
    recovery_manager.complete_scan(1)
    
    with open(recovery_manager.current_scan_file, 'r') as f:
        data = json.load(f)
    
    assert data["completed"] is True


def test_clear_scan_state(recovery_manager):
    """Test clearing scan state."""
    recovery_manager.start_scan(1, "/test/path", 10)
    
    assert recovery_manager.current_scan_file.exists()
    
    recovery_manager.clear_scan_state()
    
    assert not recovery_manager.current_scan_file.exists()


def test_record_crash(recovery_manager):
    """Test recording crash information."""
    error = ValueError("Test error")
    
    recovery_manager.record_crash(error)
    
    assert recovery_manager.crash_log_file.exists()
    
    with open(recovery_manager.crash_log_file, 'r') as f:
        content = f.read()
    
    assert "ValueError" in content
    assert "Test error" in content


def test_record_crash_with_scan_state(recovery_manager):
    """Test recording crash with scan state."""
    recovery_manager.start_scan(1, "/test/path", 10)
    
    error = ValueError("Test error")
    recovery_manager.record_crash(error)
    
    crashes = recovery_manager.get_crash_history()
    
    assert len(crashes) > 0
    assert "interrupted_scan" in crashes[0]


def test_get_crash_history(recovery_manager):
    """Test getting crash history."""
    # Record multiple crashes
    for i in range(5):
        error = ValueError(f"Error {i}")
        recovery_manager.record_crash(error)
    
    history = recovery_manager.get_crash_history(limit=3)
    
    assert len(history) == 3
    # Should return most recent
    assert "Error 4" in history[-1]["error_message"]


def test_enter_safe_mode(recovery_manager):
    """Test entering safe mode."""
    recovery_manager.enter_safe_mode()
    
    assert recovery_manager.recovery_mode == RecoveryState.SAFE_MODE
    assert recovery_manager.recovery_state_file.exists()


def test_exit_safe_mode(recovery_manager):
    """Test exiting safe mode."""
    recovery_manager.enter_safe_mode()
    
    recovery_manager.exit_safe_mode()
    
    assert recovery_manager.recovery_mode == RecoveryState.NORMAL
    assert not recovery_manager.recovery_state_file.exists()


def test_is_safe_mode(recovery_manager):
    """Test checking if in safe mode."""
    assert not recovery_manager.is_safe_mode()
    
    recovery_manager.enter_safe_mode()
    
    assert recovery_manager.is_safe_mode()


def test_reconstruct_incident(recovery_manager):
    """Test incident reconstruction."""
    scan_state = ScanState(
        scan_id=1,
        path="/test/path",
        started_at=datetime.now(),
        total_files=20,
        processed_files=10,
        completed=False,
    )
    
    # Test with redaction (default)
    reconstruction = recovery_manager.reconstruct_incident(scan_state)
    
    assert "Scan ID: 1" in reconstruction
    assert "Path:" in reconstruction
    # Path should be redacted by default
    assert "Paths are redacted for privacy" in reconstruction
    assert "10/20" in reconstruction
    assert "50.0%" in reconstruction
    
    # Test without redaction
    reconstruction_no_redact = recovery_manager.reconstruct_incident(scan_state, redact_paths=False)
    
    assert "Scan ID: 1" in reconstruction_no_redact
    assert "/test/path" in reconstruction_no_redact
    # Should not have redaction notice
    assert "Paths are redacted for privacy" not in reconstruction_no_redact


def test_reconstruct_incident_with_crash(recovery_manager):
    """Test incident reconstruction with crash history."""
    scan_state = ScanState(
        scan_id=1,
        path="/test/path",
        started_at=datetime.now(),
        total_files=10,
        processed_files=5,
    )
    
    # Record a crash
    recovery_manager.record_crash(ValueError("Test crash"))
    
    reconstruction = recovery_manager.reconstruct_incident(scan_state)
    
    assert "Last Error" in reconstruction
    assert "ValueError" in reconstruction
    assert "Test crash" in reconstruction
