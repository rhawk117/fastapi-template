from datetime import datetime
from enum import StrEnum
from typing import Annotated

from app.api.auth.schema import SessionHealth
from pydantic import EmailStr, Field
from pydantic.types import PositiveInt

from backend.common.schemas import (
    PagedResponse,
    PageParams,
    RequestSchema,
    ResponseSchema,
    SortOrderParams,
    TimeStampParams,
)
from backend.common.types import AlphaString
from backend.core.security.rbac import Role


class UserModel(ResponseSchema):
    id: Annotated[PositiveInt, Field(..., description='The ID of the user')]
    email: Annotated[EmailStr, Field(..., description='The email of the user')]
    username: Annotated[AlphaString, Field(..., description='The username of the user')]
    role: Annotated[Role, Field(..., description='The role of the user')]


class UserAuthModel(UserModel):
    password_hash: Annotated[
        str,
        Field(..., description='The hashed password of the user')
    ]


class UserDetailsModel(ResponseSchema):
    id: Annotated[PositiveInt, Field(..., description='The ID of the user')]
    username: Annotated[AlphaString, Field(..., description='The username of the user')]
    role: Annotated[Role, Field(..., description='The role of the user')]
    created_at: Annotated[
        datetime, Field(..., description='The date the user was created')
    ]
    updated_at: Annotated[
        datetime, Field(..., description='The date the user was last updated')
    ]


class UserCreateModel(RequestSchema):
    email: Annotated[EmailStr, Field(..., description='The email of the user')]
    username: Annotated[AlphaString, Field(..., description='The username of the user')]
    password: Annotated[AlphaString, Field(..., description='The password of the user')]


class UserUpdateModel(RequestSchema):
    username: Annotated[str | None, Field(None)] = None
    password: Annotated[str | None, Field(None)] = None
    role: Annotated[Role | None, Field(None)] = None


class SessionContext(ResponseSchema):
    user: Annotated[UserModel, Field(..., description='The user object')]
    session_id: Annotated[str, Field(..., description='The API key object')]
    health: Annotated[
        SessionHealth, Field(..., description='The authentication object')
    ]


class UserSortTypes(StrEnum):
    USERNAME = 'username'
    EMAIL = 'email'


UserSort = Annotated[
    UserSortTypes,
    Field(
        default=UserSortTypes.USERNAME,
        description='The field to sort the users by',
    ),
]

class UserQueryParams(PageParams, SortOrderParams):
    sort_by: UserSort


class UserDetailsQueryParams(UserQueryParams, TimeStampParams):
    pass


class UserPage(PagedResponse[UserModel]):
    pass


class UserDetailsPage(PagedResponse[UserDetailsModel]):
    pass
