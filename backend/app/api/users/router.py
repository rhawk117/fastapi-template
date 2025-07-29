from typing import Annotated

from fastapi import APIRouter, Body, Depends, status

from backend.common.http_exceptions import HTTPForbidden, HTTPNotFound
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
from .exceptions import UsernameTaken, UserNotFound
from .schema import (
    SessionContext,
    UserCreateBody,
    UserDetailsListResponse,
    UserDetailsResponse,
    UserListResponse,
    UserResponse,
    UserUpdateBody,
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


@user_router.get('/', response_model=UserListResponse)
async def get_all_users(
    user_service: UserServiceDep, reader: CurrentUserDep
) -> UserListResponse:
    """reads all users based on the role of the reader (no read up)
    Arguments:
        user_service {UserServiceDep} -- the service dep
        reader {CurrentUser} -- the current user

    Returns:
        list[UserResponse] -- all of the users based on the readers role
    """
    response = await user_service.role_based_read_all(reader)
    return response


# /


@user_router.post(
    '/',
    response_model=UserResponse,
    dependencies=[Depends(AdminRequired)],
    status_code=status.HTTP_201_CREATED,
    responses=ErrorDoc('The username is already taken', 400),
)
async def create_new_user(
    create_req: Annotated[UserCreateBody, Body(...)], user_service: UserServiceDep
) -> UserResponse:
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
    username_taken = await user_service.select_username(create_req.username)  # type: ignore
    if username_taken:
        raise UsernameTaken()

    new_user = await user_service.create_user(create_req)
    return user_service.to_response(new_user)


# /details
@user_router.get(
    '/details',
    dependencies=[Depends(AdminRequired)],
    response_model=UserDetailsListResponse,
)
async def get_all_user_details(user_service: UserServiceDep) -> UserDetailsListResponse:
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
    all_users = await user_service.models.select_all()
    return UserDetailsListResponse.from_results(
        [UserDetailsResponse.convert(user) for user in all_users]
    )


# /details/{user_id}
@user_router.get(
    '/details/{user_id}/',
    dependencies=[Depends(AdminRequired)],
    response_model=UserDetailsResponse,
    responses=NotFound('user'),
)
async def get_user_id_details(
    user_id: PathID, user_service: UserServiceDep
) -> UserDetailsResponse:
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

    user = await user_service.get_by_id(user_id)
    if not user:
        raise UserNotFound()
    return UserDetailsResponse.convert(user)


# /{user_id}/ - Read, Update, Delete
@user_router.patch(
    '/{user_id}/',
    response_model=UserResponse,
    dependencies=[Depends(AdminRequired)],
    status_code=status.HTTP_202_ACCEPTED,
    responses=ResponseList(
        [ErrorDoc('The user name being updated to is taken', 400), NotFound('user')]
    ),
)
async def update_user_id(
    user_id: PathID,
    update_req: Annotated[UserUpdateBody, Body()],
    user_service: UserServiceDep,
) -> UserResponse:
    """updates the user given an id and uses the schema to update the user's data

    **Path**
        /users/{user_id}/ - the user id to update

    **Response**
        UserResponse -- the updated user
    """
    updated_data = await user_service.update_by_id(
        user_id=user_id, update_req=update_req
    )
    return UserResponse.convert(updated_data)


@user_router.delete(
    '/{user_id}/',
    response_model=MessagedResponse,
    responses=ResponseList(
        [ErrorDoc('An admin attempts to delete themselves', 403), NotFound('user')]
    ),
)
async def delete_user_id(
    user_id: PathID, user_service: UserServiceDep, admin: AdminRoleDep
) -> MessagedResponse:
    """Deletes a user given an existing user ID

    Arguments:
        user_id {int} -- the ID of the user to be deleted
        db {requires_db} -- a database session
        admin {admin_required} -- an admin user, ensures the Admin isn't deleting
        themselves
    Returns:
        ResponseMessage -- A message indicating the deletion was successful
    """
    await user_service.delete_by_id(user_id=user_id, admin_name=admin.username)
    return MessagedResponse(message='User deleted', data={'user_id': user_id})


@user_router.get('/{user_id}/', response_model=UserResponse, responses=NotFound('user'))
async def read_user_id(
    user_id: PathID, user_service: UserServiceDep, reader: CurrentUserDep
) -> UserResponse:
    """Reads a user with 'no read up' i.e a user cannot read a user with a
    higher role / permission

    Arguments:
        user_id {int} -- the id of the user to read
        db {requires_db} -- the database session
        reader {role_required} -- the "reader" or user making the request

    Raises:
        HTTPNotFound: The user does not exist
        HTTPForbidden: The user does not have permission to read the user

    Returns:
        UserResponse -- The user attempting to be read
    """
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPNotFound('User')

    if not (reader.role >= user.role):
        raise HTTPForbidden('Cannot read a user with higher permissions')

    return UserResponse.convert(user)
