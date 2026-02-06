"""Request logging and error handling middleware."""

from __future__ import annotations

import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests with timing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.monotonic()

        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)
        elapsed_ms = (time.monotonic() - start) * 1000

        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(elapsed_ms, 2),
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Duration-MS"] = str(round(elapsed_ms, 2))
        return response
