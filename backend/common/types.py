from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Annotated, Literal, NamedTuple, TypeAlias

from fastapi import Path, Request, Response
from pydantic.types import PositiveInt, StringConstraints
from sqlalchemy import Select

PathID = Annotated[int, Path(..., description='The id of model.', gt=0)]

AlphaString = Annotated[
    str, StringConstraints(min_length=1, max_length=128, pattern=r'^\w+$')
]

PositiveNumber = Annotated[int, PositiveInt]
FixedLengthString = Annotated[str, StringConstraints(min_length=1, max_length=255)]

CallNext: TypeAlias = Callable[[Request], Awaitable[Response]]

LogLevelNames: TypeAlias = Literal[
    'TRACE', 'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'
]
LogLevelInt: TypeAlias = Literal[0, 10, 20, 30, 40, 50]


class SortOrder(StrEnum):
    ASC = 'asc'
    DESC = 'desc'


class PreparedStatements(NamedTuple):
    query: Select
    count: Select
