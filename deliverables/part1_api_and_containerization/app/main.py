import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.exception_handlers import general_error_handler, validation_error_handler
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.routers import chat, health
from app.store.conversation_history import ConversationHistoryStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logging.basicConfig(level=settings.log_level)

    # Ensure OPENAI_API_KEY is available in os.environ for LangChain/OpenAI clients
    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

    # Import the graph inside lifespan so that .env is loaded before ChatOpenAI
    # reads OPENAI_API_KEY at instantiation time.
    from langgraph.checkpoint.memory import MemorySaver  # noqa: PLC0415
    from source.application.graph import workflow  # noqa: PLC0415

    checkpointer = MemorySaver()
    app.state.graph = workflow.compile(checkpointer=checkpointer)
    app.state.history_store = ConversationHistoryStore(
        max_messages=settings.max_conversation_history
    )

    logger.info("LangGraph compiled. API ready.")
    yield

    logger.info("API shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Emporyum Tech Assistant API",
        description="Conversational AI assistant for Emporyum Tech e-commerce platform.",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Middleware — order matters: the last added is the outermost (first to run on request).
    # Desired order (outermost → innermost): CORS → RequestLogging → CorrelationId
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, general_error_handler)

    app.include_router(health.router)
    app.include_router(chat.router)

    return app


app = create_app()
