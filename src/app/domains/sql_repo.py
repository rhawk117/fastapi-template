import abc
from collections.abc import Mapping
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import TypedReturnsRows

# from sqlalchemy.sql.selectable
M = TypeVar('M')


class SQLRepositoryABC(abc.ABC, Generic[M]):
    def __init__(self, session: AsyncSession, model: type[M]) -> None:
        self.session: AsyncSession = session
        self.model: type[M] = model

    @abc.abstractmethod
    async def create(
        self,
        model_init: Mapping[str, Any],
        *,
        commit: bool = True
    ) -> M | None: ...

    @abc.abstractmethod
    async def delete(self, model: M, *, commit: bool = True) -> bool: ...

    @abc.abstractmethod
    async def update(
        self,
        model: M,
        model_init: Mapping[str, Any],
        *,
        commit: bool = True,
        refresh: bool = True,
    ) -> M: ...

    @abc.abstractmethod
    async def sync(
        self, *, commit: bool = True, flush: bool = True, refresh: bool = True
    ) -> None: ...

    @abc.abstractmethod
    async def scalars(self, query: TypedReturnsRows) -> ScalarResult[M]: ...

    @abc.abstractmethod
    async def all(self, query: TypedReturnsRows) -> list[M]: ...

    @abc.abstractmethod
    async def first(self, query: TypedReturnsRows) -> M | None: ...

    @abc.abstractmethod
    async def first_mapping(self, query: TypedReturnsRows) -> Mapping[str, Any]: ...

    @abc.abstractmethod
    async def get_mappings(
        self, query: TypedReturnsRows
    ) -> list[Mapping[str, Any]]: ...


S = TypeVar('S', bound=BaseModel)


class SQLRepository(SQLRepositoryABC[M], Generic[M]):
    """Base repository for SQLAlchemy models"""

    def __init__(self, session: AsyncSession, model: type[M]) -> None:
        super().__init__(session, model)

    async def create(
        self, model_init: Mapping[str, Any], *, commit: bool = True
    ) -> M | None:
        try:
            instance = self.model(**model_init)
            self.session.add(instance)
        except Exception:
            return None

        if commit:
            await self.session.commit()

        return instance

    async def delete(self, model: M, *, commit: bool = True) -> bool:
        try:
            await self.session.delete(model)
        except Exception:
            return False

        if commit:
            await self.session.commit()

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

        self.session.add(model)

        if commit:
            await self.session.commit()

        if refresh:
            await self.session.refresh(model)

        return model

    async def sync(
        self, *, commit: bool = True, flush: bool = False, refresh: bool = False
    ) -> None:
        if flush:
            await self.session.flush()

        if commit:
            await self.session.commit()

        if refresh:
            await self.session.refresh(self.model)

    async def scalars(self, query: TypedReturnsRows) -> ScalarResult[M]:
        result = await self.session.execute(query)
        return result.scalars()

    async def all(self, query: TypedReturnsRows) -> ScalarResult[M]:
        result = await self.session.execute(query)
        return result.scalars()

    async def first(self, query: TypedReturnsRows) -> M | None:
        result = await self.session.execute(query)
        return result.scalars().first()

    async def first_mapping(self, query: TypedReturnsRows) -> Mapping[str, Any]:
        result = await self.session.execute(query)
        row = result.mappings().first()
        if row is None:
            return {}
        return dict(row)

    async def get_mappings(self, query: TypedReturnsRows) -> list[Mapping[str, Any]]:
        result = await self.session.execute(query)
        return [dict(row) for row in result.mappings().all()]
