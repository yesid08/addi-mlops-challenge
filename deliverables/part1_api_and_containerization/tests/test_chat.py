import asyncio
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_chat_success(async_client):
    response = await async_client.post(
        "/chat",
        json={
            "user_id": "user_001",
            "conversation_id": "test-conv-1",
            "message": "Hola, ¿cómo estás?",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "correlation_id" in data
    assert data["conversation_id"] == "test-conv-1"
    assert data["user_id"] == "user_001"
    assert isinstance(data["flow"], list)


@pytest.mark.asyncio
async def test_chat_response_has_correlation_id_header(async_client):
    response = await async_client.post(
        "/chat",
        json={"user_id": "user_001", "conversation_id": "c1", "message": "test"},
    )
    assert "X-Correlation-ID" in response.headers


@pytest.mark.asyncio
async def test_chat_correlation_id_passthrough(async_client):
    """Caller-provided correlation ID is echoed in header and body."""
    response = await async_client.post(
        "/chat",
        json={"user_id": "user_001", "conversation_id": "c1", "message": "test"},
        headers={"X-Correlation-ID": "my-trace-abc123"},
    )
    assert response.headers["X-Correlation-ID"] == "my-trace-abc123"
    assert response.json()["correlation_id"] == "my-trace-abc123"


@pytest.mark.asyncio
async def test_chat_invalid_user_id_returns_422(async_client):
    response = await async_client.post(
        "/chat",
        json={"user_id": "user_999", "conversation_id": "c1", "message": "Hola"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_empty_message_returns_422(async_client):
    response = await async_client.post(
        "/chat",
        json={"user_id": "user_001", "conversation_id": "c1", "message": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_missing_fields_returns_422(async_client):
    response = await async_client.post("/chat", json={"user_id": "user_001"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_timeout_returns_504(async_client, app_with_mock_graph):
    app_with_mock_graph.state.graph.ainvoke = AsyncMock(
        side_effect=asyncio.TimeoutError()
    )
    response = await async_client.post(
        "/chat",
        json={"user_id": "user_001", "conversation_id": "c2", "message": "test"},
    )
    assert response.status_code == 504


@pytest.mark.asyncio
async def test_chat_graph_exception_returns_502(async_client, app_with_mock_graph):
    app_with_mock_graph.state.graph.ainvoke = AsyncMock(
        side_effect=RuntimeError("OpenAI rate limit")
    )
    response = await async_client.post(
        "/chat",
        json={"user_id": "user_001", "conversation_id": "c3", "message": "test"},
    )
    assert response.status_code == 502


@pytest.mark.asyncio
async def test_history_persists_across_turns(async_client):
    """Server stores history so second turn includes first turn context."""
    for msg in ["Hola", "¿Cuál es mi saldo?"]:
        resp = await async_client.post(
            "/chat",
            json={
                "user_id": "user_001",
                "conversation_id": "persist-test",
                "message": msg,
            },
        )
        assert resp.status_code == 200

    history_resp = await async_client.get(
        "/chat/conversations/persist-test/history"
    )
    assert history_resp.status_code == 200
    data = history_resp.json()
    assert data["turn_count"] == 2
    assert len(data["messages"]) == 4  # 2 user + 2 assistant


@pytest.mark.asyncio
async def test_get_history_empty_conversation(async_client):
    response = await async_client.get("/chat/conversations/never-used/history")
    assert response.status_code == 200
    data = response.json()
    assert data["turn_count"] == 0
    assert data["messages"] == []


@pytest.mark.asyncio
async def test_delete_history(async_client):
    # Populate history
    await async_client.post(
        "/chat",
        json={"user_id": "user_002", "conversation_id": "delete-test", "message": "Hola"},
    )
    # Clear it
    del_resp = await async_client.delete("/chat/conversations/delete-test/history")
    assert del_resp.status_code == 204

    # Confirm empty
    history_resp = await async_client.get("/chat/conversations/delete-test/history")
    assert history_resp.json()["turn_count"] == 0
