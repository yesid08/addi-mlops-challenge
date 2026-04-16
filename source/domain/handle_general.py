"""
Generic agent node: handles ALL questions using the general chain.

This basic implementation passes the entire Knowledge Base and filtered user data
into a single prompt. There is no topic routing or specialized handling —
every question gets the same treatment regardless of the topic.
"""

import logging
import time
from typing import Any

from source.adapters.chains.callbacks import TokenUsageCallback
from source.adapters.chains.general_chain import get_general_chain
from source.adapters.utils.data_filter import filter_user_data
from source.adapters.utils.knowledge_base import SCENARIO_KNOWLEDGE_BASE
from source.application.state import GraphState

logger = logging.getLogger(__name__)

# Fields the generic agent uses — a specialized agent would use fewer, topic-relevant fields.
GENERAL_RELEVANT_FIELDS = [
    "delivery_address_city",
    "purchase_history",
    "user_category_preferences",
    "available_promotions",
]


async def handle_general(state: GraphState) -> dict[str, Any]:
    """Handle any question by passing the entire KB and filtered user data to the LLM."""
    state["flow"].append("handle_general")

    knowledge_base = str(SCENARIO_KNOWLEDGE_BASE)
    filtered_data = filter_user_data(state.get("user_data"), GENERAL_RELEVANT_FIELDS)

    try:
        chain = get_general_chain()
        callback = TokenUsageCallback()
        start = time.monotonic()
        result = await chain.ainvoke(
            {
                "knowledge_base": knowledge_base,
                "user_data": str(filtered_data),
                "messages": state.get("messages", []),
                "question": state["question"],
            },
            config={"callbacks": [callback]},
        )
        llm_duration_ms = round((time.monotonic() - start) * 1000, 1)

        logger.info(
            "llm_call",
            extra={
                "node": "handle_general",
                "llm_duration_ms": llm_duration_ms,
                "prompt_tokens": callback.prompt_tokens,
                "completion_tokens": callback.completion_tokens,
                "total_tokens": callback.total_tokens,
                "model": callback.model_name,
                "user_id": state.get("user_id"),
                "conversation_id": state.get("conversation_id"),
            },
        )

        return {"generation": result.respuesta_final}

    except Exception as e:
        logger.exception(
            "handle_general_error",
            extra={
                "error": str(e),
                "user_id": state.get("user_id"),
                "conversation_id": state.get("conversation_id"),
            },
        )
        return {
            "generation": (
                "Disculpa, tuve un problema procesando tu solicitud. "
                "Por favor intenta de nuevo o contacta a nuestro equipo de soporte."
            ),
        }
