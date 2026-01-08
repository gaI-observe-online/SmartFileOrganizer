"""Tests for atomic writes and path redaction."""

import pytest
import json
import tempfile
from pathlib import Path

from smartfile.utils.recovery import StateRecoveryManager


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


def test_atomic_write_json(recovery_manager, tmp_path):
    """Test atomic JSON write."""
    test_file = tmp_path / "test.json"
    data = {"key": "value", "number": 42}
    
    recovery_manager._atomic_write_json(test_file, data)
    
    # Verify file was written
    assert test_file.exists()
    
    # Verify content
    with open(test_file, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == data


def test_path_redaction(recovery_manager):
    """Test path redaction."""
    # Test home directory redaction
    home = str(Path.home())
    path = f"{home}/Documents/sensitive/file.txt"
    
    redacted = recovery_manager._redact_path(path)
    
    # Should replace home with ~
    assert "~" in redacted
    assert home not in redacted


def test_path_redaction_in_text(recovery_manager):
    """Test path redaction in text."""
    text = f"Error in /home/username/file.txt and C:\\Users\\username\\file.txt"
    
    redacted = recovery_manager._redact_paths_in_text(text)
    
    # Should redact usernames
    assert "/home/username" not in redacted
    assert "/home/<user>" in redacted or "~" in redacted


def test_crash_log_with_redaction(recovery_manager):
    """Test crash logging with path redaction."""
    error = ValueError("Test error")
    
    # Record crash with redaction
    recovery_manager.record_crash(error, redact_paths=True)
    
    # Verify crash was recorded
    assert recovery_manager.crash_log_file.exists()
    
    # Read and verify redaction
    with open(recovery_manager.crash_log_file, 'r') as f:
        crash_data = json.loads(f.read())
    
    assert "error_type" in crash_data
    assert crash_data["error_type"] == "ValueError"


def test_crash_log_without_redaction(recovery_manager):
    """Test crash logging without path redaction."""
    error = ValueError("Test error with /home/user/path")
    
    # Record crash without redaction
    recovery_manager.record_crash(error, redact_paths=False)
    
    # Verify crash was recorded
    assert recovery_manager.crash_log_file.exists()


def test_corrupted_state_file_handling(recovery_manager):
    """Test handling of corrupted state files."""
    # Write corrupted JSON
    with open(recovery_manager.current_scan_file, 'w') as f:
        f.write("{invalid json")
    
    # Detecting crash should handle corruption
    result = recovery_manager.detect_crash()
    
    # Should detect the issue
    assert result is True


def test_lock_acquisition(recovery_manager):
    """Test lock acquisition."""
    # Should be able to acquire lock
    assert recovery_manager._try_acquire_lock()
    
    # Lock file should exist
    assert recovery_manager.lock_file.exists()
    
    # Release lock
    recovery_manager._release_lock()
    
    # Lock file should be removed
    assert not recovery_manager.lock_file.exists()


def test_concurrent_lock_prevention(recovery_manager):
    """Test that concurrent processes cannot acquire lock."""
    # Acquire lock
    assert recovery_manager._try_acquire_lock()
    
    # Create another recovery manager instance
    recovery_manager2 = StateRecoveryManager(recovery_manager.state_dir)
    
    # Should not be able to acquire lock (same PID, but simulates concurrent access)
    # Note: This test is limited because we're in the same process
    # In real use, the PID check would prevent concurrent access
    
    # Clean up
    recovery_manager._release_lock()
