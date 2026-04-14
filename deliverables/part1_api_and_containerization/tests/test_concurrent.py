"""
Concurrent request tests.

Verifies that the FastAPI service handles simultaneous requests from multiple
users correctly — responses land on the right conversation, history stays
isolated between conversations, and no request is lost or garbled.

The four concurrent users map to user_001 through user_004 from mock_data.
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key-for-tests")


# ── Fixture ───────────────────────────────────────────────────────────────────


@pytest.fixture
def concurrent_app():
    """Fresh FastAPI app with a mocked graph for each test."""
    from app.main import create_app
    from app.store.ab_config_store import ABConfigStore
    from app.store.conversation_history import ConversationHistoryStore
    from app.store.feedback_store import FeedbackStore

    app = create_app()
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "generation": "Respuesta de prueba concurrente.",
            "flow": ["fetch_user_data", "handle_general"],
        }
    )
    app.state.graph = mock_graph
    app.state.graph_a = mock_graph
    app.state.graph_b = mock_graph
    app.state.history_store = ConversationHistoryStore()
    app.state.feedback_store = FeedbackStore()
    app.state.ab_config_store = ABConfigStore()
    return app


# ── Helpers ───────────────────────────────────────────────────────────────────

FOUR_USERS = ["user_001", "user_002", "user_003", "user_004"]


async def _chat(client: AsyncClient, user_id: str, conv_suffix: str, message: str):
    return await client.post(
        "/chat",
        json={
            "user_id": user_id,
            "conversation_id": f"{conv_suffix}-{user_id}",
            "message": message,
        },
    )


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_four_concurrent_requests_all_succeed(concurrent_app):
    """All four simultaneous requests return HTTP 200."""
    async with AsyncClient(
        transport=ASGITransport(app=concurrent_app), base_url="http://test"
    ) as client:
        responses = await asyncio.gather(
            *[_chat(client, uid, "basic", "Hola, ¿cómo estás?") for uid in FOUR_USERS]
        )

    for user_id, resp in zip(FOUR_USERS, responses):
        assert resp.status_code == 200, f"{user_id}: {resp.text}"


@pytest.mark.asyncio
async def test_four_concurrent_responses_routed_to_correct_user(concurrent_app):
    """Each response carries the user_id and conversation_id of the originating request."""
    async with AsyncClient(
        transport=ASGITransport(app=concurrent_app), base_url="http://test"
    ) as client:
        responses = await asyncio.gather(
            *[
                _chat(client, uid, "routing", "¿Cuál es mi pedido?")
                for uid in FOUR_USERS
            ]
        )

    for user_id, resp in zip(FOUR_USERS, responses):
        data = resp.json()
        assert data["user_id"] == user_id, f"Expected {user_id}, got {data['user_id']}"
        assert data["conversation_id"] == f"routing-{user_id}"


@pytest.mark.asyncio
async def test_four_concurrent_responses_have_unique_correlation_ids(concurrent_app):
    """Each concurrent response gets its own correlation ID (no ID collisions)."""
    async with AsyncClient(
        transport=ASGITransport(app=concurrent_app), base_url="http://test"
    ) as client:
        responses = await asyncio.gather(
            *[_chat(client, uid, "corrids", "Hola") for uid in FOUR_USERS]
        )

    correlation_ids = [r.json()["correlation_id"] for r in responses]
    assert len(set(correlation_ids)) == 4, "Duplicate correlation IDs detected"


@pytest.mark.asyncio
async def test_concurrent_history_isolation(concurrent_app):
    """
    Each user sends two messages concurrently. After both rounds settle, every
    conversation must have exactly 2 turns — no cross-contamination.
    """
    async with AsyncClient(
        transport=ASGITransport(app=concurrent_app), base_url="http://test"
    ) as client:

        async def two_turns(user_id: str):
            conv_id = f"isolation-{user_id}"
            await asyncio.gather(
                _chat(client, user_id, "isolation", "Hola"),
                _chat(client, user_id, "isolation", "¿Cuál es mi saldo?"),
            )
            return conv_id

        # Run all four users concurrently — each fires two parallel messages
        conv_ids = await asyncio.gather(*[two_turns(uid) for uid in FOUR_USERS])

        for conv_id in conv_ids:
            resp = await client.get(f"/chat/conversations/{conv_id}/history")
            data = resp.json()
            assert data["turn_count"] == 2, (
                f"{conv_id} has {data['turn_count']} turns — expected 2"
            )
