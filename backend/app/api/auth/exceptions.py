from app.domains.exceptions import HTTPForbidden, HTTPUnauthorized


class HTTPInvalidCredentials(HTTPUnauthorized):
    """HTTP 401 -- Raised when the user provides invalid credentials."""

    def __init__(self) -> None:
        super().__init__('Invalid username or password, please try again.')


class HTTPSessionRequired(HTTPUnauthorized):
    """HTTP 401 -- Raised when an API key is required but not provided."""

    def __init__(self) -> None:
        super().__init__(
            detail='You must be authenticated to access this resource.',
            headers={'WWW-Authenticate': 'Key-Bearer'},
        )


class HTTPInvalidSession(HTTPForbidden):
    """HTTP 403 -- Raised when an invalid API key is provided."""

    def __init__(self) -> None:
        super().__init__(
            detail='Your session has either expired or is invalid, please log in again.',
            headers={'WWW-Authenticate': 'Key-Bearer'},
        )
