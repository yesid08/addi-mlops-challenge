import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "-")
    # Use jsonable_encoder to safely serialize Pydantic v2 error dicts, which
    # may contain non-serializable objects (e.g. ValueError) in the `ctx` field.
    errors = jsonable_encoder(exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "detail": errors,
            "correlation_id": correlation_id,
        },
    )


async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "-")
    logger.exception("Unhandled exception | correlation_id=%s", correlation_id)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred.",
            "correlation_id": correlation_id,
        },
    )
