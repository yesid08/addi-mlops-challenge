import os

from fastapi import APIRouter, Request

from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    graph_compiled = (
        hasattr(request.app.state, "graph") and request.app.state.graph is not None
    )
    key_set = bool(os.getenv("OPENAI_API_KEY"))
    return HealthResponse(
        status="ok" if graph_compiled and key_set else "degraded",
        graph_compiled=graph_compiled,
        openai_key_configured=key_set,
    )
