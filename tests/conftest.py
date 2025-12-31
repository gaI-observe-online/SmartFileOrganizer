"""Test configuration."""

import pytest


@pytest.fixture
def sample_files(tmp_path):
    """Create sample files for testing."""
    files = {
        'document': tmp_path / 'report.pdf',
        'image': tmp_path / 'photo.jpg',
        'code': tmp_path / 'script.py',
        'archive': tmp_path / 'backup.zip',
        'text': tmp_path / 'notes.txt'
    }
    
    for file_path in files.values():
        file_path.touch()
    
    return files
