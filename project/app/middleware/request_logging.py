from __future__ import annotations

import logging
import time
import uuid
from typing import TYPE_CHECKING

from app.core.security.fingerprint import ClientFingerprint
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from app.common.types import CallNext
    from fastapi import Request, Response
    from starlette.types import ASGIApp


logger = logging.getLogger(__name__)


async def request_logging_middleware(request: Request, call_next: CallNext) -> Response:
    request_id = str(uuid.uuid4())

    fingerprint = await ClientFingerprint.from_request(request)

    start_time = time.perf_counter()

    logger.info(
        f'ID={request_id} | Inbound HTTP request ({request.method}) '
        f'- {request.url} from {fingerprint.ip_address}'
    )

    response: Response = await call_next(request)

    elapsed = time.perf_counter() - start_time

    logger.info(
        f'ID={request_id} | Outbound HTTP response ({response.status_code}) '
        f'- {request.url} from {fingerprint.ip_address} '
        f'in {elapsed:.2f} seconds'
    )

    response.headers['X-Request-ID'] = request_id

    return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app, dispatch=request_logging_middleware)
