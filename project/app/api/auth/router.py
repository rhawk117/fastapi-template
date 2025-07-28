import logging
from typing import Annotated

from app.api.users.service import UserService
from app.common.http_exceptions import HTTPForbidden
from app.db.depends import DatabaseDepends
from app.utils.openapi_extra import ErrorDoc, ResponseList
from fastapi import APIRouter, Body, status

from .depends import FingerprintDep, SessionIdDep, SessionServiceDep
from .exceptions import HTTPInvalidCredentials
from .schema import (
    LoginBody,
    LogoutResponse,
    SessionIdentity,
    SessionInfo,
    SessionResponse,
)

auth_logger = logging.getLogger('security.auth')
auth_router = APIRouter()


@auth_router.post(
    '/login',
    response_model=SessionResponse,
    responses=ErrorDoc(
        'When the user provides invalid credentials',
        status.HTTP_401_UNAUTHORIZED
    ),
)
async def login_user(
    auth_form: Annotated[LoginBody, Body(...)],
    session_service: SessionServiceDep,
    client: FingerprintDep,
    db: DatabaseDepends,
) -> SessionResponse:
    """
    Checks the credentials provided by the `auth_form` or login body
    and in the response sets a cookie with the session id when given
    valid login credentials.

    Parameters
    ----------
    auth_form : Annotated[LoginBody, Body
    session_service : SessionServiceDep
    client : FingerprintDep
    db : DatabaseDepends

    Returns
    -------
    SessionResponse

    Raises
    ------
    HTTPInvalidCredentials
    """
    user_service = UserService(db)
    verified_user = await user_service.authenticate(auth_form)
    if not verified_user:
        auth_logger.warning(f'Failed login attempt on user {auth_form.username}')
        raise HTTPInvalidCredentials()

    session_id = await session_service.assign_session(
        username=verified_user.username, role=str(verified_user.role), client=client
    )

    auth_logger.info(
        f'User {verified_user.username} logged in with role {verified_user.role}'
    )

    session_identity = SessionIdentity(
        username=verified_user.username,
        role=str(verified_user.role)
    )

    return SessionResponse(
        session_id=session_id,
        identity=session_identity
    )


@auth_router.post(
    '/logout',
    response_model=LogoutResponse,
    responses=ResponseList(
        [
            ErrorDoc(
                'When the user tries to log out without a valid session',
                status.HTTP_403_FORBIDDEN,
            ),
            ErrorDoc(
                'When the user tries to log out with an invalid session',
                status.HTTP_401_UNAUTHORIZED,
            ),
        ]
    ),
)
async def logout_user(
    session_auth: SessionIdDep, session_service: SessionServiceDep
) -> LogoutResponse:
    """
    Logs out the user using the _"Session ID" dependency_

    - Load the clients signed session ID from the Authorization header

    - Attempts to revoke the session by deleting it from the Redis store

    - if the session key hasn't been tampered with by the user and is valid the
    session is revoked by deleting the key in the Redis store mapped to the session ID


    Parameters
    ----------
    session_auth : SessionIdDep
    session_service : SessionServiceDep

    Returns
    -------
    LogoutResponse

    Raises
    ------
    HTTPForbidden - Invalid or expired session
    """
    if not session_auth or not session_auth.credentials:
        raise HTTPForbidden('Invalid or expired session.')
    try:
        await session_service.revoke(session_auth.credentials)
    except Exception:
        pass

    auth_logger.info(f'User with API key {session_auth.credentials} logged out')

    return LogoutResponse()


@auth_router.get(
    '/session',
    response_model=SessionInfo,
    responses=ResponseList(
        [
            ErrorDoc(
                'When the user tries to log out without a valid session',
                status.HTTP_403_FORBIDDEN,
            ),
            ErrorDoc(
                'When the user tries to log out with an invalid session',
                status.HTTP_401_UNAUTHORIZED,
            ),
        ]
    ),
)
async def get_session_status(
    session_auth: SessionIdDep,
    session_service: SessionServiceDep
) -> SessionInfo:
    """Returns the session information for the current user

    Args:
        session_auth (SessionIdDep): _the session id_
        session_service (SessionServiceDep): _the session service_

    Raises:
        HTTPForbidden: _invalid or expired session_

    Returns:
        SessionInfo: _the session data_
    """
    if not session_auth or not session_auth.credentials:
        raise HTTPForbidden('Invalid or expired Session')

    key_info = await session_service.get_session_health(
        signed_key=session_auth.credentials
    )

    if not key_info:
        raise HTTPForbidden('Invalid or expired Session.')

    return key_info
