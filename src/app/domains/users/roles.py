from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = 'admin'
    USER = 'user'
    DEVELOPER = 'developer'
    GUEST = 'guest'
