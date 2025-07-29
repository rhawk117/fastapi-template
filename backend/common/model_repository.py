from collections.abc import Mapping, Sequence
from typing import Any, Generic, NamedTuple, TypeVar

from sqlalchemy import Row, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import MappedColumn
from sqlalchemy.sql.selectable import Select

ModelT = TypeVar('ModelT')


class PageResult(NamedTuple):
    result: Sequence[Mapping]
    total: int


class CRUDRepository(Generic[ModelT]):
    """
    Provides methods for common CRUD operations on database models
    and is the foundation for all services that interact with the database.
    """

    def __init__(self, model: type[ModelT], db: AsyncSession) -> None:
        self.model: type[ModelT] = model
        self.db: AsyncSession = db

    async def delete(self, db_model: ModelT) -> None:
        await self.db.delete(db_model)
        await self.db.commit()

    async def save(self, model_obj: ModelT, refresh: bool = False) -> None:
        self.db.add(model_obj)
        await self.db.commit()
        if refresh:
            await self.db.refresh(model_obj)

    async def get(self, predicate: Any) -> ModelT | None:
        query = select(self.model).where(predicate)
        result = await self.db.execute(query)
        output = result.scalars().first()
        return output

    async def filter(self, **filters: Any) -> list[ModelT]:
        query = select(self.model).filter_by(**filters)
        result = await self.db.execute(query)
        models = result.scalars().all()
        return list(models) if models else []

    async def get_all(self, predicate: Any | None = None) -> list[ModelT]:
        stmnt = select(self.model)
        if predicate is not None:
            stmnt = stmnt.where(predicate)
        result = await self.db.execute(stmnt)
        models = result.scalars().all()
        return list(models) if models else []

    async def get_one(self, statement: Select) -> Row | None:
        """
        Executes a SQLAlchemy statement and returns a single row.

        Parameters
        ----------
        statement : Select
            The SQLAlchemy select statement to execute.

        Returns
        -------
        Row | None
            The first row of the result or None if no rows are found.
        """
        result = await self.db.execute(statement)
        return result.one_or_none()

    async def create(self, obj_in: dict, *, refresh: bool = True) -> ModelT:
        db_model = self.model(**obj_in)
        await self.save(db_model, refresh=refresh)
        return db_model

    async def update(self, db_model: ModelT, obj_in: dict) -> ModelT:
        for field, value in obj_in.items():
            if hasattr(db_model, field):
                setattr(db_model, field, value)

        await self.db.commit()
        await self.db.refresh(db_model)
        return db_model

    async def select_row(self, statement: Select) -> Row | None:
        """
        Executes a SQLAlchemy statement and returns a single row.

        Parameters
        ----------
        statement : Select
            The SQLAlchemy select statement to execute.

        Returns
        -------
        Row | None
            The first row of the result or None if no rows are found.
        """
        result = await self.db.execute(statement)
        return result.one_or_none()

    async def get_mappings(self, statement: Select) -> Sequence[Mapping]:
        """
        Executes a SQLAlchemy statement and returns the result as a mapping.

        Parameters
        ----------
        statement : Select
            The SQLAlchemy select statement to execute.

        Returns
        -------
        Row | None
            The first row of the result as a mapping or None if no rows are found.
        """
        result = await self.db.execute(statement)
        return result.mappings().all()

    async def any(self, statement: Select) -> bool:
        """
        Checks if any rows match the given SQLAlchemy statement.

        Parameters
        ----------
        statement : Select
            The SQLAlchemy select statement to execute.

        Returns
        -------
        bool
            True if any rows match the statement, False otherwise.
        """
        result = await self.db.execute(statement)
        return result.scalar() is not None

    async def select_page(
        self, offset: int, limit: int, statement: Select
    ) -> PageResult:
        """
        Executes a paged query and returns the results along with the total count.

        Parameters
        ----------
        offset : int
            The offset for pagination.
        limit : int
            The limit for pagination.
        statement : Select
            The SQLAlchemy select statement to execute.

        Returns
        -------
        PagedQuery
            A PagedQuery object containing the results and total count.
        """
        paged_statement = statement.offset(offset).limit(limit)

        result = await self.get_mappings(paged_statement)

        count_statement = select(func.count()).select_from(self.model)
        count_result = await self.db.execute(count_statement)
        total_count = count_result.scalar_one_or_none()

        return PageResult(
            result=result,
            total=total_count if total_count is not None else 0,
        )

    def get_sort(self, sort_order: str, column: str) -> MappedColumn:
        """
        Returns an ordered SQLAlchemy statement based on the sort order and column.

        Parameters
        ----------
        sort_order : str
            The sort order, either 'asc' or 'desc'.
        column : str
            The column to order by.

        Returns
        -------
        MappedColumn
            The ordered SQLAlchemy column.
        """
        if sort_order == 'asc':
            return getattr(self.model, column).asc()
        elif sort_order == 'desc':
            return getattr(self.model, column).desc()
        else:
            raise ValueError(f'Invalid sort order: {sort_order}')
