from datetime import datetime

from fastapi import Query
from pydantic import EmailStr, Field

from app.core.pydantic import HTTPModel
from app.core.typing import AlphaString
from app.domains.query_mixin import PageMixin, PageParamsMixin

_USERNAME_DESC = 'Username of the user, must be unique and alphanumeric'
_PASSWORD_DESC = 'Password of the user, must be at least 8 characters long'
_EMAIL_DESC = 'Email of the user, must be unique and valid'
_ROLE_NAME_DESC = 'Role name of the user, must be one of the predefined roles'
_CREATED_AT_DESC = 'Creation timestamp of the user'
_UPDATED_AT_DESC = 'Last update timestamp of the user'


class UserResponse(HTTPModel):
    """
    Response model for user details.
    """

    id: str
    username: AlphaString = Field(
        ..., description=_USERNAME_DESC, min_length=3, max_length=50
    )
    email: EmailStr = Field(..., description=_EMAIL_DESC, max_length=255, min_length=5)
    role: AlphaString = Field(..., description=_ROLE_NAME_DESC, max_length=50)


class AuditedUser(UserResponse):
    """
    Response model for audited user details.
    """

    created_at: datetime = Field(..., description=_CREATED_AT_DESC)
    updated_at: datetime = Field(..., description=_UPDATED_AT_DESC)


class UserPage(PageMixin[UserResponse]): ...


class RegisterUser(HTTPModel):
    username: AlphaString = Field(
        ..., description=_USERNAME_DESC, min_length=3, max_length=50
    )
    email: EmailStr = Field(..., description=_EMAIL_DESC, max_length=255, min_length=5)
    password: str = Field(..., description=_PASSWORD_DESC, min_length=8)


class UserCreate(RegisterUser):
    role_name: AlphaString = Field(..., description=_ROLE_NAME_DESC, max_length=50)


class UserUpdate(HTTPModel):
    """
    Request model for updating user details.
    """

    username: AlphaString | None = Field(
        None, description=_USERNAME_DESC, min_length=3, max_length=50
    )
    email: EmailStr | None = Field(
        None, description=_EMAIL_DESC, max_length=255, min_length=5
    )
    role_name: AlphaString | None = Field(
        None, description=_ROLE_NAME_DESC, max_length=50
    )
    password: str | None = Field(None, description=_PASSWORD_DESC, min_length=8)


class UserQueryCommand(HTTPModel, PageParamsMixin):
    username: AlphaString | None = Query(
        None,
        description='Filter by username, must be alphanumeric',
    )
    active_only: bool = Query(
        False,
        description='Filter to include only active users',
    )
    reader_role_level: int = Query(
        ...,
        description='The role level of the reader, used to filter users based on their roles',
    )
