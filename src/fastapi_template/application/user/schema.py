from datetime import datetime

from pydantic import EmailStr

from fastapi_template.core.annotations import AlphaString
from fastapi_template.core.pydantic import CustomBaseModel
from fastapi_template.domain.models.users import UserRole


class PublicUserModel(CustomBaseModel):
    id: str
    email: str
    username: AlphaString
    role: UserRole


class PrivateUserModel(PublicUserModel):
    created_at: datetime
    updated_at: datetime


class CreateUserModel(CustomBaseModel):
    email: str
    username: AlphaString
    password: AlphaString


class UpdateUserModel(CustomBaseModel):
    username: AlphaString | None = None
    password: AlphaString | None = None
    email: EmailStr | None = None
    role: UserRole | None = None
