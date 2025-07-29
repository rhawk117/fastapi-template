from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any, NamedTuple

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import MappedColumn

from backend.app.api.users.schema import (
    UserDetailsModel,
    UserDetailsPage,
    UserModel,
    UserPage,
    UserQueryParams,
)
from backend.common.model_repository import CRUDRepository
from backend.utils import orm_utils

from .model import Role, User


class UserSorts(StrEnum):
    USERNAME = 'username'
    ROLE = 'role'


class UserQueryResult(NamedTuple):
    result: Sequence[Mapping]
    total: int


class UserRepsitory(CRUDRepository[User]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    @property
    def model_view(self) -> Select:
        return select(User.id, User.username, User.role, User.email)

    async def get_by_id(self, user_id: int) -> UserModel | None:
        statement = self.model_view.where(User.id == user_id)
        row = await self.get_one(statement)
        return UserModel.model_validate(row) if row else None

    async def get_by_username(self, username: str) -> UserModel | None:
        statement = self.model_view.where(User.username == username)
        row = await self.get_one(statement)
        return UserModel.model_validate(row) if row else None

    async def get_details_by_id(self, user_id: int) -> UserDetailsModel | None:
        model = await self.get(User.id == user_id)
        return UserDetailsModel.model_validate(model) if model else None

    async def select_models(
        self,
        *,
        statement: Select,
        params: UserQueryParams,
        min_role: Role = Role.USER
    ) -> orm_utils.PagedQuery:
        ordered_by: MappedColumn = self.get_sort(
            sort_order=params.sort_order,
            column=params.sort_by
        )
        statement = statement.where(User.role >= min_role).order_by(ordered_by)

        page_results = await orm_utils.get_page(
            params.offset, params.limit, statement, db=self.db, model=User
        )

        return page_results

    async def get_user_page(
        self,
        current_user_role: Role,
        params: UserQueryParams
    ) -> UserPage:
        base_statement = select(User.id, User.username, User.role, User.email)
        query_result = await self.select_models(
            statement=base_statement, params=params, min_role=current_user_role
        )
        models = [UserModel.model_validate(user) for user in query_result.result]

        return UserPage.from_results(
            data=models,
            total_items=query_result.total,
            page_params=params,
        )

    async def get_user_detail_page(
        self, current_user_role: Role, params: UserQueryParams
    ) -> UserDetailsPage:
        query_result = await self.select_models(
            statement=select(User), params=params, min_role=current_user_role
        )
        models = [UserDetailsModel.model_validate(user) for user in query_result.result]

        return UserDetailsPage.from_results(
            data=models,
            total_items=query_result.total,
            page_params=params,
        )

    async def username_exists(self, username: str) -> bool:
        statement = select(User.id).where(User.username == username)
        return await self.any(statement)

    async def email_exists(self, email: str) -> bool:
        statement = select(User.id).where(User.email == email)
        return await self.any(statement)

    async def delete_user_id(self, user_id: int) -> bool:
        user = await self.get(User.id == user_id)
        if not user:
            return False

        await self.delete(user)
        return True

    async def update_by_id(self, obj_in: dict[str, Any], id: int) -> UserModel | None:
        statement = select(User).where(User.id == id)
        user = await self.db.execute(statement)
        user_instance = user.scalar_one_or_none()
        if not user_instance:
            return None

        updated_user = await self.update(user_instance, obj_in)
        return UserModel.model_validate(updated_user) if updated_user else None
