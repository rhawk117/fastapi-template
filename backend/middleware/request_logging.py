from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.core.security.fingerprint import ClientFingerprint

if TYPE_CHECKING:
    from fastapi import Request, Response
    from starlette.types import ASGIApp



class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.logger = logging.getLogger(__name__)

    async def dispatch(
        self, request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid.uuid4())

        fingerprint = await ClientFingerprint.from_request(request)

        start_time = time.perf_counter()

        self.logger.info(
            f'ID={request_id} | Inbound HTTP request ({request.method}) '
            f'- {request.url} from {fingerprint.ip_address}'
        )

        response: Response = await call_next(request)

        elapsed = time.perf_counter() - start_time

        self.logger.info(
            f'ID={request_id} | Outbound HTTP response ({response.status_code}) '
            f'- {request.url} from {fingerprint.ip_address} '
            f'in {elapsed:.2f} seconds'
        )

        response.headers['X-Request-ID'] = request_id

        return response

