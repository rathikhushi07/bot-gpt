"""
Pytest configuration
"""
import pytest
from fastapi.testclient import TestClient
from src.test_chatbot.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)



