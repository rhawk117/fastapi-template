from fastapi import HTTPException, status

# Custom HTTP Exceptions & Shorthands


class BaseHTTPError(HTTPException):
    """base class for api errors to allow for the { details: "" } section to be a custom response
    for the frontend type safety
    """

    def __init__(
        self, status_code: int, details: str, headers: dict | None = None
    ) -> None:
        headers = headers or {}
        self.data = details
        super().__init__(status_code=status_code, detail=details, headers=headers)


class HTTPNotFound(BaseHTTPError):
    """Raises a 404 Not Found HTTPException - HTTPErrorLabel.NOT_FOUND"""

    def __init__(self, resource_name: str, custom_msg: str | None = None) -> None:
        message = custom_msg or f'{resource_name} not found'
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            details=message,
        )


class HTTPUnauthorized(BaseHTTPError):
    """Raises a 401 Unauthorized HTTPException - HTTPErrorLabel.INVALID_PERMISSIONS"""

    def __init__(self, msg: str | None = None, headers: dict | None = None) -> None:
        headers = headers or {}
        if not msg:
            msg = 'You are not authorized to access this resource'
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=msg,
            headers=headers,
        )


class HTTPForbidden(BaseHTTPError):
    """Raises a 403 Forbidden HTTPException"""

    def __init__(self, msg: str | None, headers: dict | None = None) -> None:
        msg_default = 'You have not been granted access to this resource'
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            details=msg or msg_default,
            headers=headers or {},
        )


class HTTPBadRequest(BaseHTTPError):
    """When the client sends a bad request, raises a 400 HTTPException - HTTPErrorLabel.BAD_REQUEST"""

    def __init__(self, msg: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            details=msg,
        )


class HTTPBadRequestData(BaseHTTPError):
    """When a validation error occurs in a pydantic model, raises a 400 HTTPException - HTTPErrorLabel.INVALID_DATA"""

    def __init__(self, msg: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            details=msg,
        )
