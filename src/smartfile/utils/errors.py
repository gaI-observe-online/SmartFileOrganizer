"""Error taxonomy and handling for SmartFileOrganizer.

This module provides a comprehensive error classification system with:
- User-actionable vs System errors
- Error codes with help article links
- Progressive disclosure of technical details
- Support for error recovery workflows

## Error Code Stability Policy

Error codes (E001-E006) are STABLE and IMMUTABLE once released:
- Once an error code is assigned, its meaning MUST NOT change
- New error semantics require new error codes (E007+)
- This ensures documentation links, support workflows, and telemetry remain consistent
- Error codes can be deprecated but never repurposed

To add a new error type:
1. Assign the next available code (E007, E008, etc.)
2. Create a new error class following the pattern
3. Document the code in docs/ERROR_HANDLING.md
4. Update this comment with the new code
"""

import logging
import traceback
import os
from enum import Enum
from typing import Optional, Dict, Any, List


logger = logging.getLogger(__name__)


# Configurable help base URL - can be overridden via environment variable
HELP_BASE_URL = os.getenv(
    'SMARTFILE_HELP_BASE_URL',
    'https://github.com/gaI-observe-online/SmartFileOrganizer/wiki'
)


class ErrorCategory(Enum):
    """Error categories for classification."""
    
    # User-actionable errors
    USER_INPUT = "user_input"  # Invalid user input
    PERMISSION = "permission"  # Permission denied
    NOT_FOUND = "not_found"  # Resource not found
    CONFIGURATION = "configuration"  # Configuration error
    
    # Network errors
    CONNECTION = "connection"  # Connection error
    TIMEOUT = "timeout"  # Request timeout
    OFFLINE = "offline"  # Offline/no network
    
    # System errors
    INTERNAL = "internal"  # Internal error
    DEPENDENCY = "dependency"  # External dependency error
    FILESYSTEM = "filesystem"  # File system error
    DATABASE = "database"  # Database error
    AI_PROVIDER = "ai_provider"  # AI provider error


class ErrorSeverity(Enum):
    """Error severity levels."""
    
    INFO = "info"  # Informational
    WARNING = "warning"  # Warning, operation can continue
    ERROR = "error"  # Error, operation failed
    CRITICAL = "critical"  # Critical error, system unstable


class OrganizerError(Exception):
    """Base exception for SmartFileOrganizer.
    
    Provides structured error information with:
    - Error code for lookup
    - User-friendly message
    - Technical details (optional)
    - Recovery suggestions
    - Help article links
    """
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        code: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        technical_details: Optional[str] = None,
        recovery_suggestions: Optional[List[str]] = None,
        help_url: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize organizer error.
        
        Args:
            message: User-friendly error message
            category: Error category
            code: Error code (e.g., "E001")
            severity: Error severity
            technical_details: Technical details (stack trace, etc.)
            recovery_suggestions: List of recovery suggestions
            help_url: URL to help article
            original_error: Original exception if wrapped
        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.code = code
        self.severity = severity
        self.technical_details = technical_details or ""
        self.recovery_suggestions = recovery_suggestions or []
        self.help_url = help_url
        self.original_error = original_error
    
    def is_user_actionable(self) -> bool:
        """Check if error is user-actionable."""
        return self.category in [
            ErrorCategory.USER_INPUT,
            ErrorCategory.PERMISSION,
            ErrorCategory.NOT_FOUND,
            ErrorCategory.CONFIGURATION,
        ]
    
    def is_network_error(self) -> bool:
        """Check if error is network-related."""
        return self.category in [
            ErrorCategory.CONNECTION,
            ErrorCategory.TIMEOUT,
            ErrorCategory.OFFLINE,
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            "code": self.code,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "user_actionable": self.is_user_actionable(),
            "network_error": self.is_network_error(),
            "technical_details": self.technical_details,
            "recovery_suggestions": self.recovery_suggestions,
            "help_url": self.help_url,
        }
    
    def get_error_details(self) -> str:
        """Get formatted error details for copying to support."""
        details = [
            f"Error Code: {self.code}",
            f"Category: {self.category.value}",
            f"Severity: {self.severity.value}",
            f"Message: {self.message}",
        ]
        
        if self.technical_details:
            details.append(f"\nTechnical Details:\n{self.technical_details}")
        
        if self.original_error:
            details.append(f"\nOriginal Error: {str(self.original_error)}")
            details.append(f"Original Type: {type(self.original_error).__name__}")
        
        return "\n".join(details)


# Specific error types

class ConnectionError(OrganizerError):
    """Error connecting to external service (AI provider, etc.)."""
    
    def __init__(
        self,
        service: str,
        endpoint: str,
        original_error: Optional[Exception] = None
    ):
        message = f"Unable to connect to {service}"
        technical_details = f"Endpoint: {endpoint}"
        
        if original_error:
            technical_details += f"\n{traceback.format_exc()}"
        
        super().__init__(
            message=message,
            category=ErrorCategory.CONNECTION,
            code="E001",
            severity=ErrorSeverity.ERROR,
            technical_details=technical_details,
            recovery_suggestions=[
                f"Check if {service} is running",
                f"Verify {service} is accessible at {endpoint}",
                "Check your network connection",
                "Try again in a few moments",
            ],
            help_url=f"{HELP_BASE_URL}/Connection-Errors" if HELP_BASE_URL else None,
            original_error=original_error
        )


