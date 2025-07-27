from typing import Annotated

from app.api.auth.depends import (
    AuthenticationDep,
    FingerprintDep,
    SessionData,
    SessionIdDep,
    SessionServiceDep,
    validate_user_session,
)
from app.db.depends import DatabaseDepends
from fastapi import Depends, Security

from .exceptions import RoleNotAllowed, UserSessionInvalid
from .model import Role, User
from .schema import SessionContext
from .service import UserService


async def get_user_service(db: DatabaseDepends) -> UserService:
    """creates the user service with the DB dependency

    Arguments:
        db {DatabaseDepends} -- the DB dependency

    Returns:
        UserService -- the user service
    """
    return UserService(db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


async def session_id_to_user(
    session_data: SessionData, user_service: UserService
) -> User:
    """Converts the SessionData into an AuthenticationDep object
    which is used to authenticate the user

    Arguments:
        session_data {SessionData} -- the SessionData object
        user_service {UserServiceDep} -- the user controller
    Returns:
        AuthenticationDep -- the authentication dependency
    """
    existing_user = await user_service.select_username(session_data.identity.username)
    if not existing_user:
        raise UserSessionInvalid()
    return existing_user


async def get_current_user(
    session_data: AuthenticationDep, user_service: UserServiceDep
) -> User:
    """Retrieves the current user from the database and performs
    sanity checks to ensure the user is valid and still exists"""
    return await session_id_to_user(session_data, user_service)


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_auth_context(
    client: FingerprintDep,
    session_auth: SessionIdDep,
    user_service: UserServiceDep,
    session_service: SessionServiceDep,
) -> SessionContext:
    """runs all of the logic for authentication with both the auth dependency
    function running and user function to ensure the user still exists and uses key
    service to get the keys health.

    contains alot of dependencies to ensure that only one of each instance such
    as a database session is created upon each request, however has the downside of being

    Returns:
        AuthContext -- the associated user and meta data for the api key
    """
    session_payload = await validate_user_session(
        session_id=session_auth, client=client, session_service=session_service
    )

    user = await session_id_to_user(session_payload, user_service)

    session_id = session_auth.credentials

    session_health = await session_service.inspect_session_health(
        session_payload=session_payload, signed_key=session_id
    )
    return SessionContext(
        user=user_service.to_response(user),
        health=session_health,
        session_id=session_id,
    )


SessionContextDep = Annotated[SessionContext, Depends(get_auth_context)]


def role_checker(min_role: Role):
    """returns a factory function that checks if the current user's role
    is greater than or equal to the minimum role required
    Arguments:
        min_role {Role} -- the minimum role required to access the route
    """

    async def role_allowed(current_user: CurrentUserDep) -> User:
        if current_user.role < min_role:
            raise RoleNotAllowed()
        return current_user

    return role_allowed


RoleRequired = role_checker(Role.READ_ONLY)
UserRequired = role_checker(Role.USER)
AdminRequired = role_checker(Role.ADMIN)


AnyRoleDep = Annotated[User, Security(RoleRequired)]
UserRoleDep = Annotated[User, Security(UserRequired)]
AdminRoleDep = Annotated[User, Security(AdminRequired)]
