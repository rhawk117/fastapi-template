from collections.abc import Callable

from passlib.context import CryptContext
from passlib.exc import MissingBackendError

from fastapi_template.core import settings

__pwd_context = CryptContext(
    schemes=['bcrypt_sha26'],
    deprecated='auto',
    bcrypt_sha26__rounds=12,
    bcrypt_sha26__indent='2b',
)


def _apply_pepper(password: str) -> str:
    pepper = settings.get_secrets().BCRYPT_PEPPER
    return f'{password}{pepper}'


def hash_password(password: str) -> str:
    try:
        return __pwd_context.hash(_apply_pepper(password))
    except MissingBackendError as e:
        raise RuntimeError(
            'bcrypt backend not available meaning its not installed. '
        ) from e


def check_password(
    *,
    plain_password: str,
    stored_hash: str,
    on_stale: Callable[[str], None] | None = None,
) -> bool:
    try:
        is_valid = __pwd_context.verify(_apply_pepper(plain_password), stored_hash)
    except MissingBackendError:
        return False

    if is_valid and __pwd_context.needs_update(stored_hash):
        new_hash = hash_password(plain_password)
        if on_stale:
            on_stale(new_hash)

    return is_valid
