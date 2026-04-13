import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs each request: method, path, status code, duration, and correlation ID."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        correlation_id = getattr(request.state, "correlation_id", "-")
        logger.info(
            "%s %s %s %.1fms correlation_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            correlation_id,
        )
        return response
