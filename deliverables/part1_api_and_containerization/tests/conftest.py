import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Provide a fake key before any module-level import of config.py triggers
# Pydantic's BaseSettings validation.
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key-for-tests")

# Make the project root importable so `source.*` packages resolve correctly
# when tests run from the deliverables sub-directory.
_PROJECT_ROOT = str(Path(__file__).parents[3])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


@pytest.fixture(scope="session")
def mock_graph_result():
    return {
        "generation": "Hola Carlos! ¿En qué te puedo ayudar hoy?",
        "flow": ["fetch_user_data", "handle_general"],
    }


@pytest.fixture
def app_with_mock_graph(mock_graph_result):
    """FastAPI app with the LangGraph instance replaced by an AsyncMock."""
    from app.main import create_app
    from app.store.ab_config_store import ABConfigStore
    from app.store.conversation_history import ConversationHistoryStore
    from app.store.feedback_store import FeedbackStore

    test_app = create_app()

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=mock_graph_result)

    # Bypass lifespan — inject state directly.
    # Both graph_a and graph_b point to the same mock so A/B routing works
    # in tests without real OpenAI calls.
    test_app.state.graph = mock_graph  # kept for /health backward-compat
    test_app.state.graph_a = mock_graph
    test_app.state.graph_b = mock_graph
    test_app.state.history_store = ConversationHistoryStore()
    test_app.state.feedback_store = FeedbackStore()
    test_app.state.ab_config_store = ABConfigStore()

    return test_app


@pytest_asyncio.fixture
async def async_client(app_with_mock_graph):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_mock_graph),
        base_url="http://test",
    ) as client:
        yield client
