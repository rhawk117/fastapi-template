from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal, TypeAlias

from fastapi import Path, Request, Response
from pydantic import Field
from pydantic.types import PositiveInt, StringConstraints, 

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

