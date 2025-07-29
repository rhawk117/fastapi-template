from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, status

from backend.common.types import PathID
from backend.utils.openapi_extra import HTTPError

from .depends import (
    AdminRequired,
    AdminRoleDep,
    CurrentUserDep,
    RoleRequired,
    SessionContextDep,
    UserServiceDep,
)
from .schema import (
    SessionContext,
    UserCreateModel,
    UserDetailsModel,
    UserDetailsPage,
    UserDetailsQueryParams,
    UserModel,
    UserPage,
    UserQueryParams,
    UserUpdateModel,
)

user_router = APIRouter(
    dependencies=[Depends(RoleRequired)],
    responses={
        status.HTTP_401_UNAUTHORIZED: HTTPError(
            'The user is not signed in or the session is invalid'
        ),
        status.HTTP_403_FORBIDDEN: HTTPError(
            'The user is not authorized to perform this action'
        ),
    },
)


@user_router.get('/me/', response_model=SessionContext)
async def get_current_user(context: SessionContextDep) -> SessionContext:
    """
    Reads the current user and returns the authentication context
    of said user using the chained dependencies, thus requiring
    no code lol

    Arguments:
        reader {CurrentUser} -- the reader

    Returns:
        UserResponse -- the current user
    """
    return context


# /
@user_router.get('/', response_model=UserPage)
async def query_all_users(
    params: Annotated[UserQueryParams, Query(...)],
    reader: CurrentUserDep,
    user_service: UserServiceDep,
) -> UserPage:
    return await user_service.query_users(reader_role=reader.role, params=params)


@user_router.post(
    '/',
    dependencies=[Depends(AdminRequired)],
    response_model=UserModel,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: HTTPError('The username or email is already taken')
    },
)
async def create_user(
    create_req: Annotated[UserCreateModel, Body(...)], user_service: UserServiceDep
) -> UserModel:
    """
    ### ADMIN PROTECTED

    Creates a user given valid form data and inserts
    the created user into the database and returns the
    created user

    Parameters
    ----------
    create_req : Annotated[UserCreateBody, Body]
    user_service : UserServiceDep

    Returns
    -------
    UserResponse

    Raises
    ------
    UsernameTaken - 400 Bad Request
    """
    return await user_service.create_user(create_req=create_req)


# /details
@user_router.get(
    '/details',
    response_model=UserDetailsPage,
)
async def query_user_details(
    params: Annotated[UserDetailsQueryParams, Query(...)],
    admin: AdminRoleDep,
    user_service: UserServiceDep,
) -> UserDetailsPage:
    """
    Admin protected route to read all of the user details, including
    the creation date and last updated timestamps

    Parameters
    ----------
    user_service : UserServiceDep

    Returns
    -------
    UserDetailsListResponse
    """
    page = await user_service.query_user_details(params=params, reader_role=admin.role)
    return page


# /details/{user_id}
@user_router.get(
    '/details/{user_id}/',
    dependencies=[Depends(AdminRequired)],
    response_model=UserDetailsModel,
    responses={status.HTTP_404_NOT_FOUND: HTTPError('The user does not exist')},
)
async def get_user_details(
    user_id: PathID, user_service: UserServiceDep
) -> UserDetailsModel:
    """
    reads the details of a single user

    Parameters
    ----------
    user_id : PathID
    user_service : UserServiceDep

    Returns
    -------
    UserDetailsResponse

    Raises
    ------
    UserNotFound
    """
    return await user_service.get_user_detail(user_id)


# /{user_id}/ - Read, Update, Delete
@user_router.patch(
    '/{user_id}/',
    response_model=UserModel,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_400_BAD_REQUEST: HTTPError('The username or email is taken')
    },
)
async def update_user(
    update_req: Annotated[UserUpdateModel, Body(...)],
    user_id: PathID,
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
) -> UserModel:
    """
    Updates the user given it's ID
    """
    updated_user = await user_service.update_user(
        user_id=user_id,
        update_req=update_req,
        current_user_id=current_user.id,
        current_user_role=current_user.role,
    )
    return updated_user


@user_router.delete(
    '/{user_id}/',
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: HTTPError('The user does not exist'),
        status.HTTP_403_FORBIDDEN: HTTPError('An admin cannot delete themselves'),
    },
)
async def delete_user(
    user_id: PathID, user_service: UserServiceDep, admin: AdminRoleDep
) -> None:
    """
    Deletes a user given it's ID

    Parameters
    ----------
    user_id : PathID
        _the ID of the user to delete_


    Raises
    ------
    HTTPNotFound
    HTTPForbidden
    """
    await user_service.delete_user(user_id=user_id, admin_name=admin.username)


@user_router.get(
    '/{user_id}/',
    response_model=UserModel,
    responses={status.HTTP_404_NOT_FOUND: HTTPError('The user does not exist')},
)
async def get_user(
    user_id: PathID, user_service: UserServiceDep, reader: CurrentUserDep
) -> UserModel:
    return await user_service.get_user(user_id=user_id, current_user_role=reader.role)
