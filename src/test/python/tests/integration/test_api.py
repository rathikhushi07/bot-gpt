import pytest
from fastapi.testclient import TestClient
import os
import tempfile
from pathlib import Path

os.environ["DATABASE_PATH"] = tempfile.mktemp(suffix=".db")
os.environ["LLM_PROVIDER"] = "mock"

from test_python_app.app import app
from test_python_app.core.database import init_database, get_db_manager
from test_python_app.models.domain.entities import User


@pytest.fixture(scope="module")
def client():
    init_database(f"sqlite:///{os.environ['DATABASE_PATH']}")
    
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def test_user(client):
    response = client.post(
        "/api/users",
        json={
            "username": "testuser",
            "email": "test@example.com"
        }
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture(scope="module")
def test_document(client, test_user):
    response = client.post(
        "/api/documents",
        json={
            "user_id": test_user["id"],
            "filename": "test.txt",
            "content": "Python is a programming language. It is used for web development and data science. Python has simple syntax.",
            "mime_type": "text/plain"
        }
    )
    assert response.status_code == 201
    return response.json()


class TestHealthEndpoints:
    
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"
    
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "UP"
        assert "timestamp" in data
        assert "database" in data


class TestUserEndpoints:
    
    def test_create_user(self, client):
        response = client.post(
            "/api/users",
            json={
                "username": "newuser",
                "email": "newuser@example.com"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
    
    def test_create_user_duplicate_username(self, client, test_user):
        response = client.post(
            "/api/users",
            json={
                "username": test_user["username"],
                "email": "another@example.com"
            }
        )
        assert response.status_code == 400
    
    def test_list_users(self, client, test_user):
        response = client.get("/api/users")
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) > 0
    
    def test_get_user(self, client, test_user):
        response = client.get(f"/api/users/{test_user['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user["id"]
        assert data["username"] == test_user["username"]
    
    def test_get_nonexistent_user(self, client):
        response = client.get("/api/users/nonexistent-id")
        assert response.status_code == 404


class TestDocumentEndpoints:
    
    def test_upload_document(self, client, test_user):
        response = client.post(
            "/api/documents",
            json={
                "user_id": test_user["id"],
                "filename": "doc.txt",
                "content": "This is a test document with some content.",
                "mime_type": "text/plain"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "doc.txt"
        assert data["chunk_count"] > 0
        assert "id" in data
    
    def test_list_documents(self, client, test_user, test_document):
        response = client.get(f"/api/documents?user_id={test_user['id']}")
        assert response.status_code == 200
        documents = response.json()
        assert isinstance(documents, list)
        assert len(documents) > 0
    
    def test_get_document(self, client, test_document):
        response = client.get(f"/api/documents/{test_document['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_document["id"]
        assert data["filename"] == test_document["filename"]
    
    def test_delete_document(self, client, test_user):
        create_response = client.post(
            "/api/documents",
            json={
                "user_id": test_user["id"],
                "filename": "to-delete.txt",
                "content": "This will be deleted.",
                "mime_type": "text/plain"
            }
        )
        doc_id = create_response.json()["id"]
        
        delete_response = client.delete(f"/api/documents/{doc_id}")
        assert delete_response.status_code == 204
        
        get_response = client.get(f"/api/documents/{doc_id}")
        assert get_response.status_code == 404


class TestConversationEndpoints:
    
    def test_create_open_chat_conversation(self, client, test_user):
        response = client.post(
            "/api/conversations",
            json={
                "user_id": test_user["id"],
                "first_message": "Hello, how are you?",
                "mode": "open_chat"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert "conversation_id" in data
        assert "message" in data
        assert data["message"]["role"] == "assistant"
        assert len(data["message"]["content"]) > 0
    
    def test_create_rag_conversation(self, client, test_user, test_document):
        response = client.post(
            "/api/conversations",
            json={
                "user_id": test_user["id"],
                "first_message": "What is Python used for?",
                "mode": "grounded_rag",
                "document_ids": [test_document["id"]]
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert "conversation_id" in data
        assert "message" in data
    
    def test_list_conversations(self, client, test_user):
        response = client.get(f"/api/conversations?user_id={test_user['id']}&page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["items"], list)
    
    def test_get_conversation_detail(self, client, test_user):
        create_response = client.post(
            "/api/conversations",
            json={
                "user_id": test_user["id"],
                "first_message": "Test message",
                "mode": "open_chat"
            }
        )
        conv_id = create_response.json()["conversation_id"]
        
        response = client.get(f"/api/conversations/{conv_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conv_id
        assert "messages" in data
        assert len(data["messages"]) >= 2
    
    def test_add_message_to_conversation(self, client, test_user):
        create_response = client.post(
            "/api/conversations",
            json={
                "user_id": test_user["id"],
                "first_message": "Hello",
                "mode": "open_chat"
            }
        )
        conv_id = create_response.json()["conversation_id"]
        
        response = client.post(
            f"/api/conversations/{conv_id}/messages",
            json={
                "content": "Tell me more"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conv_id
        assert data["message"]["role"] == "assistant"
    
    def test_delete_conversation(self, client, test_user):
        create_response = client.post(
            "/api/conversations",
            json={
                "user_id": test_user["id"],
                "first_message": "To be deleted",
                "mode": "open_chat"
            }
        )
        conv_id = create_response.json()["conversation_id"]
        
        delete_response = client.delete(f"/api/conversations/{conv_id}")
        assert delete_response.status_code == 204
        
        get_response = client.get(f"/api/conversations/{conv_id}")
        assert get_response.status_code == 404


class TestErrorHandling:
    
    def test_create_conversation_nonexistent_user(self, client):
        response = client.post(
            "/api/conversations",
            json={
                "user_id": "nonexistent-user-id",
                "first_message": "Hello",
                "mode": "open_chat"
            }
        )
        assert response.status_code == 404
    
    def test_add_message_to_nonexistent_conversation(self, client):
        response = client.post(
            "/api/conversations/nonexistent-id/messages",
            json={
                "content": "Hello"
            }
        )
        assert response.status_code == 404
    
    def test_invalid_request_validation(self, client, test_user):
        response = client.post(
            "/api/conversations",
            json={
                "user_id": test_user["id"],
                "first_message": "",
                "mode": "open_chat"
            }
        )
        assert response.status_code == 422
