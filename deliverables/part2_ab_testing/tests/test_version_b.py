"""Unit tests for the Version B treatment agent."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from source.application.state import GraphState


def _make_state(**overrides: Any) -> GraphState:
    state: GraphState = {
        "user_id": "user_001",
        "conversation_id": "test-conv",
        "question": "¿Cuál es el estado de mi pedido?",
        "messages": [],
        "generation": "",
        "flow": [],
        "user_data": {
            "primer_nombre": "Carlos",
            "account_status": "active",
            "orders": [],
        },
        "user_data_summary": None,
        "selected_topic": None,
        "selected_agent": None,
        "router_reasoning": None,
        "current_step": None,
        "is_return_in_progress": False,
        "last_topic_selected": None,
        "set_previous_selected_topics": [],
    }
    state.update(overrides)  # type: ignore[typeddict-item]
    return state


class TestHandleGeneralB:
    @pytest.mark.asyncio
    async def test_returns_generation_from_chain(self) -> None:
        mock_response = MagicMock()
        mock_response.respuesta_final = "¡Hola Carlos! Tu pedido está en camino."
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        with patch(
            "deliverables.part2_ab_testing.agent_versions.version_b.get_treatment_chain",
            return_value=mock_chain,
        ):
            from deliverables.part2_ab_testing.agent_versions.version_b import (
                handle_general_b,
            )

            result = await handle_general_b(_make_state())

        assert result["generation"] == "¡Hola Carlos! Tu pedido está en camino."

    @pytest.mark.asyncio
    async def test_appends_handle_general_to_flow(self) -> None:
        mock_response = MagicMock()
        mock_response.respuesta_final = "Respuesta de prueba."
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        state = _make_state()
        with patch(
            "deliverables.part2_ab_testing.agent_versions.version_b.get_treatment_chain",
            return_value=mock_chain,
        ):
            from deliverables.part2_ab_testing.agent_versions.version_b import (
                handle_general_b,
            )

            await handle_general_b(state)

        assert "handle_general" in state["flow"]

    @pytest.mark.asyncio
    async def test_chain_receives_expected_keys(self) -> None:
        mock_response = MagicMock()
        mock_response.respuesta_final = "OK"
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        with patch(
            "deliverables.part2_ab_testing.agent_versions.version_b.get_treatment_chain",
            return_value=mock_chain,
        ):
            from deliverables.part2_ab_testing.agent_versions.version_b import (
                handle_general_b,
            )

            await handle_general_b(_make_state())

        call_kwargs = mock_chain.ainvoke.call_args[0][0]
        assert "knowledge_base" in call_kwargs
        assert "user_data" in call_kwargs
        assert "messages" in call_kwargs
        assert "question" in call_kwargs

    @pytest.mark.asyncio
    async def test_knowledge_base_is_bullet_formatted(self) -> None:
        """KB passed to the chain should be bullet-formatted, not a raw dict repr."""
        mock_response = MagicMock()
        mock_response.respuesta_final = "OK"
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        with patch(
            "deliverables.part2_ab_testing.agent_versions.version_b.get_treatment_chain",
            return_value=mock_chain,
        ):
            from deliverables.part2_ab_testing.agent_versions.version_b import (
                handle_general_b,
            )

            await handle_general_b(_make_state())

        kb_str: str = mock_chain.ainvoke.call_args[0][0]["knowledge_base"]
        # Bullet format starts with "•", raw dict repr starts with "{"
        assert kb_str.startswith("•"), "Expected bullet-formatted KB"
        assert "{" not in kb_str[:10], "KB should not start with raw dict repr"

    @pytest.mark.asyncio
    async def test_returns_spanish_fallback_on_exception(self) -> None:
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(side_effect=RuntimeError("API error"))

        with patch(
            "deliverables.part2_ab_testing.agent_versions.version_b.get_treatment_chain",
            return_value=mock_chain,
        ):
            from deliverables.part2_ab_testing.agent_versions.version_b import (
                handle_general_b,
            )

            result = await handle_general_b(_make_state())

        assert "Disculpa" in result["generation"]

    def test_treatment_chain_uses_temperature_03(self) -> None:
        with patch(
            "deliverables.part2_ab_testing.agent_versions.version_b.ChatOpenAI"
        ) as mock_llm_cls:
            mock_instance = MagicMock()
            mock_llm_cls.return_value = mock_instance
            mock_instance.with_structured_output.return_value = MagicMock()

            from deliverables.part2_ab_testing.agent_versions.version_b import (
                get_treatment_chain,
            )

            get_treatment_chain()

            _, kwargs = mock_llm_cls.call_args
            assert kwargs.get("temperature") == 0.3


class TestFormatKbAsBullets:
    def test_output_starts_with_bullet(self) -> None:
        from deliverables.part2_ab_testing.agent_versions.version_b import (
            _format_kb_as_bullets,
        )

        result = _format_kb_as_bullets(
            {"SALUDO": {"contexto": "Saludo", "instrucciones": "Saludar"}}
        )
        assert result.startswith("•")

    def test_each_topic_on_separate_line(self) -> None:
        from deliverables.part2_ab_testing.agent_versions.version_b import (
            _format_kb_as_bullets,
        )

        kb = {
            "SALUDO": {"contexto": "A", "instrucciones": "B"},
            "PEDIDOS": {"contexto": "C", "instrucciones": "D"},
        }
        result = _format_kb_as_bullets(kb)
        lines = result.splitlines()
        assert len(lines) == 2
        assert "SALUDO" in lines[0]
        assert "PEDIDOS" in lines[1]
