from datetime import datetime

from typing import Any, Self, TypeVar
from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    """used in the custom base model as the "alias generator"
    meaning, the model will accept a camel case field name and
    also the python snake case field name
    Arguments:
        string {str} -- the string to convert to camel case
    Returns:
        str -- the string in camel case
    """
    words = string.split("_")
    new_name = []
    for i, word in enumerate(words):
        if i:
            new_name.append(word.capitalize())
        else:
            new_name.append(word.lower())

    return "".join(new_name).replace("Id", "ID")


def datetime_string(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


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
        alias_generator=to_camel,
        json_encoders={datetime: datetime_string},
    )

    @classmethod
    def convert(cls, obj_in: Any) -> Self:
        """converts the input object to the model class
        Returns:
            Self -- the type of the inheriting class
        """
        return cls.model_validate(obj=obj_in, from_attributes=True)

    def serialize(self) -> dict:
        """the standard arguments for .model_dump()
        to generalize behaviors across all models.
        Returns:
            dict - the dictionary representation of
            the model
        """
        return self.model_dump(exclude_unset=True, exclude_none=True)

    def serialize_exclude(self, exclude: set[str]) -> dict:
        return self.model_dump(exclude_unset=True, exclude_none=True, exclude=exclude)


SchemaT = TypeVar("SchemaT", bound=CustomBaseModel)

class RequestSchema(CustomBaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True
    )


class ResponseSchema(CustomBaseModel):
    pass