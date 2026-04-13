"""Tests for feedback endpoints and FeedbackStore."""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key-for-tests")
_PROJECT_ROOT = str(Path(__file__).parents[3])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mock_graph_result():
    return {
        "generation": "Hola Carlos! ¿En qué te puedo ayudar hoy?",
        "flow": ["fetch_user_data", "handle_general"],
    }


@pytest.fixture
def app_with_feedback(mock_graph_result):
    """App with mock graphs, history store pre-loaded with metadata, and a FeedbackStore."""
    from app.main import create_app
    from app.store.conversation_history import ConversationHistoryStore
    from app.store.feedback_store import FeedbackStore

    test_app = create_app()

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=mock_graph_result)

    history_store = ConversationHistoryStore()
    # Pre-load metadata so the feedback endpoint can resolve conversation → variant.
    history_store.set_metadata("conv-a", "user_001", "A")
    history_store.set_metadata("conv-b", "user_002", "B")

    test_app.state.graph = mock_graph
    test_app.state.graph_a = mock_graph
    test_app.state.graph_b = mock_graph
    test_app.state.history_store = history_store
    test_app.state.feedback_store = FeedbackStore()

    return test_app


@pytest_asyncio.fixture
async def feedback_client(app_with_feedback):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_feedback),
        base_url="http://test",
    ) as client:
        yield client


# ---------------------------------------------------------------------------
# POST /chat/conversations/{id}/feedback
# ---------------------------------------------------------------------------


class TestPostFeedback:
    @pytest.mark.asyncio
    async def test_good_rating_returns_200(self, feedback_client: AsyncClient) -> None:
        resp = await feedback_client.post(
            "/chat/conversations/conv-a/feedback",
            json={"rating": "good"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_bad_rating_returns_200(self, feedback_client: AsyncClient) -> None:
        resp = await feedback_client.post(
            "/chat/conversations/conv-b/feedback",
            json={"rating": "bad"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_response_schema(self, feedback_client: AsyncClient) -> None:
        resp = await feedback_client.post(
            "/chat/conversations/conv-a/feedback",
            json={"rating": "good"},
        )
        body = resp.json()
        assert body["conversation_id"] == "conv-a"
        assert body["rating"] == "good"
        assert body["ab_variant"] == "A"
        assert "timestamp" in body

    @pytest.mark.asyncio
    async def test_variant_b_returned_for_b_conversation(
        self, feedback_client: AsyncClient
    ) -> None:
        resp = await feedback_client.post(
            "/chat/conversations/conv-b/feedback",
            json={"rating": "good"},
        )
        assert resp.json()["ab_variant"] == "B"

    @pytest.mark.asyncio
    async def test_unknown_conversation_returns_404(
        self, feedback_client: AsyncClient
    ) -> None:
        resp = await feedback_client.post(
            "/chat/conversations/does-not-exist/feedback",
            json={"rating": "good"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_rating_returns_422(
        self, feedback_client: AsyncClient
    ) -> None:
        resp = await feedback_client.post(
            "/chat/conversations/conv-a/feedback",
            json={"rating": "meh"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /ab/feedback/summary
# ---------------------------------------------------------------------------


class TestFeedbackSummary:
    @pytest.mark.asyncio
    async def test_summary_empty_state(self, feedback_client: AsyncClient) -> None:
        """Summary should always return 200 even with no feedback recorded."""
        resp = await feedback_client.get("/ab/feedback/summary")
        assert resp.status_code == 200
        body = resp.json()
        assert body["A"]["total"] == 0
        assert body["B"]["total"] == 0
        assert body["statistical_test"] is None

    @pytest.mark.asyncio
    async def test_summary_accumulates_ratings(
        self, feedback_client: AsyncClient
    ) -> None:
        """Good and bad counts should reflect submitted feedback."""
        # Submit some feedback
        for _ in range(3):
            await feedback_client.post(
                "/chat/conversations/conv-a/feedback", json={"rating": "good"}
            )
        await feedback_client.post(
            "/chat/conversations/conv-a/feedback", json={"rating": "bad"}
        )

        resp = await feedback_client.get("/ab/feedback/summary")
        body = resp.json()
        # Variant A should have at least the 4 entries we just added.
        assert body["A"]["total"] >= 4

    @pytest.mark.asyncio
    async def test_statistical_test_absent_below_threshold(
        self, app_with_feedback
    ) -> None:
        """z-test must be None when either variant has fewer than 10 entries."""
        # Use a fresh client with a clean feedback store.
        from app.store.feedback_store import FeedbackStore

        app_with_feedback.state.feedback_store = FeedbackStore()

        async with AsyncClient(
            transport=ASGITransport(app=app_with_feedback), base_url="http://test"
        ) as client:
            # Add only 5 entries to variant A, none to B.
            for _ in range(5):
                await client.post(
                    "/chat/conversations/conv-a/feedback", json={"rating": "good"}
                )
            resp = await client.get("/ab/feedback/summary")
            assert resp.json()["statistical_test"] is None

    @pytest.mark.asyncio
    async def test_statistical_test_present_above_threshold(
        self, app_with_feedback
    ) -> None:
        """z-test should be present when each variant has ≥10 feedback entries."""
        from app.store.feedback_store import FeedbackEntry, FeedbackStore

        store = FeedbackStore()
        for i in range(12):
            store.record(
                FeedbackEntry(
                    conversation_id=f"c{i}",
                    user_id="user_001",
                    ab_variant="A",
                    rating="good" if i < 9 else "bad",
                )
            )
        for i in range(12):
            store.record(
                FeedbackEntry(
                    conversation_id=f"d{i}",
                    user_id="user_002",
                    ab_variant="B",
                    rating="good" if i < 7 else "bad",
                )
            )
        app_with_feedback.state.feedback_store = store

        async with AsyncClient(
            transport=ASGITransport(app=app_with_feedback), base_url="http://test"
        ) as client:
            resp = await client.get("/ab/feedback/summary")
            test_result = resp.json()["statistical_test"]
            assert test_result is not None
            assert "z_statistic" in test_result
            assert "p_value" in test_result
            assert "significant" in test_result


# ---------------------------------------------------------------------------
# FeedbackStore unit tests (no HTTP)
# ---------------------------------------------------------------------------


class TestFeedbackStore:
    def test_record_and_summary_counts(self) -> None:
        from app.store.feedback_store import FeedbackEntry, FeedbackStore

        store = FeedbackStore()
        store.record(FeedbackEntry("c1", "user_001", "A", "good"))
        store.record(FeedbackEntry("c2", "user_001", "A", "bad"))
        store.record(FeedbackEntry("c3", "user_002", "B", "good"))

        summary = store.get_summary()
        assert summary["A"]["good"] == 1
        assert summary["A"]["bad"] == 1
        assert summary["A"]["total"] == 2
        assert summary["B"]["good"] == 1
        assert summary["B"]["total"] == 1

    def test_good_rate_none_when_no_entries(self) -> None:
        from app.store.feedback_store import FeedbackStore

        store = FeedbackStore()
        summary = store.get_summary()
        assert summary["A"]["good_rate"] is None
        assert summary["B"]["good_rate"] is None

    def test_good_rate_computed_correctly(self) -> None:
        from app.store.feedback_store import FeedbackEntry, FeedbackStore

        store = FeedbackStore()
        store.record(FeedbackEntry("c1", "user_001", "A", "good"))
        store.record(FeedbackEntry("c2", "user_001", "A", "good"))
        store.record(FeedbackEntry("c3", "user_001", "A", "bad"))

        summary = store.get_summary()
        assert summary["A"]["good_rate"] == round(2 / 3, 4)