class AIProviderError(OrganizerError):
    """Error from AI provider."""
    
    def __init__(
        self,
        provider: str,
        operation: str,
        original_error: Optional[Exception] = None
    ):
        message = f"AI provider ({provider}) failed during {operation}"
        technical_details = ""
        
        if original_error:
            technical_details = f"{traceback.format_exc()}"
        
        super().__init__(
            message=message,
            category=ErrorCategory.AI_PROVIDER,
            code="E002",
            severity=ErrorSeverity.WARNING,
            technical_details=technical_details,
            recovery_suggestions=[
                "The system will fall back to rule-based organization",
                f"Check if {provider} is running properly",
                f"Try pulling the required model",
                "Review the logs for more details",
            ],
            help_url=f"{HELP_BASE_URL}/AI-Provider-Errors" if HELP_BASE_URL else None,
            original_error=original_error
        )


class FileSystemError(OrganizerError):
    """File system error (permission denied, disk full, etc.)."""
    
    def __init__(
        self,
        operation: str,
        path: str,
        original_error: Optional[Exception] = None
    ):
        message = f"File system error during {operation}"
        technical_details = f"Path: {path}"
        
        if original_error:
            technical_details += f"\n{str(original_error)}\n{traceback.format_exc()}"
        
        recovery_suggestions = [
            "Check file/directory permissions",
            "Ensure sufficient disk space",
            "Verify the path is accessible",
        ]
        
        # Add specific suggestions based on error type
        if original_error and "Permission denied" in str(original_error):
            recovery_suggestions.insert(0, f"Grant read/write permissions for: {path}")
        
        super().__init__(
            message=message,
            category=ErrorCategory.FILESYSTEM,
            code="E003",
            severity=ErrorSeverity.ERROR,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            help_url=f"{HELP_BASE_URL}/Filesystem-Errors" if HELP_BASE_URL else None,
            original_error=original_error
        )


class ConfigurationError(OrganizerError):
    """Configuration error."""
    
    def __init__(
        self,
        config_key: str,
        issue: str,
        expected_value: Optional[str] = None
    ):
        message = f"Configuration error for '{config_key}': {issue}"
        technical_details = f"Config key: {config_key}\nIssue: {issue}"
        
        if expected_value:
            technical_details += f"\nExpected: {expected_value}"
        
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            code="E004",
            severity=ErrorSeverity.ERROR,
            technical_details=technical_details,
            recovery_suggestions=[
                f"Check the configuration for '{config_key}'",
                "Edit config with: python organize.py config --edit",
                "Refer to config.example.json for valid values",
            ],
            help_url=f"{HELP_BASE_URL}/Configuration" if HELP_BASE_URL else None,
            original_error=None
        )


class ScanInterruptedError(OrganizerError):
    """Scan was interrupted before completion."""
    
    def __init__(
        self,
        scan_id: int,
        files_processed: int,
        total_files: int
    ):
        message = f"Scan #{scan_id} was interrupted"
        technical_details = f"Processed {files_processed} of {total_files} files"
        
        super().__init__(
            message=message,
            category=ErrorCategory.INTERNAL,
            code="E005",
            severity=ErrorSeverity.WARNING,
            technical_details=technical_details,
            recovery_suggestions=[
                "You can resume the scan from where it left off",
                "Or start a new scan",
            ],
            help_url=f"{HELP_BASE_URL}/Recovery-Mode" if HELP_BASE_URL else None,
            original_error=None
        )


class DatabaseError(OrganizerError):
    """Database operation error."""
    
    def __init__(
        self,
        operation: str,
        original_error: Optional[Exception] = None
    ):
        message = f"Database error during {operation}"
        technical_details = ""
        
        if original_error:
            technical_details = f"{str(original_error)}\n{traceback.format_exc()}"
        
        super().__init__(
            message=message,
            category=ErrorCategory.DATABASE,
            code="E006",
            severity=ErrorSeverity.ERROR,
            technical_details=technical_details,
            recovery_suggestions=[
                "Check database file permissions",
                "Ensure database is not corrupted",
                "Try running with --safe-mode flag",
            ],
            help_url=f"{HELP_BASE_URL}/Database-Errors" if HELP_BASE_URL else None,
            original_error=original_error
        )


def format_error_for_display(error: OrganizerError, show_technical: bool = False) -> str:
    """Format error for console display.
    
    Args:
        error: OrganizerError to format
        show_technical: Whether to include technical details
        
    Returns:
        Formatted error string
    """
    lines = [
        f"❌ Error [{error.code}]: {error.message}",
        "",
    ]
    
    # Add recovery suggestions
    if error.recovery_suggestions:
        lines.append("💡 Suggested actions:")
        for suggestion in error.recovery_suggestions:
            lines.append(f"  • {suggestion}")
        lines.append("")
    
    # Add help URL or fallback message
    if error.help_url:
        lines.append(f"📖 More help: {error.help_url}")
    elif not HELP_BASE_URL:
        lines.append("📖 For help, run with --show-technical-details and report the issue")
    lines.append("")
    
    # Add technical details if requested
    if show_technical and error.technical_details:
        lines.append("🔧 Technical Details:")
        lines.append(error.technical_details)
        lines.append("")
    
    # Add note about copying details
    lines.append("💾 To copy error details for support, use: --copy-error-details")
    
    return "\n".join(lines)
