from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_template.api.http_exceptions import HTTPBadRequest, HTTPForbidden, HTTPNotFound
from backend.core.security.cryptography import CryptoUtils
from backend.core.security.rbac import Role

from .exceptions import UserNotFound
from .repository import UserRepository
from .schema import (
    UserCreateModel,
    UserDetailsModel,
    UserDetailsPage,
    UserDetailsQueryParams,
    UserModel,
    UserPage,
    UserQueryParams,
    UserUpdateModel,
)


class UserService:
    """The service for the User model"""

    def __init__(self, db: AsyncSession) -> None:
        self.repository = UserRepository(db)

    async def authenticate(self, username: str, password: str) -> UserModel | None:
        """verifies the user credentials by checking the hashed password

        Arguments:
            auth_form {AuthForm}
            db {AsyncSession}
        Returns:
            Optional[User]
        """
        user = await self.repository.get_by_username(username)
        if not user:
            return None

        if not CryptoUtils.verify_hash(
            plain_text=password,
            hashed_text=user.password_hash
        ):
            return None

        return UserModel.model_validate(user)

    async def create_user(self, create_req: UserCreateModel) -> UserModel:
        """
        creates and inserts a user model using the create user request
        schema


        Parameters
        ----------
        create_req : UserCreateBody

        Returns
        -------
        User
        """
        if await self.repository.username_taken(create_req.username):
            raise HTTPBadRequest('Username already taken.')

        if await self.repository.email_taken(create_req.email):
            raise HTTPBadRequest('Email already taken.')

        user_kwargs = create_req.model_dump(exclude={'password'})
        user_kwargs['password_hash'] = CryptoUtils.hash(create_req.password)
        user_orm = await self.repository.insert(user_kwargs)

        return UserModel.model_validate(user_orm)

    async def update_user(
        self,
        user_id: int,
        update_req: UserUpdateModel,
        current_user_id: int,
        current_user_role: Role,
    ) -> UserModel:
        """
        updates a user ORM model using the UpdateUser request
        body schema given a valid user_id


        Parameters
        ----------
        user_id : int
        update_req : UserUpdateBody

        Returns
        -------
        User

        Raises
        ------
        UserNotFound - 404
        HTTPBadRequest - 400
        UsernameTaken - 400
        """

        existing_user = await self.repository.get_by_id(user_id)
        if not existing_user:
            raise HTTPNotFound('User not found.')

        if current_user_id != existing_user.id and not current_user_role == Role.ADMIN:
            raise HTTPForbidden('You are not authorized to perform this action.')

        if await self.new_username_taken(update_req.username, existing_user.username):
            raise HTTPBadRequest('Username already taken.')

        update_arguments = update_req.model_dump(exclude={'password'}, exclude_none=True)
        if not update_arguments and not update_req.password:
            raise HTTPBadRequest('No fields to update.')

        if update_req.password:
            update_arguments['password_hash'] = CryptoUtils.hash(update_req.password)

        updated_user = await self.repository.update(update_arguments, existing_user)

        return UserModel.model_validate(updated_user)

    async def new_username_taken(
        self, new_username: str | None, old_username: str
    ) -> bool:
        """
        edge case checking if the users new username is already taken

        Parameters
        ----------
        new_username : str | None
        old_username : str

        Returns
        -------
        bool
        """
        return (
            new_username is not None
            and new_username != old_username
            and await self.repository.username_taken(new_username)
        )

    async def delete_user(self, user_id: int, admin_name: str) -> None:
        """
        deletes a user by id, raises a UserNotFound if the user does not exist

        Parameters
        ----------
        user_id : int
        admin_name : str

        Raises
        ------
        UserNotFound - 404
        DeleteSelfForbidden - 403
        """
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFound()

        acting_admin = await self.repository.get_by_username(admin_name)
        if acting_admin is None:  # should never happen just to be safe
            raise HTTPForbidden('You are not authorized to delete users.')

        if acting_admin.id == user_id:
            raise HTTPForbidden('You cannot delete yourself.')

        await self.repository.delete(user)

    async def query_users(self, reader_role: Role, params: UserQueryParams) -> UserPage:
        page_result = await self.repository.get_page(reader_role, params)

        models = [UserModel.model_validate(user) for user in page_result.rows]

        return UserPage.from_results(
            data=models, total_items=page_result.total, page_params=params
        )

    async def get_user_detail(self, user_id: int) -> UserDetailsModel:
        """
        retrieves a user by id, raises a UserNotFound if the user does not exist

        Parameters
        ----------
        user_id : int

        Returns
        -------
        UserModel

        Raises
        ------
        UserNotFound - 404
        """
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFound()

        return UserDetailsModel.model_validate(user)

    async def query_user_details(
        self, reader_role: Role, params: UserDetailsQueryParams
    ) -> UserDetailsPage:
        """
        retrieves a user by id, raises a UserNotFound if the user does not exist

        Parameters
        ----------
        reader_role : Role
        user_id : int

        Returns
        -------
        UserModel

        Raises
        ------
        UserNotFound - 404
        """

        results = await self.repository.get_details_page(reader_role, params)

        models = [UserDetailsModel.model_validate(user) for user in results.rows]

        return UserDetailsPage.from_results(
            data=models, total_items=results.total, page_params=params
        )

    async def get_user(self, user_id: int, current_user_role: Role) -> UserModel:
        '''
        gets a user by id, raises a UserNotFound if the user does not exist

        Parameters
        ----------
        user_id : int
        current_user_role : Role

        Returns
        -------
        UserModel

        Raises
        ------
        UserNotFound
        HTTPForbidden
        '''
        target_user = await self.repository.get_by_id(user_id)
        if not target_user:
            raise UserNotFound()

        if current_user_role != Role.ADMIN and target_user.id != user_id:
            raise HTTPForbidden('You are not authorized to view this user.')

        return UserModel.model_validate(target_user)

    async def get_username(self, username: str) -> UserModel:
        """
        retrieves a user by username, raises a UserNotFound if the user does not exist

        Parameters
        ----------
        username : str

        Returns
        -------
        UserModel

        Raises
        ------
        UserNotFound - 404
        """
        user = await self.repository.get_by_username(username)
        if not user:
            raise HTTPNotFound('user')

        return UserModel.model_validate(user)