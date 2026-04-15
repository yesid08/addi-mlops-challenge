"""Feedback router — user adoption signal for A/B experiment evaluation.

Endpoints:
  POST /chat/conversations/{conversation_id}/feedback
      Record a "good" or "bad" rating for a completed conversation.
      The variant (A or B) is looked up from conversation metadata stored
      by the chat router, so callers do not need to track it themselves.
      Returns 404 if the conversation_id has no recorded metadata (i.e. the
      conversation never went through POST /chat first).

  GET /ab/feedback/summary
      Return per-variant good/bad counts, good-rates, and a live two-proportion
      z-test.  The statistical_test field is null until each variant accumulates
      at least 10 feedback entries.
"""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.schemas import (
    FeedbackRequest,
    FeedbackResponse,
    FeedbackSummaryResponse,
    VariantStats,
)
from app.store.feedback_store import FeedbackEntry

router = APIRouter(tags=["feedback"])
logger = logging.getLogger(__name__)


@router.post(
    "/chat/conversations/{conversation_id}/feedback",
    response_model=FeedbackResponse,
    responses={
        404: {"description": "Conversation not found — call POST /chat first"},
        422: {"description": "Validation error (invalid rating value)"},
    },
)
async def post_feedback(
    conversation_id: str,
    body: FeedbackRequest,
    request: Request,
) -> FeedbackResponse:
    history_store = request.app.state.history_store
    feedback_store = request.app.state.feedback_store

    metadata = history_store.get_metadata(conversation_id)
    if metadata is None:
        raise HTTPException(
            status_code=404,
            detail=f"No conversation found for id '{conversation_id}'. "
            "Send at least one message via POST /chat first.",
        )

    entry = FeedbackEntry(
        conversation_id=conversation_id,
        user_id=metadata["user_id"],
        ab_variant=metadata["ab_variant"],
        was_good=body.was_good,
    )
    feedback_store.record(entry)

    logger.info(
        "Feedback recorded | conversation=%s | variant=%s | was_good=%s",
        conversation_id,
        entry.ab_variant,
        body.was_good,
    )

    return FeedbackResponse(
        conversation_id=conversation_id,
        was_good=body.was_good,
        ab_variant=entry.ab_variant,
        timestamp=entry.timestamp,
    )


@router.get("/ab/feedback/summary", response_model=FeedbackSummaryResponse)
async def get_feedback_summary(request: Request) -> FeedbackSummaryResponse:
    """Return per-variant adoption stats and a live two-proportion z-test."""
    feedback_store = request.app.state.feedback_store
    raw = feedback_store.get_summary()

    def _variant_stats(v: str) -> VariantStats:
        return VariantStats(
            good=raw[v]["good"],
            bad=raw[v]["bad"],
            total=raw[v]["total"],
            good_rate=raw[v]["good_rate"],
        )

    return FeedbackSummaryResponse(
        A=_variant_stats("A"),
        B=_variant_stats("B"),
        statistical_test=raw.get("statistical_test"),
    )
