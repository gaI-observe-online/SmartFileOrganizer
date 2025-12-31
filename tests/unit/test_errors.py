"""Tests for error handling system."""

import pytest
from pathlib import Path

from smartfile.utils.errors import (
    OrganizerError,
    ErrorCategory,
    ErrorSeverity,
    ConnectionError,
    AIProviderError,
    FileSystemError,
    ConfigurationError,
    ScanInterruptedError,
    DatabaseError,
    format_error_for_display,
)


def test_organizer_error_basic():
    """Test basic OrganizerError creation."""
    error = OrganizerError(
        message="Test error",
        category=ErrorCategory.INTERNAL,
        code="E999",
        severity=ErrorSeverity.ERROR,
    )
    
    assert error.message == "Test error"
    assert error.category == ErrorCategory.INTERNAL
    assert error.code == "E999"
    assert error.severity == ErrorSeverity.ERROR
    assert not error.is_user_actionable()
    assert not error.is_network_error()


def test_organizer_error_user_actionable():
    """Test user-actionable error detection."""
    error = OrganizerError(
        message="Config error",
        category=ErrorCategory.CONFIGURATION,
        code="E004",
    )
    
    assert error.is_user_actionable()
    assert not error.is_network_error()


def test_organizer_error_network():
    """Test network error detection."""
    error = OrganizerError(
        message="Connection failed",
        category=ErrorCategory.CONNECTION,
        code="E001",
    )
    
    assert error.is_network_error()
    assert not error.is_user_actionable()


def test_organizer_error_to_dict():
    """Test error serialization."""
    error = OrganizerError(
        message="Test error",
        category=ErrorCategory.INTERNAL,
        code="E999",
        recovery_suggestions=["Try again", "Check logs"],
        help_url="https://example.com/help",
    )
    
    data = error.to_dict()
    
    assert data["code"] == "E999"
    assert data["message"] == "Test error"
    assert data["category"] == "internal"
    assert len(data["recovery_suggestions"]) == 2
    assert data["help_url"] == "https://example.com/help"


def test_connection_error():
    """Test ConnectionError."""
    error = ConnectionError(
        service="Ollama",
        endpoint="http://localhost:11434",
    )
    
    assert error.code == "E001"
    assert "Ollama" in error.message
    assert error.is_network_error()
    assert len(error.recovery_suggestions) > 0


def test_ai_provider_error():
    """Test AIProviderError."""
    error = AIProviderError(
        provider="Ollama",
        operation="generation",
    )
    
    assert error.code == "E002"
    assert "Ollama" in error.message
    assert "generation" in error.message
    assert error.severity == ErrorSeverity.WARNING
    assert "fall back" in error.recovery_suggestions[0].lower()


def test_filesystem_error():
    """Test FileSystemError."""
    error = FileSystemError(
        operation="move file",
        path="/test/path",
    )
    
    assert error.code == "E003"
    assert "move file" in error.message
    assert "/test/path" in error.technical_details
    assert len(error.recovery_suggestions) > 0


def test_configuration_error():
    """Test ConfigurationError."""
    error = ConfigurationError(
        config_key="ai.model",
        issue="missing required value",
        expected_value="llama3.3",
    )
    
    assert error.code == "E004"
    assert "ai.model" in error.message
    assert "llama3.3" in error.technical_details
    assert error.is_user_actionable()


def test_scan_interrupted_error():
    """Test ScanInterruptedError."""
    error = ScanInterruptedError(
        scan_id=42,
        files_processed=10,
        total_files=20,
    )
    
    assert error.code == "E005"
    assert "42" in error.message
    assert "10" in error.technical_details
    assert "20" in error.technical_details


def test_database_error():
    """Test DatabaseError."""
    error = DatabaseError(
        operation="insert record",
    )
    
    assert error.code == "E006"
    assert "insert record" in error.message
    assert error.severity == ErrorSeverity.ERROR


def test_format_error_for_display_simple():
    """Test error formatting without technical details."""
    error = OrganizerError(
        message="Test error",
        category=ErrorCategory.INTERNAL,
        code="E999",
        technical_details="Some technical details",
        recovery_suggestions=["Try this", "Or that"],
        help_url="https://example.com/help",
    )
    
    output = format_error_for_display(error, show_technical=False)
    
    assert "E999" in output
    assert "Test error" in output
    assert "Try this" in output
    assert "https://example.com/help" in output
    assert "Some technical details" not in output  # Should not show technical


def test_format_error_for_display_with_technical():
    """Test error formatting with technical details."""
    error = OrganizerError(
        message="Test error",
        category=ErrorCategory.INTERNAL,
        code="E999",
        technical_details="Stack trace here",
    )
    
    output = format_error_for_display(error, show_technical=True)
    
    assert "Stack trace here" in output


def test_error_with_original_exception():
    """Test error wrapping original exception."""
    original = ValueError("Original error")
    
    error = OrganizerError(
        message="Wrapped error",
        category=ErrorCategory.INTERNAL,
        code="E999",
        original_error=original,
    )
    
    details = error.get_error_details()
    
    assert "Original error" in details
    assert "ValueError" in details


def test_error_details_format():
    """Test get_error_details formatting."""
    error = OrganizerError(
        message="Test error",
        category=ErrorCategory.CONFIGURATION,
        code="E004",
        severity=ErrorSeverity.ERROR,
        technical_details="Some tech details",
    )
    
    details = error.get_error_details()
    
    assert "Error Code: E004" in details
    assert "Category: configuration" in details
    assert "Severity: error" in details
    assert "Message: Test error" in details
    assert "Some tech details" in details
