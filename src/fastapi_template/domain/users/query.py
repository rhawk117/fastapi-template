from enum import StrEnum
from typing import Annotated

from pydantic import Field

from fastapi_template.domain.query_schema import (
    PageParams,
    SortParams,
    TimeStampParams,
)


class UserSortTypes(StrEnum):
    USERNAME = 'username'
    EMAIL = 'email'


class UserQueryParams(PageParams, SortParams):
    col: Annotated[
        UserSortTypes,
        Field(
            default=UserSortTypes.USERNAME,
            description='The field to sort the items by',
        ),
    ]


class UserDetailsQueryParams(UserQueryParams, TimeStampParams):
    pass
