"""
Unit tests for domain functions and adapters.

No real LLM calls are made — the chain is replaced with an AsyncMock so tests
run without an OpenAI key and return in milliseconds.
"""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key-for-tests")

from source.adapters.utils.data_filter import filter_user_data
from source.domain.fetch_user_data import fetch_user_data
from source.domain.handle_general import handle_general


# ── Helpers ──────────────────────────────────────────────────────────────────

def _base_state(**overrides):
    state = {
        "user_id": "user_001",
        "conversation_id": "conv-1",
        "question": "Hola",
        "messages": [],
        "flow": [],
        "user_data": None,
        "user_data_summary": None,
        "generation": "",
    }
    state.update(overrides)
    return state


# ── fetch_user_data ───────────────────────────────────────────────────────────

class TestFetchUserData:
    @pytest.mark.asyncio
    async def test_returns_user_data_for_known_user(self):
        state = _base_state(user_id="user_001")
        result = await fetch_user_data(state)
        assert result["user_data"]["primer_nombre"] == "Carlos"

    @pytest.mark.asyncio
    async def test_returns_different_user_for_user_002(self):
        state = _base_state(user_id="user_002")
        result = await fetch_user_data(state)
        # user_002 exists in mock data — just verify we got *a* user
        assert result["user_data"] != {}
        assert "primer_nombre" in result["user_data"]

    @pytest.mark.asyncio
    async def test_unknown_user_returns_empty_data(self):
        state = _base_state(user_id="user_999")
        result = await fetch_user_data(state)
        assert result["user_data"] == {}

    @pytest.mark.asyncio
    async def test_appends_node_name_to_flow(self):
        state = _base_state(user_id="user_001")
        await fetch_user_data(state)
        assert "fetch_user_data" in state["flow"]

    @pytest.mark.asyncio
    async def test_skips_fetch_if_user_data_already_set(self):
        """Second call with pre-populated user_data should return {} (checkpoint optimisation)."""
        existing = {"primer_nombre": "Ana", "account_status": "active", "orders": []}
        state = _base_state(user_id="user_001", user_data=existing)
        result = await fetch_user_data(state)
        assert result == {}

    @pytest.mark.asyncio
    async def test_user_data_summary_equals_user_data(self):
        state = _base_state(user_id="user_001")
        result = await fetch_user_data(state)
        assert result["user_data"] == result["user_data_summary"]


# ── handle_general ────────────────────────────────────────────────────────────

def _mock_chain(respuesta: str = "Respuesta de prueba") -> MagicMock:
    response = MagicMock()
    response.respuesta_final = respuesta
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value=response)
    return chain


class TestHandleGeneral:
    @pytest.mark.asyncio
    async def test_returns_generation_from_chain(self):
        state = _base_state(
            user_data={"primer_nombre": "Carlos", "account_status": "active", "orders": []}
        )
        mock_chain = _mock_chain("Hola Carlos, ¿en qué te puedo ayudar?")

        with patch("source.domain.handle_general.get_general_chain", return_value=mock_chain):
            result = await handle_general(state)

        assert result["generation"] == "Hola Carlos, ¿en qué te puedo ayudar?"

    @pytest.mark.asyncio
    async def test_appends_node_name_to_flow(self):
        state = _base_state(
            user_data={"primer_nombre": "Carlos", "account_status": "active", "orders": []}
        )
        with patch("source.domain.handle_general.get_general_chain", return_value=_mock_chain()):
            await handle_general(state)

        assert "handle_general" in state["flow"]

    @pytest.mark.asyncio
    async def test_chain_receives_question_and_messages(self):
        state = _base_state(
            question="¿Cuál es mi pedido?",
            messages=[{"role": "user", "content": "Hola"}],
            user_data={"primer_nombre": "Carlos", "account_status": "active", "orders": []},
        )
        mock_chain = _mock_chain()

        with patch("source.domain.handle_general.get_general_chain", return_value=mock_chain):
            await handle_general(state)

        call_args = mock_chain.ainvoke.call_args[0][0]
        assert call_args["question"] == "¿Cuál es mi pedido?"
        assert call_args["messages"] == [{"role": "user", "content": "Hola"}]

    @pytest.mark.asyncio
    async def test_chain_receives_knowledge_base_and_user_data(self):
        state = _base_state(
            user_data={"primer_nombre": "Carlos", "account_status": "active", "orders": []}
        )
        mock_chain = _mock_chain()

        with patch("source.domain.handle_general.get_general_chain", return_value=mock_chain):
            await handle_general(state)

        call_args = mock_chain.ainvoke.call_args[0][0]
        assert "knowledge_base" in call_args
        assert "user_data" in call_args
        # user_data is stringified before sending to chain
        assert isinstance(call_args["user_data"], str)

    @pytest.mark.asyncio
    async def test_returns_spanish_fallback_on_chain_exception(self):
        state = _base_state(
            user_data={"primer_nombre": "Carlos", "account_status": "active", "orders": []}
        )
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(side_effect=RuntimeError("OpenAI down"))

        with patch("source.domain.handle_general.get_general_chain", return_value=mock_chain):
            result = await handle_general(state)

        assert "generation" in result
        assert "Disculpa" in result["generation"]

    @pytest.mark.asyncio
    async def test_handles_none_user_data_gracefully(self):
        """Graph may call handle_general even when user_data is None (unknown user)."""
        state = _base_state(user_data=None)
        mock_chain = _mock_chain("Lo siento, no encontré tu información.")

        with patch("source.domain.handle_general.get_general_chain", return_value=mock_chain):
            result = await handle_general(state)

        assert "generation" in result


# ── filter_user_data ──────────────────────────────────────────────────────────

class TestFilterUserData:
    def _full_user(self):
        return {
            "primer_nombre": "Ana",
            "email": "ana@example.com",
            "account_status": "active",
            "orders": [{"order_id": "ORD-001"}],
            "delivery_address_city": "Medellín",
            "purchase_history": ["electronics"],
            "available_promotions": ["promo_a"],
            "phone": "+57300",
        }

    def test_always_includes_mandatory_fields(self):
        result = filter_user_data(self._full_user(), [])
        assert "primer_nombre" in result
        assert "account_status" in result
        assert "orders" in result

    def test_includes_requested_relevant_field(self):
        result = filter_user_data(self._full_user(), ["delivery_address_city"])
        assert "delivery_address_city" in result

    def test_excludes_unrequested_non_mandatory_fields(self):
        result = filter_user_data(self._full_user(), [])
        assert "phone" not in result
        assert "email" not in result

    def test_multiple_relevant_fields_all_included(self):
        result = filter_user_data(
            self._full_user(),
            ["delivery_address_city", "purchase_history", "available_promotions"],
        )
        assert "delivery_address_city" in result
        assert "purchase_history" in result
        assert "available_promotions" in result

    def test_none_user_data_returns_empty_dict(self):
        assert filter_user_data(None, ["delivery_address_city"]) == {}

    def test_empty_user_data_returns_empty_dict(self):
        assert filter_user_data({}, ["delivery_address_city"]) == {}

    def test_missing_relevant_field_is_skipped_silently(self):
        """Requesting a field that does not exist in user_data must not raise."""
        user = {"primer_nombre": "Ana", "account_status": "active", "orders": []}
        result = filter_user_data(user, ["nonexistent_field"])
        assert "nonexistent_field" not in result

    def test_empty_string_in_relevant_fields_is_ignored(self):
        """An empty string in the relevant_fields list must not pollute the result."""
        user = {"primer_nombre": "Ana", "account_status": "active", "orders": []}
        result = filter_user_data(user, [""])
        assert "" not in result
