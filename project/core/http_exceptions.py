from http import HTTPStatus
from typing import Any

from fastapi import HTTPException, status


class BaseHTTPException(HTTPException):
    def __init__(
        self,
        *,
        status_code: int,
        detail: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(status_code, detail, headers)


class HTTPNotFound(BaseHTTPException):
    def __init__(self, resource: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource '{resource}' not found.",
            headers={'X-Error': 'ResourceNotFound'},
        )


class HTTPBadRequest(BaseHTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers={'X-Error': 'BadRequest'},
        )


class HTTPUnauthorized(BaseHTTPException):
    def __init__(
        self, detail: str = 'Unauthorized access', headers: dict | None = None
    ) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers or {'X-Error': HTTPStatus.UNAUTHORIZED.phrase},
        )


class HTTPForbidden(BaseHTTPException):
    def __init__(self, detail: str, headers: dict | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers or {'X-Error': HTTPStatus.FORBIDDEN.phrase},
        )
