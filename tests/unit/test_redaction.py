"""Tests for sensitive data redaction."""

import pytest
from smartfile.utils.redaction import SensitiveDataRedactor


@pytest.fixture
def redactor():
    """Create redactor instance."""
    return SensitiveDataRedactor(enabled=True)


def test_ssn_redaction(redactor):
    """Test SSN redaction."""
    text = "My SSN is 123-45-6789"
    redacted = redactor.redact(text)
    
    assert "123-45-6789" not in redacted
    assert "***-**-****" in redacted


def test_credit_card_redaction(redactor):
    """Test credit card redaction."""
    text = "Card number: 4111-1111-1111-1111"
    redacted = redactor.redact(text)
    
    assert "4111-1111-1111-1111" not in redacted
    assert "****-****-****-****" in redacted


def test_email_redaction(redactor):
    """Test email redaction."""
    text = "Contact: user@example.com"
    redacted = redactor.redact(text)
    
    assert "user@example.com" not in redacted
    assert "****@example.com" in redacted


def test_phone_redaction(redactor):
    """Test phone number redaction."""
    text = "Call 555-123-4567"
    redacted = redactor.redact(text)
    
    assert "555-123-4567" not in redacted
    assert "***-***-****" in redacted


def test_password_redaction(redactor):
    """Test password field redaction."""
    text = "password: mysecret123"
    redacted = redactor.redact(text)
    
    assert "mysecret123" not in redacted
    assert "password: ****" in redacted.lower()


def test_username_in_path_redaction(redactor):
    """Test username redaction in paths."""
    text = "/Users/john/Documents/file.pdf"
    redacted = redactor.redact(text)
    
    assert "john" not in redacted
    assert "/Users/****/" in redacted


def test_windows_path_redaction(redactor):
    """Test Windows path redaction."""
    text = r"C:\Users\Alice\Documents\file.pdf"
    redacted = redactor.redact(text)
    
    assert "Alice" not in redacted
    assert r"C:\Users\****" in redacted


def test_multiple_patterns_redaction(redactor):
    """Test multiple patterns in one text."""
    text = "SSN: 123-45-6789, Email: user@test.com, Card: 4111-1111-1111-1111"
    redacted = redactor.redact(text)
    
    assert "123-45-6789" not in redacted
    assert "user@test.com" not in redacted
    assert "4111-1111-1111-1111" not in redacted


def test_detect_sensitive_content(redactor):
    """Test sensitive content detection."""
    text = "SSN: 123-45-6789\nEmail: user@test.com"
    findings = redactor.detect_sensitive_content(text)
    
    assert len(findings) >= 2
    types = [f[0] for f in findings]
    assert "SSN" in types
    assert "Email" in types


def test_redaction_disabled():
    """Test redaction can be disabled."""
    redactor = SensitiveDataRedactor(enabled=False)
    text = "SSN: 123-45-6789"
    redacted = redactor.redact(text)
    
    assert redacted == text


def test_api_key_redaction(redactor):
    """Test API key redaction."""
    text = "API_KEY=" + "a" * 40
    redacted = redactor.redact(text)
    
    assert "a" * 40 not in redacted
    assert "****" in redacted
