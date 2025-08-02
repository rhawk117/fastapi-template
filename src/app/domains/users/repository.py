from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import MappedColumn, selectinload

from app.domains.sql_repo import SQLRepository
from app.domains.users.schemas import UserQueryCommand
from app.utils import sql_utils

from .models import Role, User


def public_cols() -> tuple[MappedColumn, ...]:
    return (
        User.id,  # type: ignore
        User.username,
        User.email,
        User.role,
    )


def user_select() -> Select:
    return select(User).options(selectinload(User.role))


def select_id() -> Select:
    return select(User.id)


class UserRepository(SQLRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> User | None:
        stmnt = user_select().where(User.username == username)
        result = await self.first(stmnt)
        return result

    async def username_taken(self, username: str) -> bool:
        stmnt = select_id().where(User.username == username)
        result = await self.first(stmnt)
        return result is not None

    async def email_taken(self, email: str) -> bool:
        stmnt = select_id().where(User.email == email)
        result = await self.first(stmnt)
        return result is not None

    async def get_by_id(self, user_id: str) -> User | None:
        stmnt = user_select().where(User.id == user_id)
        result = await self.first(stmnt)
        return result

    async def get_by_email(self, email: str) -> User | None:
        stmnt = select_id().where(User.email == email)
        result = await self.first(stmnt)
        return result

    def no_readup(self, reader_role_level: int, base_stmnt: Select) -> Select:
        return (
            base_stmnt.join(Role, User.role_id == Role.id)
            .where(Role.role_level <= reader_role_level)
            .order_by(Role.role_level.desc(), User.username)
        )

    async def query(self, *, command: UserQueryCommand) -> dict:
        base_stmnt = self.no_readup(command.reader_role_level, user_select())

        where_clauses = []
        if command.username:
            where_clauses.append(User.username.ilike(f'%{command.username}%'))

        if command.active_only:
            where_clauses.append(User.is_active.is_(True))

        stmnt = sql_utils.prepare_select(
            base_stmnt,
            where_clauses=where_clauses,
            options=[selectinload(User.role)]
        )

        stmnt = sql_utils.paginate_select(
            stmnt,
            offset=command.offset,
            limit=command.limit,
            total_column='query_total',
        )

        result = await self.get_mappings(stmnt)

        output = {}
        if result:
            output['total'] = result[0].pop('query_total', 0)  # type: ignore
            output['rows'] = [row for row in result]

        return output
