from typing import Any, Generic, TypeVar

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.selectable import Select

ModelT = TypeVar("ModelT")


class ModelRepository(Generic[ModelT]):
    """Provides methods for common CRUD operations on database models
    and is the foundation for all services that interact with the database.
    Properties:
        model {ModelT} -- the SQLAlchemy model class for the repository
        db {AsyncSession} -- the database session to use for queries
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

    async def select(self, predicate: Any) -> ModelT | None:
        query = select(self.model).where(predicate)
        result = await self.db.execute(query)
        output = result.scalars().first()
        return output

    async def filter_by(self, **filters: Any) -> list[ModelT]:
        query = select(self.model).filter_by(**filters)
        result = await self.db.execute(query)
        models = result.scalars().all()
        return list(models) if models else []

    async def select_all(self, predicate: Any | None = None) -> list[ModelT]:
        stmnt = select(self.model)
        if predicate is not None:
            stmnt = stmnt.where(predicate)
        result = await self.db.execute(stmnt)
        models = result.scalars().all()
        return list(models) if models else []

    async def exists(self, predicate: Any) -> bool:
        query = select(func.count()).select_from(self.model).filter(predicate)
        result = await self.db.execute(query)
        count = result.scalar_one()
        return count > 0

    async def select_limited(self, skip: int = 0, limit: int = 100) -> list[ModelT]:
        query = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(query)
        models = result.scalars().all()
        return list(models) if models else []

    async def create(self, obj_in: dict) -> ModelT:
        db_model = self.model(**obj_in)
        await self.save(db_model, refresh=True)
        return db_model

    async def update(self, db_model: ModelT, obj_in: dict) -> ModelT:
        for field, value in obj_in.items():
            if hasattr(db_model, field):
                setattr(db_model, field, value)

        await self.db.commit()
        await self.db.refresh(db_model)
        return db_model

    async def size(self) -> int:
        query = select(func.count()).select_from(self.model)
        result = await self.db.execute(query)
        total: int = result.scalar_one()
        return total

    async def count_by(self, query: Select) -> int:
        count_query = query.with_only_columns(
            func.count(), maintain_column_froms=True
        ).order_by(None)
        result = await self.db.execute(count_query)
        total: int = result.scalar_one()

        return total
