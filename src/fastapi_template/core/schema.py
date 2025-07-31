from datetime import datetime
from typing import Annotated

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict
from pydantic.types import StringConstraints


def to_camel(string: str) -> str:
    words = string.split('_')
    new_name = []
    for i, word in enumerate(words):
        if i:
            new_name.append(word.capitalize())
        else:
            new_name.append(word.lower())

    return ''.join(new_name).replace('Id', 'ID')


def datetime_string(dt: datetime) -> str:
    return dt.strftime('%Y-%m-%d %H:%M')


class CustomBaseModel(BaseModel):
    """
    The Pydantic base model for all app models allowing for standard serialization
    and deserialization of ambiguous types such as datetime, globally allow
    camel case in the body of requests and responses and also allows for
    the use of enums as values in the models
    """

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        validate_assignment=True,
        from_attributes=True,
        alias_generator=to_camel,
        json_encoders={datetime: datetime_string},
    )

    def serialize(
        self,
        *,
        exclude_none: bool = True,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        by_alias: bool = True,
        exclude: set[str] | None = None,
    ) -> dict:
        dumped = self.model_dump()
        return jsonable_encoder(
            dumped,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            by_alias=by_alias,
            exclude=exclude,
        )


AlphaString = Annotated[
    str, StringConstraints(min_length=1, max_length=128, pattern=r'^\w+$')
]

FixedLengthString = Annotated[str, StringConstraints(min_length=1, max_length=255)]
