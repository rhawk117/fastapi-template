from enum import StrEnum
from typing import Annotated

from pydantic import Field

from backend.common.schemas import (
    PageParams,
    SortOrderParams,
    TimeStampParams,
)


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
