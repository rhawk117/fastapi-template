from enum import StrEnum
from types import MappingProxyType


class UserRole(StrEnum):
    ADMIN = 'admin'
    MODERATOR = 'moderator'
    USER = 'user'
    READ_ONLY = 'read_only'


RoleLevelMap = MappingProxyType(
    {UserRole.ADMIN: 3, UserRole.MODERATOR: 2, UserRole.USER: 1, UserRole.READ_ONLY: 0}
)



