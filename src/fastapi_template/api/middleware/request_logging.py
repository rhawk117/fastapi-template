from __future__ import annotations

import time
from collections.abc import Awaitable
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

log = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.perf_counter()

        request_id = request.headers.get('X-Request-ID', 'N/A')

        log.info(
            'app.request',
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            user_agent=request.headers.get('User-Agent', 'N/A'),
            client_ip=request.client.host if request.client else 'N/A',
        )

        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to milliseconds

        log.info(
            'app.response',
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            elapsed_ms=elapsed,
        )

        return response
