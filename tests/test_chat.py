"""Tests for chat endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


def test_send_message_unauthenticated(client: TestClient):
    """Test sending message without authentication."""
    response = client.post(
        "/api/v1/chat/message",
        json={"message": "Hello"},
    )
    assert response.status_code == 403


@patch("app.services.llm_service.LLMService.generate_response")
def test_send_message_authenticated(mock_generate, client: TestClient, auth_headers: dict):
    """Test sending message with authentication."""
    mock_generate.return_value = AsyncMock(return_value="Hello! How can I help you?")

    response = client.post(
        "/api/v1/chat/message",
        json={"message": "Hello"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "message" in data
    assert data["message"]["role"] == "assistant"


@patch("app.services.llm_service.LLMService.generate_response")
def test_send_message_with_custom_model(mock_generate, client: TestClient, auth_headers: dict):
    """Test sending message with custom model configuration."""
    mock_generate.return_value = AsyncMock(return_value="Response from custom model")

    response = client.post(
        "/api/v1/chat/message",
        json={
            "message": "Test message",
            "model_config": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "temperature": 0.5,
                "max_tokens": 1000,
            },
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model_config"]["model"] == "gpt-3.5-turbo"


def test_create_conversation(client: TestClient, auth_headers: dict):
    """Test creating a new conversation."""
    response = client.post(
        "/api/v1/chat/conversations",
        json={"title": "Test Conversation"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Conversation"
    assert "id" in data


def test_get_conversations(client: TestClient, auth_headers: dict):
    """Test getting user's conversations."""
    # Create some conversations
    client.post(
        "/api/v1/chat/conversations",
        json={"title": "Conversation 1"},
        headers=auth_headers,
    )
    client.post(
        "/api/v1/chat/conversations",
        json={"title": "Conversation 2"},
        headers=auth_headers,
    )

    # Get conversations
    response = client.get("/api/v1/chat/conversations", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_conversation_by_id(client: TestClient, auth_headers: dict):
    """Test getting a specific conversation."""
    # Create conversation
    create_response = client.post(
        "/api/v1/chat/conversations",
        json={"title": "Test Conversation"},
        headers=auth_headers,
    )
    conversation_id = create_response.json()["id"]

    # Get conversation
    response = client.get(
        f"/api/v1/chat/conversations/{conversation_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conversation_id
    assert data["title"] == "Test Conversation"


def test_update_conversation_title(client: TestClient, auth_headers: dict):
    """Test updating conversation title."""
    # Create conversation
    create_response = client.post(
        "/api/v1/chat/conversations",
        json={"title": "Old Title"},
        headers=auth_headers,
    )
    conversation_id = create_response.json()["id"]

    # Update title
    response = client.patch(
        f"/api/v1/chat/conversations/{conversation_id}",
        json={"title": "New Title"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"


def test_delete_conversation(client: TestClient, auth_headers: dict):
    """Test deleting a conversation."""
    # Create conversation
    create_response = client.post(
        "/api/v1/chat/conversations",
        json={"title": "To Delete"},
        headers=auth_headers,
    )
    conversation_id = create_response.json()["id"]

    # Delete conversation
    response = client.delete(
        f"/api/v1/chat/conversations/{conversation_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify deletion
    get_response = client.get(
        f"/api/v1/chat/conversations/{conversation_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


def test_get_nonexistent_conversation(client: TestClient, auth_headers: dict):
    """Test getting a conversation that doesn't exist."""
    response = client.get(
        "/api/v1/chat/conversations/nonexistent-id",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_empty_message(client: TestClient, auth_headers: dict):
    """Test sending an empty message."""
    response = client.post(
        "/api/v1/chat/message",
        json={"message": ""},
        headers=auth_headers,
    )
    assert response.status_code == 422
