from typing import Protocol

from passlib.context import CryptContext
from passlib.exc import MissingBackendError
from pydantic import SecretStr


class StaleCallback(Protocol):
    def __call__(self, new_hash: str) -> None: ...


_crypto_conext = CryptContext(
    schemes=['bcrypt_sha256'],
    deprecated='auto',
    bcrypt_sha256__rounds=12,
    bcrypt_sha256__indent='2b',
)


class PasswordService:
    def __init__(self, bcrypt_pepper: SecretStr) -> None:
        self._pepper: str = bcrypt_pepper.get_secret_value()
        self._crypto_conext: CryptContext = _crypto_conext

    def _apply_pepper(self, password: str) -> str:
        return f'{password}{self._pepper}'

    def hash_password(self, password: str) -> str:
        peppered = self._apply_pepper(password)
        hashed_password = None
        try:
            hashed_password = self._crypto_conext.hash(peppered)
        except MissingBackendError as e:
            raise RuntimeError(
                'bcrypt backend not available, meaning it is not installed.'
            ) from e

        return hashed_password

    def check_password(
        self,
        *,
        plain_password: str,
        stored_hash: str,
        on_stale: StaleCallback | None = None,
    ) -> bool:
        peppered = self._apply_pepper(plain_password)
        try:
            is_valid = self._crypto_conext.verify(peppered, stored_hash)
        except MissingBackendError:
            raise RuntimeError(
                'bcrypt backend not available, meaning it is not installed.'
            )

        if is_valid and self._crypto_conext.needs_update(stored_hash):
            new_hash = self._crypto_conext.hash(peppered)
            if on_stale:
                on_stale(new_hash)

        return is_valid


async def get_password_service(bcrypt_pepper: SecretStr) -> PasswordService:
    """
    Factory function to create a PasswordService instance.

    Parameters
    ----------
    bcrypt_pepper : SecretStr
        The pepper to be applied to passwords before hashing.

    Returns
    -------
    PasswordService
        An instance of PasswordService.
    """
    return PasswordService(bcrypt_pepper=bcrypt_pepper)
