from collections.abc import Mapping
from typing import Any, Generic, TypedDict, TypeVar

from pydantic import BaseModel
from sqlalchemy import Result, ScalarResult, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import TypedReturnsRows

M = TypeVar('M')
# S = TypeVar('S', bound=BaseModel)


class SqlPageResult(TypedDict, Generic[M]):
    models: list[M]
    total: int
    page: int
    page_size: int


class SqlRepository(Generic[M]):
    """
    CRUD Repository wrapper with common operations for SQLAlchemy models
    and an async session.
    """

    def __init__(self, session: AsyncSession, model: type[M]) -> None:
        self._session: AsyncSession = session
        self.model: type[M] = model

    async def create(self, model_init: Mapping[str, Any], *, commit: bool = True) -> M:
        instance = self.model(**model_init)
        self._session.add(instance)

        if commit:
            await self._session.commit()

        return instance

    async def delete(self, model: M, *, commit: bool = True) -> bool:
        try:
            await self._session.delete(model)
        except Exception:
            return False

        if commit:
            await self._session.commit()

        return True

    async def update(
        self,
        model: M,
        model_init: Mapping[str, Any],
        *,
        commit: bool = True,
        refresh: bool = True,
    ) -> M:
        for key, value in model_init.items():
            setattr(model, key, value)

        self._session.add(model)

        await self.sync(commit=commit, refresh=refresh)

        return model

    async def get(self, where_clause: Any) -> M | None:
        query = select(self.model).where(where_clause)
        result = await self._session.execute(query)
        return result.scalars().first()

    async def sync(
        self, *, commit: bool = True, flush: bool = False, refresh: bool = False
    ) -> None:
        if flush:
            await self._session.flush()

        if commit:
            await self._session.commit()

        if refresh:
            await self._session.refresh(self.model)

    async def scalars(self, query: TypedReturnsRows) -> ScalarResult[M]:
        result = await self._session.execute(query)
        return result.scalars()

    async def all(self, query: TypedReturnsRows) -> list[M]:
        result = await self._session.execute(query)
        result = result.scalars().all()
        return list(result) or []

    async def first(self, query: Select) -> M | None:
        result = await self._session.execute(query)
        return result.scalars().first()

    async def get_mapping(self, query: TypedReturnsRows) -> Mapping[str, Any]:
        result = await self._session.execute(query)
        row = result.mappings().first()
        if row is None:
            return {}
        return dict(row)

    async def get_mappings(self, query: TypedReturnsRows) -> list[Mapping[str, Any]]:
        result = await self._session.execute(query)
        return [dict(row) for row in result.mappings().all()]

    async def rollback(self) -> None:
        """Rolls back the current transaction."""
        await self._session.rollback()

    async def _execute_paginated(
        self, statement: Select, page: int = 1, page_size: int = 10
    ) -> tuple[Result, int]:
        """Paginate the results of a query."""

        if page < 1:
            page = 1

        if page_size < 1:
            page_size = 10

        offset = (page - 1) * page_size

        count_stmnt = select(func.count()).select_from(self.model)
        if statement._whereclause is not None:
            count_stmnt = count_stmnt.where(statement._whereclause)

        count_result = await self._session.execute(count_stmnt)
        total = count_result.scalar_one()
        paginated_query = statement.offset(offset).limit(page_size)
        result = await self._session.execute(paginated_query)
        return result, total

    async def paginate(
        self,
        statement: Select,
        page: int = 1,
        page_size: int = 10,
    ) -> SqlPageResult[M]:
        result, total = await self._execute_paginated(statement, page, page_size)
        return SqlPageResult(
            models=list(result.scalars().all()) or [],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def paginate_mappings(
        self,
        statement: Select,
        page: int = 1,
        page_size: int = 10,
    ) -> SqlPageResult[Mapping[str, Any]]:
        result, total = await self._execute_paginated(statement, page, page_size)

        return SqlPageResult(
            models=[dict(row) for row in result.mappings().all()],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def count_by(self, where_clause: Any) -> int:
        query = select(func.count()).select_from(self.model).where(where_clause)
        result = await self._session.execute(query)
        return result.scalar_one()

    async def exists(self, where_clause: Any) -> bool:
        query = select(func.count()).select_from(self.model).where(where_clause)
        result = await self._session.execute(query)
        count = result.scalar_one()
        return count > 0

    def order_by(self, query: Select, direction: str, col: Any) -> Select:
        if direction.lower() == 'asc':
            return query.order_by(col.asc())
        elif direction.lower() == 'desc':
            return query.order_by(col.desc())
        else:
            raise ValueError("Invalid sort direction. Use 'asc' or 'desc'.")
