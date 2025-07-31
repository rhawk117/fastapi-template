from fastapi_template.api.exceptions import (
    BaseHTTPException,
    HTTPForbidden,
    HTTPNotFound,
    HTTPUnauthorized,
)


class UserNotFound(HTTPNotFound):
    """404 Not Found"""

    def __init__(self) -> None:
        super().__init__('User')


class UsernameTaken(BaseHTTPException):
    """422 - When the username is already taken"""

    def __init__(self) -> None:
        super().__init__(
            detail='Username is already taken',
            status_code=422,
        )


class RoleNotAllowed(HTTPForbidden):
    """when a user tries to perform an action they do not have permissions for"""

    def __init__(self) -> None:
        super().__init__(
            'You do not have the required permissions to perform this action'
        )


class UserSessionInvalid(HTTPUnauthorized):
    def __init__(self) -> None:
        super().__init__(
            'The user this session corresponds to either does'
            ' not exist or did not authorize this session'
        )
