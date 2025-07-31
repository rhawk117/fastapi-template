from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from fastapi_template.domain.models.users import User
from fastapi_template.infrastructure.repositories import (
    PageResult,
    SQLMappedRepository,
    SQLModelRepository,
)

from .query import UserDetailsQueryParams, UserQueryParams, UserSortTypes


class UserRepository(SQLModelRepository[User, str], SQLMappedRepository[User, str]):
    model = User

    _PUBLIC_COLS = {
        'id',
        'username',
        'role',
        'email',
    }

    _ADMIN_COLS = {
        'id',
        'username',
        'role',
        'email',
        'created_at',
        'updated_at',
    }

    _AUTH_COLS = {
        'id',
        'username',
        'role',
        'email',
        'password_hash',
    }

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_user_by(
        self,
        *,
        columns: set[str] | None = None,
        id: str | None = None,
        username: str | None = None,
        email: str | None = None,
    ) -> Mapping | None:
        if id:
            return await self.by_id(id, include=columns)

        elif username:
            return await self.first(
                where_clauses=[User.username == username], include=columns
            )

        elif email:
            return await self.first(
                where_clauses=[User.email == email], include=columns
            )

        else:
            raise ValueError('At least one of id, username, or email must be provided.')

    async def get_user_auth(
        self, *, username: str | None = None, email: str | None = None
    ) -> Mapping | None:
        if username:
            return await self.get_user_by(username=username, columns=self._AUTH_COLS)

        elif email:
            return await self.get_user_by(email=email, columns=self._AUTH_COLS)

        else:
            raise ValueError('At least one of username or email must be provided.')

    async def is_username_taken(self, username: str) -> bool:
        existing_user = await self.first(
            where_clauses=[User.username == username], include={'id'}
        )
        return existing_user is not None

    async def is_email_taken(self, email: str) -> bool:
        existing_user = await self.first(
            where_clauses=[User.email == email], include={'id'}
        )
        return existing_user is not None

    def _get_page_order_by(
        self, query: UserQueryParams
    ) -> list[tuple[str, InstrumentedAttribute]]:
        if query.col == UserSortTypes.EMAIL:
            order_by = User.email
        else:
            order_by = User.username

        return [(query.order, order_by)]

    async def paginate_user_details(
        self, *, query: UserDetailsQueryParams
    ) -> PageResult:
        where_clauses = []

        if query.created_before:
            where_clauses.append(User.created_at < query.created_before)

        if query.created_after:
            where_clauses.append(User.created_at > query.created_after)

        if query.updated_before:
            where_clauses.append(User.updated_at < query.updated_before)

        if query.updated_after:
            where_clauses.append(User.updated_at > query.updated_after)

        return await self.paginate(
            include=self._ADMIN_COLS,
            limit=query.limit,
            offset=query.offset,
            where_clauses=where_clauses,
            sort=self._get_page_order_by(query),  # type: ignore[arg-type]
        )

    async def paginate_users(self, *, query: UserQueryParams) -> PageResult:
        return await self.paginate(
            include=self._PUBLIC_COLS,
            limit=query.limit,
            offset=query.offset,
            sort=self._get_page_order_by(query),  # type: ignore[arg-type]
        )

    async def update_by_id(self, user_id: str, obj_in: Mapping) -> dict | None:
        user = await self.get(user_id)
        if not user:
            return None

        updated_user = await self.update(user, obj_in)
        return updated_user.__dict__

    async def delete_by_id(self, user_id: str) -> bool:
        user = await self.get(user_id)
        if not user:
            return False

        await self.delete(user)
        return True
