import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Provide a fake key before any module-level import of config.py triggers
# Pydantic's BaseSettings validation.
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key-for-tests")


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
    from app.store.conversation_history import ConversationHistoryStore

    test_app = create_app()

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=mock_graph_result)

    # Bypass lifespan — inject state directly
    test_app.state.graph = mock_graph
    test_app.state.history_store = ConversationHistoryStore()

    return test_app


@pytest_asyncio.fixture
async def async_client(app_with_mock_graph):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_mock_graph),
        base_url="http://test",
    ) as client:
        yield client
