from typing import Annotated

from fastapi import APIRouter, Body, Query, status

from app.domains.users.schemas import (
    UserCreate,
    UserPage,
    UserQueryCommand,
    UserResponse,
    UserUpdate,
)

from ..annotations import PathUUID
from ..depends import UserServiceDepends
from ..openapi_extra import HTTPError

users_router = APIRouter()


@users_router.post(
    '/',
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: HTTPError(
            'Invalid user name or email not unique.'
        ),
        status.HTTP_404_NOT_FOUND: HTTPError('User not found.'),
    },
)
async def create_user(
    *,
    user: UserCreate,
    user_service: UserServiceDepends
) -> UserResponse:
    """
    Create a new user.
    """
    return await user_service.create_user(user)


@users_router.get(
    '/{user_id}',
    response_model=UserResponse,
    responses={
        status.HTTP_404_NOT_FOUND: HTTPError('User not found.'),
    },
)
async def get_user(
    *,
    user_id: PathUUID,
    user_service: UserServiceDepends
) -> UserResponse:
    """
    Retrieve a user by their ID.
    """
    return await user_service.get_user_by_id(user_id)


@users_router.patch(
    '/{user_id}',
    response_model=UserResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: HTTPError(
            'Invalid user name or email not unique.'
        ),
        status.HTTP_404_NOT_FOUND: HTTPError('User not found.'),
    },
)
async def update_user(
    *,
    user_id: PathUUID,
    user_update: Annotated[UserUpdate, Body()],
    user_service: UserServiceDepends,
) -> UserResponse:
    """
    Update an existing user by their ID.
    """
    return await user_service.update_user(user_id, user_update)


@users_router.delete(
    '/{user_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: HTTPError('User not found.'),
    },
)
async def delete_user(
    *,
    user_id: PathUUID,
    user_service: UserServiceDepends
) -> None:
    """
    Delete a user by their ID.
    """
    await user_service.delete_user(user_id)



@users_router.get(
    '/',
    response_model=UserPage,
    responses={
        status.HTTP_404_NOT_FOUND: HTTPError('No users found.'),
    },
)
async def list_users(
    *,
    query: Annotated[UserQueryCommand, Query(...)],
    user_service: UserServiceDepends
) -> UserPage:
    """
    List users with pagination and filtering.
    """
    return await user_service.list_users(query)