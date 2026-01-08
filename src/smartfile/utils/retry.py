"""Retry and connection resilience utilities.

This module provides retry logic with exponential backoff for network operations,
offline mode detection, and connection state management.
"""

import logging
import time
import random
from typing import Callable, Optional, Any, TypeVar, List
from functools import wraps
from enum import Enum


logger = logging.getLogger(__name__)

T = TypeVar('T')


class ConnectionState(Enum):
    """Connection state."""
    
    ONLINE = "online"
    OFFLINE = "offline"
    RECONNECTING = "reconnecting"
    DEGRADED = "degraded"  # Partial connectivity


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        idempotent: bool = True
    ):
        """Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
            idempotent: Whether the operation is idempotent (safe to retry)
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.idempotent = idempotent


def calculate_backoff_delay(
    attempt: int,
    config: RetryConfig
) -> float:
    """Calculate delay for retry attempt with exponential backoff.
    
    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration
        
    Returns:
        Delay in seconds
    """
    delay = config.initial_delay * (config.exponential_base ** attempt)
    delay = min(delay, config.max_delay)
    
    # Add jitter if enabled
    if config.jitter:
        jitter_amount = delay * 0.1  # 10% jitter
        delay += random.uniform(-jitter_amount, jitter_amount)
    
    return max(0, delay)


def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable.
    
    Args:
        error: Exception to check
        
    Returns:
        True if error is retryable
    """
    # Import here to avoid circular dependency
    from .errors import OrganizerError, ErrorCategory
    
    # Check for network-related errors
    if isinstance(error, OrganizerError):
        return error.is_network_error()
    
    # Check for common retryable exceptions
    # Note: We check for built-in exceptions by name to avoid shadowing
    retryable_exception_names = (
        'ConnectionError',
        'TimeoutError',
        'OSError',
    )
    
    exception_name = type(error).__name__
    if exception_name in retryable_exception_names:
        return True
    
    # Check error message for retryable indicators
    error_str = str(error).lower()
    retryable_indicators = [
        "connection",
        "timeout",
        "network",
        "temporary",
        "unavailable",
    ]
    
    return any(indicator in error_str for indicator in retryable_indicators)


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
):
    """Decorator for retrying functions with exponential backoff.
    
    Only retries operations that are explicitly marked as idempotent
    to prevent duplicate side effects.
    
    Args:
        config: Retry configuration (uses defaults if None)
        on_retry: Callback called on retry (error, attempt, delay)
        
    Returns:
        Decorated function
        
    Example:
        @retry_with_backoff(RetryConfig(max_attempts=5, idempotent=True))
        def connect_to_service():
            # ... connection logic (read-only, safe to retry)
            pass
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None
            
            # If operation is not idempotent, only try once
            max_attempts = config.max_attempts if config.idempotent else 1
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                
                except Exception as e:
                    last_error = e
                    
                    # Check if error is retryable
                    if not is_retryable_error(e):
                        # Not retryable, raise immediately
                        raise
                    
                    # Check if we have more attempts
                    if attempt >= config.max_attempts - 1:
                        # Last attempt, raise
                        raise
                    
                    # Calculate delay
                    delay = calculate_backoff_delay(attempt, config)
                    
                    # Log retry
                    logger.warning(
                        f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    
                    # Call on_retry callback if provided
                    if on_retry:
                        on_retry(e, attempt, delay)
                    
                    # Wait before retry
                    time.sleep(delay)
            
            # Should not reach here, but just in case
            if last_error:
                raise last_error
            
            raise RuntimeError("Retry logic failed unexpectedly")
        
        return wrapper
    
    return decorator


class ConnectionMonitor:
    """Monitor connection state and handle reconnection."""
    
    def __init__(
        self,
        check_interval: float = 5.0,
        retry_config: Optional[RetryConfig] = None
    ):
        """Initialize connection monitor.
        
        Args:
            check_interval: Interval between connectivity checks in seconds
            retry_config: Retry configuration for reconnection
        """
        self.check_interval = check_interval
        self.retry_config = retry_config or RetryConfig()
        self.state = ConnectionState.ONLINE
        self.pending_operations: List[Callable] = []
    
    def check_connectivity(self, test_func: Callable[[], bool]) -> ConnectionState:
        """Check connectivity using provided test function.
        
        Args:
            test_func: Function that returns True if connected
            
        Returns:
            Current connection state
        """
        try:
            if test_func():
                if self.state != ConnectionState.ONLINE:
                    logger.info("Connection restored")
                    self.state = ConnectionState.ONLINE
                    self._process_pending_operations()
                return ConnectionState.ONLINE
            else:
                self._handle_offline()
                return ConnectionState.OFFLINE
        
        except Exception as e:
            logger.warning(f"Connectivity check failed: {e}")
            self._handle_offline()
            return ConnectionState.OFFLINE
    
    def _handle_offline(self):
        """Handle offline state."""
        if self.state == ConnectionState.ONLINE:
            logger.warning("Connection lost, entering offline mode")
            self.state = ConnectionState.OFFLINE
    
    def queue_operation(self, operation: Callable):
        """Queue operation to retry when online.
        
        Args:
            operation: Callable to execute when online
        """
        logger.debug("Queueing operation for retry when online")
        self.pending_operations.append(operation)
    
    def _process_pending_operations(self):
        """Process pending operations after reconnection."""
        if not self.pending_operations:
            return
        
        logger.info(f"Processing {len(self.pending_operations)} pending operations")
        
        failed_operations = []
        for operation in self.pending_operations:
            try:
                operation()
            except Exception as e:
                logger.error(f"Failed to process pending operation: {e}")
                failed_operations.append(operation)
        
        # Keep failed operations for retry
        self.pending_operations = failed_operations
        
        if failed_operations:
            logger.warning(f"{len(failed_operations)} operations still failed after retry")


def with_connection_check(
    monitor: ConnectionMonitor,
    queue_on_failure: bool = True
):
    """Decorator to check connection before executing function.
    
    Args:
        monitor: Connection monitor instance
        queue_on_failure: Whether to queue operation if offline
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            if monitor.state == ConnectionState.OFFLINE:
                if queue_on_failure:
                    # Queue operation for later
                    operation = lambda: func(*args, **kwargs)
                    monitor.queue_operation(operation)
                    logger.info("Operation queued (offline mode)")
                    return None
                else:
                    from .errors import ConnectionError
                    raise ConnectionError(
                        service="Unknown",
                        endpoint="N/A",
                        original_error=None
                    )
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
