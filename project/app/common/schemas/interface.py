from datetime import datetime
from typing import Annotated, Any, Generic, Self, TypeVar

from pydantic import BaseModel, ConfigDict, Field


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

    @classmethod
    def convert(cls, obj_in: Any) -> Self:
        """
        `.model_validate()` with `from_attributes=True`

        Parameters
        ----------
        obj_in : Any

        Returns
        -------
        Self
        """
        return cls.model_validate(obj=obj_in, from_attributes=True)

    def dump(self) -> dict:
        """
        `.model_dump()` with `exclude_unset=True` and `exclude_none=True`

        Returns
        -------
        dict
        """
        return self.model_dump(exclude_unset=True, exclude_none=True)

    def dump_exclude(self, exclude: set[str]) -> dict:
        """
        `.model_dump()` with `exclude_unset=True`, `exclude_none=True` and
        `exclude=exclude`

        Parameters
        ----------
        exclude : set[str]

        Returns
        -------
        dict
        """
        return self.model_dump(
            exclude_unset=True,
            exclude_none=True,
            exclude=exclude
        )


