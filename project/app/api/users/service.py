from app.api.auth.schema import LoginBody
from app.common.db_service import DatabaseService
from app.common.http_exceptions import HTTPBadRequest
from app.core.security.cryptography import CryptoUtils
from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import DeleteSelfForbidden, UsernameTaken, UserNotFound
from .model import User
from .schema import UserCreateBody, UserListResponse, UserResponse, UserUpdateBody


class UserService(DatabaseService[User]):
    """The service for the User model"""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    def to_response(self, user: User) -> UserResponse:
        return UserResponse.convert(user)

    async def authenticate(self, login_req: LoginBody) -> User | None:
        """verifies the user credentials by checking the hashed password

        Arguments:
            auth_form {AuthForm}
            db {AsyncSession}
        Returns:
            Optional[User]
        """
        existing_user = await self.select_username(login_req.username)
        if not existing_user:
            return None

        if not CryptoUtils.verify_hash(
            plain_text=login_req.password, hashed_text=existing_user.password_hash
        ):
            return None

        return existing_user

    async def select_username(self, username: str) -> User | None:
        return await self.models.select(User.username == username)

    async def require_username(self, username: str) -> User:
        """
        gets the username and throws a 404 if not found

        Parameters
        ----------
        username : str

        Returns
        -------
        User

        Raises
        ------
        UserNotFound - 404
        """
        user = await self.select_username(username)
        if not user:
            raise UserNotFound()
        return user

    async def create_user(self, create_req: UserCreateBody) -> User:
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
        user_in = create_req.dump_exclude(exclude={'password'})
        user_in['password_hash'] = CryptoUtils.hash(create_req.password)

        return await self.models.create(user_in)

    async def update_by_id(self, user_id: int, update_req: UserUpdateBody) -> User:
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
        usr_updated = await self.get_by_id(user_id)
        if not usr_updated:
            raise UserNotFound()

        update_dump = update_req.dump_exclude(exclude={'password'})
        if update_req.password:
            update_dump['password_hash'] = CryptoUtils.hash(update_req.password)

        if not update_dump:
            raise HTTPBadRequest('Cannot update a user without making any changes.')

        if self.new_username_taken(update_req.username, usr_updated.username):
            raise UsernameTaken()

        return await self.models.update(usr_updated, update_dump)

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
            and await self.select_username(new_username) is not None
        )

    async def delete_by_id(self, user_id: int, admin_name: str) -> None:
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
        user = await self.get_by_id(user_id)
        if user is None:
            raise UserNotFound()

        acting_admin = await self.select_username(admin_name)

        if acting_admin is None or acting_admin.id == user_id:
            raise DeleteSelfForbidden()

        await self.models.delete(user)

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.models.select(User.id == user_id)

    async def role_based_read_all(self, reader_role: User) -> UserListResponse:
        """
        returns all the users in the database if the user is an admin
        otherwise returns only the user's data

        Parameters
        ----------
        reader_role : User

        Returns
        -------
        UserListResponse
        """
        readable_users = await self.models.select_all(
            User.role_level <= reader_role.role_level
        )
        response = UserListResponse.from_results(
            [UserResponse.convert(user) for user in readable_users]
        )
        return response

    async def read_all_users(self) -> UserListResponse:
        """
        returns all the users in the database

        Returns
        -------
        UserListResponse
        """
        all_users = await self.models.select_all()
        response = UserListResponse.from_results(
            [UserResponse.convert(user) for user in all_users]
        )
        return response
