from abc import ABC
from typing import Generic

from sqlalchemy.ext.asyncio import AsyncSession

from .model_repository import ModelRepository, ModelT


class DatabaseService(ABC, Generic[ModelT]):
    """The base service class for all services that interact with a model
    in the database. It provides a repository to directly interface with the model

    Attributes:
        models {ModelRepository[ModelT]} -- the repository of the model the service acts
        on.
    """

    def __init__(self, model: type[ModelT], db: AsyncSession) -> None:
        self.models: ModelRepository[ModelT] = ModelRepository(model, db)
