"""Tests for retry and connection resilience."""

import pytest
import time
from unittest.mock import Mock, patch

from smartfile.utils.retry import (
    RetryConfig,
    calculate_backoff_delay,
    is_retryable_error,
    retry_with_backoff,
    ConnectionMonitor,
    ConnectionState,
)
from smartfile.utils.errors import OrganizerError, ErrorCategory


def test_retry_config_defaults():
    """Test RetryConfig default values."""
    config = RetryConfig()
    
    assert config.max_attempts == 3
    assert config.initial_delay == 1.0
    assert config.max_delay == 30.0
    assert config.exponential_base == 2.0
    assert config.jitter is True


def test_retry_config_custom():
    """Test RetryConfig with custom values."""
    config = RetryConfig(
        max_attempts=5,
        initial_delay=2.0,
        max_delay=60.0,
        exponential_base=3.0,
        jitter=False
    )
    
    assert config.max_attempts == 5
    assert config.initial_delay == 2.0
    assert config.max_delay == 60.0
    assert config.exponential_base == 3.0
    assert config.jitter is False


def test_calculate_backoff_delay():
    """Test exponential backoff calculation."""
    config = RetryConfig(initial_delay=1.0, exponential_base=2.0, max_delay=10.0, jitter=False)
    
    # First retry
    delay0 = calculate_backoff_delay(0, config)
    assert delay0 == 1.0
    
    # Second retry
    delay1 = calculate_backoff_delay(1, config)
    assert delay1 == 2.0
    
    # Third retry
    delay2 = calculate_backoff_delay(2, config)
    assert delay2 == 4.0
    
    # Should be capped at max_delay
    delay10 = calculate_backoff_delay(10, config)
    assert delay10 == 10.0


def test_calculate_backoff_delay_with_jitter():
    """Test backoff delay with jitter."""
    config = RetryConfig(initial_delay=1.0, jitter=True)
    
    # With jitter, delay should vary but be close to expected
    delays = [calculate_backoff_delay(0, config) for _ in range(10)]
    
    # All delays should be positive
    assert all(d > 0 for d in delays)
    
    # Should have some variation (not all the same)
    assert len(set(delays)) > 1


def test_is_retryable_error_organizer_error():
    """Test retryable error detection for OrganizerError."""
    from smartfile.utils.errors import ConnectionError
    
    # Network error should be retryable
    network_error = ConnectionError(
        service="Test",
        endpoint="localhost",
    )
    assert is_retryable_error(network_error)
    
    # Non-network error should not be retryable
    non_network_error = OrganizerError(
        message="Config error",
        category=ErrorCategory.CONFIGURATION,
        code="E004",
    )
    assert not is_retryable_error(non_network_error)


def test_is_retryable_error_standard_exceptions():
    """Test retryable error detection for standard exceptions."""
    # Connection errors should be retryable
    assert is_retryable_error(ConnectionError("Connection failed"))
    assert is_retryable_error(TimeoutError("Timeout"))
    assert is_retryable_error(OSError("Network error"))
    
    # Other errors should not be retryable
    assert not is_retryable_error(ValueError("Invalid value"))
    assert not is_retryable_error(TypeError("Type error"))


def test_retry_with_backoff_success_first_try():
    """Test retry decorator when function succeeds on first try."""
    mock_func = Mock(return_value="success")
    
    @retry_with_backoff(RetryConfig(max_attempts=3))
    def test_func():
        return mock_func()
    
    result = test_func()
    
    assert result == "success"
    assert mock_func.call_count == 1


def test_retry_with_backoff_success_after_retry():
    """Test retry decorator when function succeeds after retries."""
    call_count = 0
    
    def test_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Temporary failure")
        return "success"
    
    decorated = retry_with_backoff(RetryConfig(max_attempts=5, initial_delay=0.1))
    result = decorated(test_func)()
    
    assert result == "success"
    assert call_count == 3


def test_retry_with_backoff_max_attempts_exceeded():
    """Test retry decorator when max attempts exceeded."""
    @retry_with_backoff(RetryConfig(max_attempts=3, initial_delay=0.1))
    def test_func():
        raise ConnectionError("Persistent failure")
    
    with pytest.raises(ConnectionError):
        test_func()


def test_retry_with_backoff_non_retryable_error():
    """Test retry decorator with non-retryable error."""
    call_count = 0
    
    def test_func():
        nonlocal call_count
        call_count += 1
        raise ValueError("Not retryable")
    
    decorated = retry_with_backoff(RetryConfig(max_attempts=3))
    
    with pytest.raises(ValueError):
        decorated(test_func)()
    
    # Should only try once
    assert call_count == 1


def test_retry_with_backoff_callback():
    """Test retry decorator with callback."""
    callback_calls = []
    
    def on_retry(error, attempt, delay):
        callback_calls.append((error, attempt, delay))
    
    call_count = 0
    
    def test_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Temporary")
        return "success"
    
    decorated = retry_with_backoff(
        RetryConfig(max_attempts=5, initial_delay=0.1),
        on_retry=on_retry
    )
    decorated(test_func)()
    
    # Should have 2 retry callbacks (failures before success)
    assert len(callback_calls) == 2


def test_connection_monitor_initial_state():
    """Test ConnectionMonitor initial state."""
    monitor = ConnectionMonitor()
    
    assert monitor.state == ConnectionState.ONLINE
    assert len(monitor.pending_operations) == 0


def test_connection_monitor_check_connectivity_online():
    """Test connectivity check when online."""
    monitor = ConnectionMonitor()
    
    def test_online():
        return True
    
    state = monitor.check_connectivity(test_online)
    
    assert state == ConnectionState.ONLINE
    assert monitor.state == ConnectionState.ONLINE


def test_connection_monitor_check_connectivity_offline():
    """Test connectivity check when offline."""
    monitor = ConnectionMonitor()
    
    def test_offline():
        return False
    
    state = monitor.check_connectivity(test_offline)
    
    assert state == ConnectionState.OFFLINE
    assert monitor.state == ConnectionState.OFFLINE


def test_connection_monitor_reconnection():
    """Test reconnection detection."""
    monitor = ConnectionMonitor()
    
    # Go offline
    monitor.check_connectivity(lambda: False)
    assert monitor.state == ConnectionState.OFFLINE
    
    # Come back online
    monitor.check_connectivity(lambda: True)
    assert monitor.state == ConnectionState.ONLINE


def test_connection_monitor_queue_operation():
    """Test queuing operations when offline."""
    monitor = ConnectionMonitor()
    
    operation = Mock()
    monitor.queue_operation(operation)
    
    assert len(monitor.pending_operations) == 1
    assert not operation.called


def test_connection_monitor_process_pending_operations():
    """Test processing pending operations after reconnection."""
    monitor = ConnectionMonitor()
    
    # Queue some operations while offline
    monitor.state = ConnectionState.OFFLINE
    
    op1 = Mock()
    op2 = Mock()
    monitor.queue_operation(op1)
    monitor.queue_operation(op2)
    
    # Come back online
    monitor.check_connectivity(lambda: True)
    
    # Operations should be executed
    assert op1.called
    assert op2.called
    assert len(monitor.pending_operations) == 0


def test_connection_monitor_failed_pending_operations():
    """Test handling of failed pending operations."""
    monitor = ConnectionMonitor()
    
    monitor.state = ConnectionState.OFFLINE
    
    # Add operation that will fail
    failed_op = Mock(side_effect=Exception("Failed"))
    monitor.queue_operation(failed_op)
    
    # Come back online
    monitor.check_connectivity(lambda: True)
    
    # Failed operation should still be in queue
    assert len(monitor.pending_operations) == 1
