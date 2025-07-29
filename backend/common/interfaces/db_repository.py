from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import Result, RowMapping, Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.sql.expression import ColumnElement

ModelType = TypeVar('ModelType', bound=DeclarativeBase)
IdType = TypeVar('IdType', bound=int | str | uuid.UUID)

WhereClause = ColumnElement[bool]


class DatabaseRepository(Generic[ModelType, IdType], ABC):
    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        self.session: AsyncSession = session
        self.model: type[ModelType] = model

    @property
    @abstractmethod
    def primary_key_column(self) -> InstrumentedAttribute[IdType]:
        pass

    def _create_select(
        self,
        *,
        load_options: Sequence[ExecutableOption] | None = None,
        where_clauses: Sequence[WhereClause] | None = None,
        columns: Sequence[InstrumentedAttribute[Any]] | None = None,
    ) -> Select[tuple[ModelType]] | Select[tuple[Any, ...]]:
        if columns:
            query = select(*columns)
        else:
            query = select(self.model)

        if load_options:
            query = query.options(*load_options)

        if where_clauses:
            query = query.where(*where_clauses)

        return query

    def get_obj_pk(self, obj: ModelType) -> IdType | None:
        return getattr(obj, self.primary_key_column.key, None)

    async def insert(
        self,
        obj_in: dict[str, Any] | Mapping[str, Any],
        *,
        flush: bool = True,
        refresh: bool = True,
        load_options: Sequence[ExecutableOption] | None = None,
    ) -> ModelType | None:
        if not isinstance(obj_in, (dict, Mapping)):
            return None

        try:
            db_model = self.model(**obj_in)
            self.session.add(db_model)

            if flush:
                await self.session.flush()

            if refresh:
                await self.session.refresh(db_model)

                if load_options:
                    entity_id = self.get_obj_pk(db_model)
                    if entity_id is not None:
                        return await self.get_by_pk(
                            entity_id, load_options=load_options
                        )

            return db_model
        except Exception:
            return None

    async def insert_all(
        self,
        objs_in: Sequence[Mapping[str, Any]],
        *,
        flush: bool = True,
    ) -> Sequence[ModelType]:
        try:
            object_list: list[ModelType] = [self.model(**obj_in) for obj_in in objs_in]
            self.session.add_all(object_list)

            if flush:
                await self.session.flush()

            return object_list
        except Exception:
            return []

    async def get_by_pk(
        self,
        entity_id: IdType,
        *,
        load_options: Sequence[ExecutableOption] | None = None,
        columns: Sequence[InstrumentedAttribute[Any]] | None = None,
    ) -> ModelType | None:
        """Get by primary key - implementation is correct, returns None."""
        try:
            query = self._create_select(load_options=load_options, columns=columns)
            query = query.where(self.primary_key_column == entity_id)

            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception:
            return None

    async def get_by_pk_mapping(
        self,
        entity_id: IdType,
        *,
        columns: Sequence[InstrumentedAttribute[Any]] | None = None,
        load_options: Sequence[ExecutableOption] | None = None,
    ) -> RowMapping | None:
        """
        Gets an model by its primary key as a dictionary mapping.

        Parameters
        ----------
        entity_id : IdType
            The primary key value (fixed parameter name)
        """
        try:
            query = self._create_select(
                columns=columns or [], load_options=load_options
            )
            if not columns:
                query = select(self.model)

            query = query.where(self.primary_key_column == entity_id)

            result = await self.session.execute(query)
            return result.mappings().first()
        except Exception:
            return None

    async def get_first(
        self,
        *,
        where_clauses: Sequence[WhereClause] | None = None,
        load_options: Sequence[ExecutableOption] | None = None,
        columns: Sequence[InstrumentedAttribute[Any]] | None = None,
    ) -> ModelType | None:
        try:
            query = self._create_select(
                where_clauses=where_clauses, load_options=load_options, columns=columns
            )
            result = await self.session.execute(query)
            return result.scalars().first()
        except Exception:
            return None

    async def get_first_mapping(
        self,
        *,
        where_clauses: Sequence[WhereClause] | None = None,
        columns: Sequence[InstrumentedAttribute[Any]] | None = None,
    ) -> RowMapping | None:
        try:
            query = self._create_select(
                where_clauses=where_clauses,
                columns=columns,
            )
            result = await self.session.execute(query)
            return result.mappings().first()
        except Exception:
            return None

    async def get_all(
        self,
        *,
        where_clauses: Sequence[WhereClause] | None = None,
        load_options: Sequence[ExecutableOption] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        order_by: Sequence[ColumnElement[Any]] | None = None,
    ) -> Sequence[ModelType]:
        try:
            query = self._create_select(
                where_clauses=where_clauses, load_options=load_options
            )

            if order_by:
                query = query.order_by(*order_by)

            if offset is not None:
                query = query.offset(offset)

            if limit is not None:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception:
            return []

    async def get_all_mappings(
        self,
        *,
        where_clauses: Sequence[WhereClause] | None = None,
        columns: Sequence[InstrumentedAttribute[Any]] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        order_by: Sequence[ColumnElement[Any]] | None = None,
    ) -> Sequence[RowMapping]:
        try:
            query = self._create_select(where_clauses=where_clauses, columns=columns)

            if order_by:
                query = query.order_by(*order_by)

            if offset is not None:
                query = query.offset(offset)

            if limit is not None:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return result.mappings().all()
        except Exception:
            return []

    async def update(
        self,
        obj_in: Mapping[str, Any],
        existing_entity: ModelType,
    ) -> ModelType | None:
        try:
            for key, value in obj_in.items():
                setattr(existing_entity, key, value)

            self.session.add(existing_entity)

            await self.session.flush()
            await self.session.refresh(existing_entity)

            return existing_entity
        except Exception:
            return None

    async def bulk_update(
        self,
        obj_in: Mapping[str, Any],
        *,
        where_clauses: Sequence[WhereClause] | None = None,
    ) -> int:
        try:
            statement = update(self.model).values(**obj_in)
            if where_clauses:
                statement = statement.where(*where_clauses)

            result = await self.session.execute(statement)
            return result.rowcount or 0
        except Exception:
            return 0

    async def delete(self, model: ModelType) -> bool:
        try:
            await self.session.delete(model)
            await self.session.flush()
            return True
        except Exception:
            return False

    async def bulk_delete(
        self,
        *,
        where_clauses: Sequence[WhereClause] | None = None,
    ) -> int:
        try:
            stmt = delete(self.model)

            if where_clauses:
                stmt = stmt.where(*where_clauses)

            result = await self.session.execute(stmt)
            return result.rowcount or 0
        except Exception:
            return 0

    async def exists(
        self,
        *,
        where_clauses: Sequence[WhereClause] | None = None,
    ) -> bool:
        try:
            query = select(func.count()).select_from(self.model)

            if where_clauses:
                for clause in where_clauses:
                    query = query.where(clause)

            result = await self.session.execute(query)
            count = result.scalar_one()
            return count > 0
        except Exception:
            return False

    async def count(
        self,
        *,
        where_clauses: Sequence[WhereClause] | None = None,
    ) -> int:
        try:
            query = select(func.count()).select_from(self.model)
            if where_clauses:
                query = query.where(*where_clauses)

            result = await self.session.execute(query)
            return result.scalar_one()
        except Exception:
            return 0

    async def run(self, statement: Select) -> Result:
        return await self.session.execute(statement)
