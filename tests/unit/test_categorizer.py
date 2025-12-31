"""Tests for file categorization."""

import pytest
from pathlib import Path
from datetime import datetime

from smartfile.core.config import Config
from smartfile.analysis.categorizer import Categorizer


@pytest.fixture
def categorizer(tmp_path):
    """Create categorizer instance."""
    config_path = tmp_path / "config.json"
    config = Config(config_path)
    return Categorizer(config)


def test_categorize_pdf_document(categorizer, tmp_path):
    """Test PDF categorization."""
    test_file = tmp_path / "report.pdf"
    test_file.touch()
    
    level1, _, _, _ = categorizer.categorize(test_file)
    
    assert level1 == "Documents"


def test_categorize_image(categorizer, tmp_path):
    """Test image categorization."""
    test_file = tmp_path / "photo.jpg"
    test_file.touch()
    
    level1, _, _, _ = categorizer.categorize(test_file)
    
    assert level1 == "Images"


def test_categorize_code(categorizer, tmp_path):
    """Test code file categorization."""
    test_file = tmp_path / "script.py"
    test_file.touch()
    
    level1, _, _, _ = categorizer.categorize(test_file)
    
    assert level1 == "Code"


def test_categorize_archive(categorizer, tmp_path):
    """Test archive categorization."""
    test_file = tmp_path / "backup.zip"
    test_file.touch()
    
    level1, _, _, _ = categorizer.categorize(test_file)
    
    assert level1 == "Archives"


def test_categorize_finance(categorizer, tmp_path):
    """Test finance document categorization."""
    test_file = tmp_path / "invoice_2024.xlsx"
    test_file.touch()
    
    content = "Invoice #12345"
    level1, _, _, _ = categorizer.categorize(test_file, content)
    
    assert level1 == "Finance"


def test_categorize_work_context(categorizer, tmp_path):
    """Test work context detection."""
    test_file = tmp_path / "work_report.pdf"
    test_file.touch()
    
    _, level2, _, _ = categorizer.categorize(test_file)
    
    assert level2 == "Work"


def test_categorize_time_based(categorizer, tmp_path):
    """Test time-based categorization."""
    test_file = tmp_path / "test.txt"
    test_file.touch()
    
    _, _, level3, _ = categorizer.categorize(test_file)
    
    # Should be current year
    current_year = datetime.now().strftime('%Y')
    assert level3 == current_year


def test_build_path(categorizer, tmp_path):
    """Test path building from categories."""
    base_dir = tmp_path
    
    path = categorizer.build_path(
        base_dir,
        level1="Documents",
        level2="Work",
        level3="2024",
        level4="ProjectX"
    )
    
    assert path == base_dir / "Documents" / "Work" / "ProjectX"


def test_build_path_no_general(categorizer, tmp_path):
    """Test path building skips 'General' context."""
    base_dir = tmp_path
    
    path = categorizer.build_path(
        base_dir,
        level1="Documents",
        level2="General",
        level3="",
        level4=""
    )
    
    assert path == base_dir / "Documents"
    assert "General" not in str(path)
