from typing import Protocol

from passlib.context import CryptContext
from passlib.exc import MissingBackendError

from app.core.settings import core

__pwd_context = CryptContext(
    schemes=['bcrypt_sha26'],
    deprecated='auto',
    bcrypt_sha26__rounds=12,
    bcrypt_sha26__indent='2b',
)


def _apply_pepper(password: str) -> str:
    pepper = core.get_secrets().BCRYPT_PEPPER
    return f'{password}{pepper}'


def hash_password(password: str) -> str:
    """
    hashes the password using bcrypt_sha26 algorithm.

    Parameters
    ----------
    password : str

    Returns
    -------
    str

    Raises
    ------
    RuntimeError -- Missing required package
    """
    try:
        return __pwd_context.hash(_apply_pepper(password))
    except MissingBackendError as e:
        raise RuntimeError(
            'bcrypt backend not available meaning its not installed. '
        ) from e


class StaleCallback(Protocol):
    def __call__(self, new_hash: str) -> None: ...


def check_password(
    *,
    plain_password: str,
    stored_hash: str,
    on_stale: StaleCallback | None = None,
) -> bool:
    """
    Checks if the provided plain password matches the stored hash.

    Parameters
    ----------
    plain_password : str
    stored_hash : str
    on_stale : StaleCallback | None, optional

    Returns
    -------
    bool
    """
    try:
        is_valid = __pwd_context.verify(_apply_pepper(plain_password), stored_hash)
    except MissingBackendError:
        return False

    if is_valid and __pwd_context.needs_update(stored_hash):
        new_hash = hash_password(plain_password)
        if on_stale:
            on_stale(new_hash)

    return is_valid
