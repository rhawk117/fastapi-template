from typing import Protocol

from passlib.context import CryptContext
from passlib.exc import MissingBackendError

from .settings import get_crypto_settings


class StaleCallback(Protocol):
    def __call__(self, new_hash: str) -> None: ...


def create_crypt_ctx(
    *,
    rounds: int = 12,
) -> CryptContext:
    return CryptContext(
        schemes=['bcrypt_sha256'],
        deprecated='auto',
        bcrypt_sha256__rounds=rounds,
        bcrypt_sha256__indent='2b',
    )


_crypt_context = create_crypt_ctx()


def _apply_pepper(password: str, pepper: str) -> str:
    pepper = get_crypto_settings().BCRYPT_PEPPER
    return f'{password}{pepper}'


def hash_password(password: str) -> str:
    """
    Hashes the provided password using bcrypt with an optional pepper.

    Parameters
    ----------
    password : str

    Returns
    -------
    str

    Raises
    ------
    RuntimeError
        _Package missing, shouldn't happen_
    """
    peppered = _apply_pepper(password, get_crypto_settings().BCRYPT_PEPPER)
    hashed_password = None
    crypt_ctx = _crypt_context
    try:
        hashed_password = crypt_ctx.hash(peppered)
    except MissingBackendError as e:
        raise RuntimeError(
            'bcrypt backend not available, meaning it is not installed.'
        ) from e

    return hashed_password


def check_password(
    *,
    plain_password: str,
    stored_hash: str,
    on_stale: StaleCallback | None = None,
) -> bool:
    """
    Verifies a plain password against the stored hash. If the hash is stale,

    Parameters
    ----------
    plain_password : str
    stored_hash : str
    on_stale : StaleCallback | None, optional
        _How to handle stale passwords_, by default None

    Returns
    -------
    bool
        _password hashes match_

    Raises
    ------
    RuntimeError
        _Bcrypt backend missing, shouldn't happen_
    """
    peppered = _apply_pepper(plain_password, get_crypto_settings().BCRYPT_PEPPER)

    crypt_ctx = _crypt_context
    try:
        is_valid = crypt_ctx.verify(peppered, stored_hash)
    except MissingBackendError:
        raise RuntimeError(
            'bcrypt backend is not available, meaning it is not installed.'
        )

    if is_valid and _crypt_context.needs_update(stored_hash):
        new_hash = _crypt_context.hash(peppered)
        if on_stale:
            on_stale(new_hash)

    return is_valid
