from datetime import datetime
from typing import Any, Self, TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict


def to_camel_case(string: str) -> str:
    """
    used in the custom base model as the "alias generator"
    meaning, the model will accept a camel case field name and
    also the python snake case field name
    """
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
    """The base model for all app models allowing for standard serialization
    and deserialization of ambiguous types such as datetime, globally allow
    camel case in the body of requests and responses and also allows for
    the use of enums as values in the models
    """

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        validate_assignment=True,
        from_attributes=True,
        alias_generator=to_camel_case,
        str_strip_whitespace=True,
        json_encoders={datetime: datetime_string},
    )

    @classmethod
    def convert(cls, obj_in: Any) -> Self:
        return cls.model_validate(obj=obj_in, from_attributes=True)

    def dump(self) -> dict:
        """
        utility `.model_dump()` method to generalize behaviors across
        all models.
        Sets `exclude_unset=True` and `exclude_none=True`

        Returns
        -------
        dict
        """
        return self.model_dump(exclude_unset=True, exclude_none=True)

    def dump_exclude(self, exclude: set[str]) -> dict:
        return self.model_dump(exclude_unset=True, exclude_none=True, exclude=exclude)

    def serialize(
        self,
        *,
        exclude_unset: bool = True,
        exclude_none: bool = True,
        by_alias: bool = True,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
    ) -> dict:
        """
        Uses FastAPI's `jsonable_encoder` to serialize the model
        """
        return jsonable_encoder(
            self,
            exclude_unset=exclude_unset,
            exclude_none=exclude_none,
            by_alias=by_alias,
            include=include,
            exclude=exclude,
        )


SchemaT = TypeVar('SchemaT', bound=CustomBaseModel)
