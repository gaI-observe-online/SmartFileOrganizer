"""Utilities for redacting sensitive information."""

import re
from pathlib import Path
from typing import List, Tuple


class SensitiveDataRedactor:
    """Redact sensitive information from text."""
    
    # Minimum length for API key detection (configurable to reduce false positives)
    MIN_API_KEY_LENGTH = 40
    
    # Patterns for sensitive data detection
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
    API_KEY_PATTERN = None  # Will be set in __init__
    PASSWORD_PATTERN = re.compile(r'(?i)(password|passwd|pwd)[\s:=]+[^\s]+')
    
    def __init__(self, enabled: bool = True, min_api_key_length: int = 40):
        """Initialize redactor.
        
        Args:
            enabled: Whether redaction is enabled
            min_api_key_length: Minimum length for API key detection (default 40 to reduce false positives)
        """
        self.enabled = enabled
        self.min_api_key_length = min_api_key_length
        # Compile API key pattern with configurable length
        self.API_KEY_PATTERN = re.compile(rf'\b[A-Za-z0-9]{{{min_api_key_length},}}\b')
    
    def redact(self, text: str) -> str:
        """Redact sensitive information from text.
        
        Args:
            text: Input text
            
        Returns:
            Redacted text
        """
        if not self.enabled:
            return text
        
        # SSN: 123-45-6789 → ***-**-****
        text = self.SSN_PATTERN.sub('***-**-****', text)
        
        # Credit Card: 4111-1111-1111-1111 → ****-****-****-****
        text = self.CREDIT_CARD_PATTERN.sub('****-****-****-****', text)
        
        # Email: user@example.com → ****@example.com
        text = self.EMAIL_PATTERN.sub(self._redact_email, text)
        
        # Phone: 555-123-4567 → ***-***-****
        text = self.PHONE_PATTERN.sub('***-***-****', text)
        
        # API Keys (configurable length)
        text = self.API_KEY_PATTERN.sub('****', text)
        
        # Passwords: password: secret → password: ****
        text = self.PASSWORD_PATTERN.sub(r'\1: ****', text)
        
        # Username in paths: /Users/john/ → /Users/****/
        text = self._redact_usernames(text)
        
        return text
    
    def _redact_email(self, match: re.Match) -> str:
        """Redact email address, keeping domain.
        
        Args:
            match: Regex match object
            
        Returns:
            Redacted email
        """
        email = match.group(0)
        if '@' in email:
            _, domain = email.split('@', 1)
            return f"****@{domain}"
        return '****'
    
    def _redact_usernames(self, text: str) -> str:
        """Redact usernames in file paths.
        
        Args:
            text: Input text
            
        Returns:
            Text with redacted usernames
        """
        # /Users/username/ → /Users/****/
        text = re.sub(r'/Users/[^/]+/', '/Users/****/', text)
        
        # /home/username/ → /home/****/
        text = re.sub(r'/home/[^/]+/', '/home/****/', text)
        
        # C:\Users\username\ → C:\Users\***\
        text = re.sub(r'C:\\Users\\[^\\]+\\', r'C:\\Users\\****\\', text, flags=re.IGNORECASE)
        
        return text
    
    def detect_sensitive_content(self, text: str) -> List[Tuple[str, str]]:
        """Detect sensitive content in text.
        
        Args:
            text: Input text
            
        Returns:
            List of (type, matched_text) tuples
        """
        findings = []
        
        if self.SSN_PATTERN.search(text):
            findings.append(("SSN", "SSN pattern detected"))
        
        if self.CREDIT_CARD_PATTERN.search(text):
            findings.append(("CreditCard", "Credit card pattern detected"))
        
        if self.EMAIL_PATTERN.search(text):
            findings.append(("Email", "Email address detected"))
        
        if self.PHONE_PATTERN.search(text):
            findings.append(("Phone", "Phone number detected"))
        
        if self.API_KEY_PATTERN.search(text):
            findings.append(("APIKey", "Potential API key detected"))
        
        if self.PASSWORD_PATTERN.search(text):
            findings.append(("Password", "Password field detected"))
        
        return findings
    
    def redact_path(self, path: Path) -> str:
        """Redact sensitive information from file path.
        
        Args:
            path: File path
            
        Returns:
            Redacted path string
        """
        return self.redact(str(path))
