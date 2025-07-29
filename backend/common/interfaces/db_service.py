from abc import ABC

from .db_repository import DatabaseRepository


class DatabaseService(ABC):
    """The base service class for all services that interact with a model
    in the database. It provides a repository to directly interface with the model

    Attributes:
        models {DatabaseRepository[ModelT]} -- the repository of the model the service
        acts on.
    """

    def __init__(self, repository: DatabaseRepository) -> None:
        self.repository: DatabaseRepository = repository
