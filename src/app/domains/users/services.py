from app.core.security import passwords
from app.domains.exceptions import HTTPBadRequest, HTTPNotFound

from .repository import UserRepository
from .schemas import (
    RegisterUser,
    UserCreate,
    UserPage,
    UserQueryCommand,
    UserResponse,
    UserUpdate,
)


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def get_user_by_id(self, user_id: str) -> UserResponse:
        user_orm = await self.repository.get_by_id(user_id)
        if not user_orm:
            raise HTTPNotFound('user')

        return UserResponse.model_validate(user_orm)

    async def authenticate_user(
        self, username: str, password: str
    ) -> UserResponse | None:
        existing_user = await self.repository.get_by_username(username)

        if not existing_user:
            raise HTTPNotFound('user')

        if not passwords.check_password(
            plain_password=password, stored_hash=existing_user.password_hash
        ):
            return None

        return UserResponse.model_validate(existing_user)

    async def _prepare_user_arguments(
        self,
        user_data: UserCreate | UserUpdate | RegisterUser
    ) -> dict:
        args = user_data.model_dump(exclude={'password'})
        if not args:
            raise HTTPBadRequest('No user data provided')

        if user_data.username and await self.repository.username_taken(
            user_data.username
        ):
            raise HTTPBadRequest('Username already taken')

        if user_data.email and await self.repository.email_taken(user_data.email):
            raise HTTPBadRequest('Email already registered')

        if user_data.password:
            args['password_hash'] = passwords.hash_password(user_data.password)

        return args

    async def register_user(self, user_data: RegisterUser) -> UserResponse:
        user_init = await self._prepare_user_arguments(user_data)
        user_orm = await self.repository.create(user_init)
        return UserResponse.model_validate(user_orm)

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        user_init = await self._prepare_user_arguments(user_data)
        user_orm = await self.repository.create(user_init)
        return UserResponse.model_validate(user_orm)

    async def update_user(self, user_id: str, user_data: UserUpdate) -> UserResponse:
        user_orm = await self.repository.get_by_id(user_id)
        if not user_orm:
            raise HTTPNotFound('user')

        update_args = await self._prepare_user_arguments(user_data)
        updated_user = await self.repository.update(user_orm, update_args)
        return UserResponse.model_validate(updated_user)

    async def delete_user(self, user_id: str) -> None:
        user_orm = await self.repository.get_by_id(user_id)
        if not user_orm:
            raise HTTPNotFound('user')

        await self.repository.delete(user_orm)

    async def list_users(self, command: UserQueryCommand) -> UserPage:
        query_results = await self.repository.query(command=command)

        if not 'rows' or 'total' not in query_results:
            raise HTTPBadRequest('Invalid query results')

        users = [UserResponse.model_validate(user) for user in query_results['rows']]

        return UserPage.from_results(
            data=users,
            total_items=query_results['total'],
            page_params=command
        )
