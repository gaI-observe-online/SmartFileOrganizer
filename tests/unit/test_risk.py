"""Tests for risk assessment."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta

from smartfile.analysis.risk import RiskAssessor
from smartfile.utils.redaction import SensitiveDataRedactor


@pytest.fixture
def risk_assessor():
    """Create risk assessor instance."""
    redactor = SensitiveDataRedactor(enabled=True)
    return RiskAssessor(redactor)


def test_ssn_detection(risk_assessor, tmp_path):
    """Test SSN pattern detection."""
    test_file = tmp_path / "test.txt"
    test_file.touch()
    
    content = "SSN: 123-45-6789"
    score, reasons = risk_assessor.calculate_risk_score(test_file, content)
    
    assert score >= 40
    assert any("SSN" in r for r in reasons)


def test_credit_card_detection(risk_assessor, tmp_path):
    """Test credit card pattern detection."""
    test_file = tmp_path / "test.txt"
    test_file.touch()
    
    content = "Card: 4111-1111-1111-1111"
    score, reasons = risk_assessor.calculate_risk_score(test_file, content)
    
    assert score >= 40
    assert any("Credit" in r or "credit" in r for r in reasons)


def test_password_detection(risk_assessor, tmp_path):
    """Test password pattern detection."""
    test_file = tmp_path / "test.txt"
    test_file.touch()
    
    content = "password: secret123"
    score, reasons = risk_assessor.calculate_risk_score(test_file, content)
    
    assert score >= 50
    assert any("Password" in r or "password" in r for r in reasons)


def test_api_key_detection(risk_assessor, tmp_path):
    """Test API key pattern detection."""
    test_file = tmp_path / "test.txt"
    test_file.touch()
    
    content = "API_KEY=" + "x" * 40
    score, reasons = risk_assessor.calculate_risk_score(test_file, content)
    
    assert score >= 50


def test_large_file_detection(risk_assessor, tmp_path):
    """Test large file detection."""
    test_file = tmp_path / "large.bin"
    test_file.touch()
    
    # Simulate large file (>500MB)
    large_size = 600 * 1024 * 1024
    score, reasons = risk_assessor.calculate_risk_score(test_file, "", large_size)
    
    assert score >= 10
    assert any("Large file" in r or "large file" in r for r in reasons)


def test_system_file_detection(risk_assessor, tmp_path):
    """Test system file extension detection."""
    test_file = tmp_path / "system.dll"
    test_file.touch()
    
    score, reasons = risk_assessor.calculate_risk_score(test_file, "")
    
    assert score >= 30
    assert any("System file" in r or "system file" in r for r in reasons)


def test_risk_level_low(risk_assessor):
    """Test low risk level classification."""
    level = risk_assessor.get_risk_level(20)
    assert level == "low"


def test_risk_level_medium(risk_assessor):
    """Test medium risk level classification."""
    level = risk_assessor.get_risk_level(50)
    assert level == "medium"


def test_risk_level_high(risk_assessor):
    """Test high risk level classification."""
    level = risk_assessor.get_risk_level(80)
    assert level == "high"


def test_requires_approval_low(risk_assessor):
    """Test approval not required for low risk."""
    requires = risk_assessor.requires_approval(20, 30)
    assert not requires


def test_requires_approval_high(risk_assessor):
    """Test approval required for high risk."""
    requires = risk_assessor.requires_approval(50, 30)
    assert requires


def test_combined_risk_factors(risk_assessor, tmp_path):
    """Test multiple risk factors combine correctly."""
    test_file = tmp_path / "sensitive.dll"
    test_file.touch()
    
    content = "SSN: 123-45-6789\nPassword: secret123"
    score, reasons = risk_assessor.calculate_risk_score(test_file, content)
    
    # Should have SSN (40) + Password (50) + System file (30) = 100+
    assert score >= 90
    assert len(reasons) >= 3


def test_risk_score_capped_at_100(risk_assessor, tmp_path):
    """Test risk score is capped at 100."""
    test_file = tmp_path / "test.dll"
    test_file.touch()
    
    # Multiple high-risk factors
    content = "SSN: 123-45-6789\nPassword: secret\nCard: 4111-1111-1111-1111"
    score, _ = risk_assessor.calculate_risk_score(test_file, content)
    
    assert score <= 100
