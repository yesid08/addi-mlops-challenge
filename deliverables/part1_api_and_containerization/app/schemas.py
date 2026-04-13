import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

VALID_USER_IDS = {f"user_{i:03d}" for i in range(1, 9)}  # user_001 .. user_008


class ChatRequest(BaseModel):
    user_id: str = Field(..., examples=["user_001"])
    conversation_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=4000)

    @field_validator("user_id")
    @classmethod
    def user_id_must_exist(cls, v: str) -> str:
        if v not in VALID_USER_IDS:
            raise ValueError(
                f"user_id '{v}' not found. Valid IDs: user_001 through user_008"
            )
        return v

    @field_validator("conversation_id")
    @classmethod
    def conversation_id_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_\-]+$", v):
            raise ValueError(
                "conversation_id must contain only alphanumeric characters, hyphens, or underscores"
            )
        return v


class ChatResponse(BaseModel):
    conversation_id: str
    user_id: str
    response: str
    correlation_id: str
    flow: list[str] = []
    ab_variant: str = "A"


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    correlation_id: str


class HealthResponse(BaseModel):
    status: str
    graph_compiled: bool
    openai_key_configured: bool
    version: str = "1.0.0"


class MessageEntry(BaseModel):
    role: str
    content: str


class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    messages: list[MessageEntry]
    turn_count: int


# ---------------------------------------------------------------------------
# Feedback schemas
# ---------------------------------------------------------------------------


class FeedbackRequest(BaseModel):
    rating: Literal["good", "bad"] = Field(..., examples=["good"])


class FeedbackResponse(BaseModel):
    conversation_id: str
    rating: str
    ab_variant: str
    timestamp: str


class VariantStats(BaseModel):
    good: int
    bad: int
    total: int
    good_rate: float | None


class StatisticalTest(BaseModel):
    z_statistic: float
    p_value: float
    significant: bool
    note: str


class FeedbackSummaryResponse(BaseModel):
    A: VariantStats
    B: VariantStats
    statistical_test: StatisticalTest | None = None
