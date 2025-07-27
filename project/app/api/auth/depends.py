from typing import Annotated

from app.core.security.oauth_bearer import SessionIdDep
from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials

from .exceptions import HTTPInvalidSession, HTTPSessionRequired
from .schema import ClientFingerprint, SessionData
from .service import SessionService
from .session_store import SessionKeyStore


async def get_client_id(request: Request) -> ClientFingerprint:
    return await ClientFingerprint.from_request(request)


FingerprintDep = Annotated[ClientFingerprint, Depends(get_client_id)]


async def get_session_service() -> SessionService:
    key_store = SessionKeyStore()
    return SessionService(session_store=key_store)


SessionServiceDep = Annotated[SessionService, Depends(get_session_service)]


async def validate_user_session(
    session_id: HTTPAuthorizationCredentials | None,
    client: FingerprintDep,
    session_service: SessionServiceDep,
) -> SessionData:
    """
    The logic / middleware for authentication returning
    the validated authentication context.


    Parameters
    ----------
    session_id : HTTPAuthorizationCredentials | None
    client : FingerprintDep
    session_service : SessionServiceDep

    Returns
    -------
    SessionData

    Raises
    ------
    HTTPSessionRequired - 401
    HTTPInvalidSession - 403
    """

    if not session_id or not session_id.credentials:
        raise HTTPSessionRequired()

    api_key = session_id.credentials  # the 'Authorization' header
    key_data = await session_service.load_session(api_key, client)
    if not key_data:
        raise HTTPInvalidSession()
    return key_data


async def get_session_data(
    client: FingerprintDep,
    key: SessionIdDep,
    session_service: SessionServiceDep
) -> SessionData:
    """
    ### API Authentication

    Gets the api key from the Authorization header and checks if the key is valid,
    exists in Redis, hasn't been highjacked and hasn't reached the max key age and
    returns the key data if valid. If the key is invalid or missing, raises an
    HTTPInvalidSession exception. If the key is missing, raises an HTTPSessionRequired
    exception.

    Arguments:
        - **client {ClientFingerprintDep}**  the identity of the client making the
           request
        - **key {OAuthKeySecurity}**  the security OAuth model dependency
        - **session_service {SessionServiceDep}**  the key service dependency

    Raises:
        - **HTTPSessionRequired**: The api key is required but not provided
        - **HTTPInvalidSession**: The api key is invalid or has expired or has been
            revoked
    Returns:
        - SessionData -- the payload of the api key if valid
    """
    return await validate_user_session(key, client, session_service)


AuthenticationDep = Annotated[SessionData, Security(get_session_data)]
