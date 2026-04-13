import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
    ErrorResponse,
    MessageEntry,
)

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=ChatResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        504: {"model": ErrorResponse, "description": "LLM timeout"},
        502: {"model": ErrorResponse, "description": "Upstream LLM error"},
        500: {"model": ErrorResponse, "description": "Internal error"},
    },
)
async def post_chat(request: Request, body: ChatRequest) -> ChatResponse:
    correlation_id: str = request.state.correlation_id
    graph = request.app.state.graph
    history_store = request.app.state.history_store

    chat_history = history_store.get(body.conversation_id)

    graph_input = {
        "question": body.message,
        "messages": chat_history,
        "user_id": body.user_id,
        "conversation_id": body.conversation_id,
        "generation": "",
        "flow": [],
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
    config = {"configurable": {"thread_id": body.conversation_id}}

    try:
        result = await asyncio.wait_for(
            graph.ainvoke(graph_input, config=config),
            timeout=settings.chat_timeout_seconds,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "LLM timeout after %ss | correlation_id=%s",
            settings.chat_timeout_seconds,
            correlation_id,
        )
        raise HTTPException(
            status_code=504,
            detail={
                "error": "LLM timeout",
                "detail": f"Response not received within {settings.chat_timeout_seconds}s",
                "correlation_id": correlation_id,
            },
        )
    except Exception as exc:
        logger.exception(
            "Graph invocation failed | correlation_id=%s | error=%s",
            correlation_id,
            exc,
        )
        raise HTTPException(
            status_code=502,
            detail={
                "error": "Upstream error",
                "detail": str(exc),
                "correlation_id": correlation_id,
            },
        )

    generation = result.get("generation", "")

    history_store.append_turn(
        conversation_id=body.conversation_id,
        user_message=body.message,
        assistant_message=generation,
    )

    logger.info(
        "Chat OK | user=%s | conversation=%s | flow=%s | correlation_id=%s",
        body.user_id,
        body.conversation_id,
        result.get("flow"),
        correlation_id,
    )

    return ChatResponse(
        conversation_id=body.conversation_id,
        user_id=body.user_id,
        response=generation,
        correlation_id=correlation_id,
        flow=result.get("flow", []),
    )


@router.get(
    "/conversations/{conversation_id}/history",
    response_model=ConversationHistoryResponse,
)
async def get_history(
    conversation_id: str, request: Request
) -> ConversationHistoryResponse:
    history_store = request.app.state.history_store
    messages = history_store.get(conversation_id)
    return ConversationHistoryResponse(
        conversation_id=conversation_id,
        messages=[MessageEntry(**m) for m in messages],
        turn_count=len(messages) // 2,
    )


@router.delete("/conversations/{conversation_id}/history", status_code=204)
async def clear_history(conversation_id: str, request: Request) -> None:
    request.app.state.history_store.clear(conversation_id)
