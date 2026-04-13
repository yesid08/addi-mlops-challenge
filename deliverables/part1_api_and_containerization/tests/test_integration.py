"""
Integration tests: full LangGraph workflow (fetch_user_data → handle_general → END).

The LLM chain is mocked so no OpenAI key is required, but the graph itself is
compiled and executed — both nodes run in the correct order through LangGraph's
state machine.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key-for-tests")

from langgraph.checkpoint.memory import MemorySaver

from source.application.graph import workflow

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def compiled_graph():
    """Compile the workflow once for all integration tests in this module."""
    return workflow.compile(checkpointer=MemorySaver())


def _mock_chain(answer: str = "Hola Carlos, ¿en qué te puedo ayudar?") -> MagicMock:
    response = MagicMock()
    response.respuesta_final = answer
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value=response)
    return chain


def _graph_input(user_id: str = "user_001", question: str = "Hola") -> dict:
    return {
        "user_id": user_id,
        "conversation_id": "integration-conv",
        "question": question,
        "messages": [],
        "flow": [],
        "generation": "",
        "user_data": None,
        "user_data_summary": None,
        "selected_topic": None,
        "selected_agent": None,
        "router_reasoning": None,
        "current_step": None,
        "is_return_in_progress": False,
        "last_topic_selected": None,
        "set_previous_selected_topics": [],
    }


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestFullGraphFlow:
    @pytest.mark.asyncio
    async def test_both_nodes_appear_in_flow(self, compiled_graph):
        with patch(
            "source.domain.handle_general.get_general_chain", return_value=_mock_chain()
        ):
            result = await compiled_graph.ainvoke(
                _graph_input(user_id="user_001"),
                config={"configurable": {"thread_id": "it-flow-1"}},
            )

        assert "fetch_user_data" in result["flow"]
        assert "handle_general" in result["flow"]

    @pytest.mark.asyncio
    async def test_nodes_execute_in_order(self, compiled_graph):
        with patch(
            "source.domain.handle_general.get_general_chain", return_value=_mock_chain()
        ):
            result = await compiled_graph.ainvoke(
                _graph_input(user_id="user_001"),
                config={"configurable": {"thread_id": "it-order-1"}},
            )

        flow = result["flow"]
        assert flow.index("fetch_user_data") < flow.index("handle_general")

    @pytest.mark.asyncio
    async def test_generation_is_populated(self, compiled_graph):
        expected = "Tu pedido está en camino, Carlos."
        with patch(
            "source.domain.handle_general.get_general_chain",
            return_value=_mock_chain(expected),
        ):
            result = await compiled_graph.ainvoke(
                _graph_input(user_id="user_001", question="¿Cuál es mi pedido?"),
                config={"configurable": {"thread_id": "it-gen-1"}},
            )

        assert result["generation"] == expected

    @pytest.mark.asyncio
    async def test_user_data_fetched_for_known_user(self, compiled_graph):
        with patch(
            "source.domain.handle_general.get_general_chain", return_value=_mock_chain()
        ):
            result = await compiled_graph.ainvoke(
                _graph_input(user_id="user_001"),
                config={"configurable": {"thread_id": "it-user-1"}},
            )

        assert result["user_data"]["primer_nombre"] == "Carlos"

    @pytest.mark.asyncio
    async def test_unknown_user_produces_empty_user_data(self, compiled_graph):
        with patch(
            "source.domain.handle_general.get_general_chain", return_value=_mock_chain()
        ):
            result = await compiled_graph.ainvoke(
                _graph_input(user_id="user_999"),
                config={"configurable": {"thread_id": "it-unknown-1"}},
            )

        assert result["user_data"] == {}

    @pytest.mark.asyncio
    async def test_fallback_generation_on_llm_error(self, compiled_graph):
        broken_chain = MagicMock()
        broken_chain.ainvoke = AsyncMock(side_effect=RuntimeError("LLM unavailable"))

        with patch(
            "source.domain.handle_general.get_general_chain", return_value=broken_chain
        ):
            result = await compiled_graph.ainvoke(
                _graph_input(user_id="user_001"),
                config={"configurable": {"thread_id": "it-err-1"}},
            )

        assert "Disculpa" in result["generation"]

    @pytest.mark.asyncio
    async def test_different_users_get_correct_data(self, compiled_graph):
        """Run two sequential invocations for different users; each gets their own data."""
        with patch(
            "source.domain.handle_general.get_general_chain", return_value=_mock_chain()
        ):
            result_001 = await compiled_graph.ainvoke(
                _graph_input(user_id="user_001"),
                config={"configurable": {"thread_id": "it-multi-1"}},
            )
            result_002 = await compiled_graph.ainvoke(
                _graph_input(user_id="user_002"),
                config={"configurable": {"thread_id": "it-multi-2"}},
            )

        assert (
            result_001["user_data"]["primer_nombre"]
            != result_002["user_data"]["primer_nombre"]
        )
