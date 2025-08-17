import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.infrastructure import log
from app.infrastructure.security.fingerprint import (
    RequestFingerprint,
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs incoming requests and responses.

    Side effects
        - Adds a `fingerprint` attribute to `request.state`
        - On class instantiation, registers a logger in the JSON log registry.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        correlation_id_header: str,
        logger_name: str = 'access',
        ip_header: str = 'X-Forwarded-For',
    ) -> None:
        super().__init__(app)
        self.logger_name: str = logger_name
        self.ip_header: str = ip_header
        self.correlation_id_header: str = correlation_id_header
        log.get_json_registry().register(self.logger_name, 'INFO')

    @property
    def access_logger(self):
        return log.get_json_logger(self.logger_name)

    def _access_message(
        self,
        request: Request,
        fingerprint: RequestFingerprint,
        id: str
    ) -> str:
        return (
            f'{id} | Incoming {request.method} request to '
            f'{fingerprint.request_path} from {fingerprint.ip.ip_address}'
        )

    def _response_message(
        self,
        response: Response,
        request_id: str,
        elapsed: float,
    ) -> str:
        return (
            f'The API responsed to request {request_id} in '
            f'{elapsed:.3f}s with a HTTP '
            f'{response.status_code} to the client.'
        )

    def _get_request_id(self, request: Request) -> str:
        """
        Extracts the request ID from the request headers.
        If not found, returns 'unknown'.
        """
        return request.headers.get(self.correlation_id_header, 'unknown')

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Logs incoming requests and outgoing responses with relevant details
        for monitoring and debugging.

        Side effects
            - Adds a `fingerprint` attribute to `request.state`

        Parameters
        ----------
        request : Request
        call_next : Callable[[Request], Awaitable[Response]]

        Returns
        -------
        Response
        """

        response_time = time.perf_counter()
        request.state.fingerprint = await RequestFingerprint.parse_request(
            request, ip_header=self.ip_header
        )
        self.access_logger.info(
            self._access_message(
                request,
                request.state.fingerprint,
                id=self._get_request_id(request),
            ),
            method=request.method,
            ip_address=request.state.fingerprint.ip.ip_address,
            user_agent=request.state.fingerprint.ip.ip_address.__repr__(),
            path=str(request.url),
            body=request.body(),
            query_params=request.query_params,
            headers=dict(request.headers),
        )

        response: Response = await call_next(request)
        response_time = time.perf_counter() - response_time

        self.access_logger.info(
            self._response_message(
                response,
                request_id=self._get_request_id(request),
                elapsed=response_time,
            ),
            status_code=response.status_code,
            response_time=response_time,
            headers=dict(response.headers),
            body=response.body,
            okay=response.status_code < 400,
        )

        return response
