from __future__ import annotations

from typing import NamedTuple, Sequence

from sqlalchemy import RowMapping, Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, load_only
from sqlalchemy.sql.base import ExecutableOption

from backend.utils import pagination_utils
from fastapi_template.domain.sql_repo import DatabaseRepository

from .model import User, UserRole
from .params import UserDetailsQueryParams, UserQueryParams, UserSortTypes


class Page(NamedTuple):
    rows: Sequence[RowMapping]
    total: int


class UserRepository(DatabaseRepository[User, str]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    @property
    def primary_key_column(self) -> InstrumentedAttribute[str]:
        return User.id

    @property
    def public_user(self) -> ExecutableOption:
        return load_only(User.id, User.username, User.role, User.email)

    @property
    def details_user(self) -> ExecutableOption:
        return load_only(
            User.id,
            User.username,
            User.role,
            User.email,
            User.created_at,
            User.updated_at,
        )

    async def get_by_id(self, user_uuid: str) -> User | None:
        user_orm = await self.get_by_pk(user_uuid)
        return user_orm

    async def get_by_username(self, username: str) -> User | None:
        user_orm = await self.get_first(where_clauses=[User.username == username])
        return user_orm

    async def username_taken(self, username: str) -> bool:
        return await self.exists(where_clauses=[User.username == username])

    async def email_taken(self, email: str) -> bool:
        return await self.exists(where_clauses=[User.email == email])

    async def get_by_email(self, email: str) -> User | None:
        user_orm = await self.get_first(
            where_clauses=[User.email == email], load_options=[self.public_user]
        )
        return user_orm

    def _prepare_user_query(
        self,
        statement: Select,
        parameters: UserQueryParams,
    ) -> Select:
        if parameters.sort_by == UserSortTypes.USERNAME:
            sort_columns = [User.username]
        elif parameters.sort_by == UserSortTypes.EMAIL:
            sort_columns = [User.email]

        sort_columns = pagination_utils.get_sort_clauses(parameters, sort_columns)
        statement = statement.order_by(*sort_columns)
        return pagination_utils.add_pagination_params(statement, parameters)

    async def get_page(
        self, reader_permissions: UserRole, parameters: UserQueryParams
    ) -> Page:
        query = (
            select(User).where(User.role < reader_permissions).options(self.public_user)
        )
        total = await self.count(where_clauses=[User.role <= reader_permissions])
        query = self._prepare_user_query(parameters=parameters, statement=query)

        results = await self.run(query)
        rows = results.mappings().all()
        return Page(rows=rows, total=total)

    async def get_details_page(
        self, reader_permissions: UserRole, parameters: UserDetailsQueryParams
    ) -> Page:
        where_clauses = [User.role < reader_permissions]

        timestamp_clauses = pagination_utils.get_timestamp_clauses(parameters, User)
        where_clauses.extend(timestamp_clauses)

        query = select(User).where(*where_clauses)

        total = await self.count(where_clauses=where_clauses)
        query = self._prepare_user_query(parameters=parameters, statement=query)
        result = await self.run(query)
        rows = result.mappings().all()
        return Page(rows=rows, total=total)
