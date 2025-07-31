from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class _EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra='allow',
    )


class SecretSettings(_EnvSettings):
    """
    Environment settings for the application.
    """

    SECRET_KEY: str

    ENCRYPTION_KEY: str
    ENCRYPTION_SALT: str

    JWT_ALGORITHM: Literal['HS256', 'RS256']
    JWT_FINGERPRINT_SECRET: str

    PRIVATE_KEY_PASSWORD: str | None = None
    PRIVATE_KEY_FILE: str
    PUBLIC_KEY_FILE: str
    BCRYPT_PEPPER: str | None = None

    DATABASE_URL: str

    REDIS_HOST: str = 'localhost'

    REDIS_PASSWORD: str | None = None
    REDIS_USERNAME: str | None = None

    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def __keys_dir(self) -> Path:
        root = Path(__file__).parent.parent.parent.resolve()
        return root / 'keys'

    def private_key_path(self) -> Path:
        return self.__keys_dir / self.PRIVATE_KEY_FILE

    def public_key_path(self) -> Path:
        return self.__keys_dir / self.PUBLIC_KEY_FILE

    @property
    def private_key_password(self) -> bytes | None:
        if self.PRIVATE_KEY_PASSWORD:
            return self.PRIVATE_KEY_PASSWORD.encode('utf-8')
        return None
