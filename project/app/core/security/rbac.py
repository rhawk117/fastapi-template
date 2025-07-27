from enum import StrEnum


class Role(StrEnum):
    """represents the role of a user"""

    ADMIN = 'admin'
    USER = 'user'
    READ_ONLY = 'read_only'

    @classmethod
    def get_role_level(cls, role: 'Role') -> int:
        hierarchy = {cls.ADMIN: 3, cls.USER: 2, cls.READ_ONLY: 1}
        return hierarchy.get(role, -1)

    def __lt__(self, other: 'Role') -> bool:
        return self.get_role_level(self) < self.get_role_level(other)

    def __le__(self, other: 'Role') -> bool:
        return self.get_role_level(self) <= self.get_role_level(other)

    def __ge__(self, other: 'Role') -> bool:
        return self.get_role_level(self) >= self.get_role_level(other)

    def __gt__(self, other: 'Role') -> bool:
        return self.get_role_level(self) > self.get_role_level(other)
