from app.api.auth.schema import LoginBody
from app.common.errors import HTTPBadRequest
from app.common.service_abc import DatabaseService
from app.core.security.crypto import CryptoUtils
from sqlalchemy.ext.asyncio import AsyncSession

from .errors import DeleteSelfForbidden, UsernameTaken, UserNotFound
from .model import User
from .schema import UserCreateBody, UserListResponse, UserResponse, UserUpdateBody


class UserService(DatabaseService[User]):
    """The service for the User model"""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    def to_response(self, model: User) -> UserResponse:
        """returns a UserResponse model from the User model

        Arguments:
            model {User} -- the databas model

        Returns:
            UserResponse -- the pydantic model
        """
        return UserResponse.convert(model)

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
        """gets the username and throws a 404 if not found

        Arguments:
            username {str} -- the username to search for
        Raises:
            HTTPException: 404 (UserNotFound)
        Returns:
            User -- the user model
        """
        user = await self.select_username(username)
        if not user:
            raise UserNotFound()
        return user

    async def create_user(self, create_req: UserCreateBody) -> User:
        """creates and inserts a user model using the create user request
        schema

        Arguments:
            db {AsyncSession} -- the database session
            create_req {CreateUser} -- the request schema

        Returns:
            User -- the created user
        """
        user_in = create_req.serialize_exclude(exclude={'password'})
        user_in['password_hash'] = CryptoUtils.hash(create_req.password)

        return await self.models.create(user_in)

    async def update_by_id(self, user_id: int, update_req: UserUpdateBody) -> User:
        """updates a user ORM model using the UpdateUser request
        body schema given a valid user_id

        Arguments:
            user_id {int}
            update_req {UpdateUser}
        Raises:
            HTTPException: 404 (UserNotFound)
        Returns:
            User -- the updated user ORM model
        """
        usr_updated = await self.get_by_id(user_id)
        if not usr_updated:
            raise UserNotFound()

        update_dump = update_req.serialize_exclude(exclude={'password'})
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
        """edge case checking if the users new username is already taken

        Arguments:
            username {str} -- the username to check

        Returns:
            bool -- True if the username is already taken
        """
        return (
            new_username is not None
            and new_username != old_username
            and await self.select_username(new_username) is not None
        )

    async def delete_by_id(self, user_id: int, admin_name: str) -> None:
        """deletes the user given a valid user_id

        Arguments:
            user_id {int}
            admin_name {str} -- the name of the admin
        Raises:
            HTTPException: 404
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

        Arguments:
            user_role {str} -- the role of the user

        Returns:
            list[User] -- list of users
        """
        readable_users = await self.models.select_all(
            User.role_level <= reader_role.role_level
        )
        response = UserListResponse.from_results(
            [self.to_response(user) for user in readable_users]
        )
        return response

    async def read_all_users(self) -> UserListResponse:
        """returns all the users in the database
        Arguments:
            db {AsyncSession} -- the database session
        Returns:
            list[User] -- list of users
        """
        all_users = await self.models.select_all()
        response = UserListResponse.from_results(
            [self.to_response(user) for user in all_users]
        )
        return response
