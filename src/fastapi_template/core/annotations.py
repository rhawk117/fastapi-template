from typing import Annotated

from pydantic.types import StringConstraints

AlphaString = Annotated[
    str, StringConstraints(min_length=1, max_length=128, pattern=r'^\w+$')
]

FixedLengthString = Annotated[str, StringConstraints(min_length=1, max_length=255)]


