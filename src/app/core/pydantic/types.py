from typing import Annotated

from pydantic.types import StringConstraints
from pydantic import Field


ALPHA_NUMERIC_PATTERN = r'^[a-zA-Z0-9]+$'

AlphaString = Annotated[
    str,
    Field(
        description='A string contain7ing only alphanumeric characters',
        min_length=1,
        pattern=ALPHA_NUMERIC_PATTERN,
    ),
]


SmallString = Annotated[
    str,
    Field(
        description='A small string, (max 64 characters)',
        min_length=1,
        max_length=64,
    ),
]
MediumString = Annotated[
    str,
    Field(
        description='A medium string, (max 128 characters)',
        min_length=1,
        max_length=128,
    ),
]
LargeString = Annotated[
    str,
    Field(
        description='A large string, used for longer text fields (max 256 characters)',
        min_length=1,
        max_length=256,
    ),
]
