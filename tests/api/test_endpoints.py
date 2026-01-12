"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "ai_provider" in data


def test_status_endpoint():
    """Test status endpoint."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "ai_connected" in data
    assert "ai_endpoint" in data
    assert "ai_model" in data


def test_settings_endpoint():
    """Test settings endpoint."""
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert "ai_endpoint" in data
    assert "ai_model" in data
    assert "port" in data


def test_scans_list_endpoint():
    """Test scans listing endpoint."""
    response = client.get("/api/scans")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_categories_endpoint():
    """Test categories endpoint."""
    response = client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_files_list_endpoint():
    """Test files listing endpoint."""
    response = client.get("/api/files")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
