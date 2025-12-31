"""Tests for configuration management."""

import pytest
import json
from pathlib import Path

from smartfile.core.config import Config


def test_default_config_creation(tmp_path):
    """Test default config is created if not exists."""
    config_path = tmp_path / "config.json"
    config = Config(config_path)
    
    assert config_path.exists()
    assert config.get('version') == '1.0.0'


def test_config_get_nested(tmp_path):
    """Test getting nested config values."""
    config_path = tmp_path / "config.json"
    config = Config(config_path)
    
    value = config.get('ai.models.ollama.model')
    assert value == 'llama3.3'


def test_config_get_with_default(tmp_path):
    """Test getting config with default value."""
    config_path = tmp_path / "config.json"
    config = Config(config_path)
    
    value = config.get('nonexistent.key', 'default')
    assert value == 'default'


def test_config_set_value(tmp_path):
    """Test setting config values."""
    config_path = tmp_path / "config.json"
    config = Config(config_path)
    
    config.set('test.key', 'test_value')
    
    assert config.get('test.key') == 'test_value'
    
    # Verify it was saved
    with open(config_path) as f:
        data = json.load(f)
    assert data['test']['key'] == 'test_value'


def test_config_set_nested(tmp_path):
    """Test setting nested config values."""
    config_path = tmp_path / "config.json"
    config = Config(config_path)
    
    config.set('level1.level2.level3', 'deep_value')
    
    assert config.get('level1.level2.level3') == 'deep_value'


def test_organizer_dir(tmp_path):
    """Test organizer directory path."""
    config = Config()
    organizer_dir = config.organizer_dir
    
    assert organizer_dir.name == '.organizer'
    assert organizer_dir.parent == Path.home()


def test_ensure_organizer_dir(tmp_path):
    """Test ensuring organizer directory exists."""
    config_path = tmp_path / "config.json"
    config = Config(config_path)
    
    # Temporarily override organizer_dir
    test_dir = tmp_path / ".organizer"
    config.organizer_dir = test_dir
    
    config.ensure_organizer_dir()
    
    assert test_dir.exists()
    assert test_dir.is_dir()
