import pytest
from fastapi.testclient import TestClient
import os
import tempfile

os.environ["DATABASE_PATH"] = tempfile.mktemp(suffix=".db")
os.environ["LLM_PROVIDER"] = "mock"

from test_python_app.app import app
from test_python_app.core.database import init_database

init_database(f"sqlite:///{os.environ['DATABASE_PATH']}")


@pytest.fixture
def client():
    return TestClient(app)
