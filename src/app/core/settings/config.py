
import functools
import uuid
from datetime import timedelta
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import SettingsConfigDict

from .interface import EnvConfig

LoguruLevels = Literal[
    'TRACE',
    'DEBUG',
    'INFO',
    'SUCCESS',
    'WARNING',
    'ERROR',
    'CRITICAL',
]

LoguruCompression = Literal['zip', 'tar', 'gz', 'bz2', 'xz', 'none']


class JwtConfig(EnvConfig):
    '''
    Env prefix is JWT_
    '''
    model_config = SettingsConfigDict(env_prefix='JWT_')

    ISSUER: str = 'FastAPI Template'
    AUDIENCE: str = 'FastAPI Template Audience'

    ACCESS_TOKEN_TTL_MINUTES: int = 15
    REFRESH_TOKEN_TTL_HOURS: int = 24

    ALGORITHM: str = 'RS256'

    @property
    def access_token_ttl(self) -> int:
        return int(timedelta(minutes=self.ACCESS_TOKEN_TTL_MINUTES).total_seconds())

    @property
    def refresh_token_ttl(self) -> int:
        return int(timedelta(hours=self.REFRESH_TOKEN_TTL_HOURS).total_seconds())


class DatabaseConfig(EnvConfig):
    '''
    Env prefix is DATABASE_
    '''
    model_config = SettingsConfigDict(env_prefix='DATABASE_')

    DRIVER_NAME: str = 'sqlite+aiosqlite'
    DIRECTORY: str | None = None
    FILE_NAME: str | None = None
    ECHO: bool = False

    @property
    def database(self) -> str:
        return (
            f'{self.DIRECTORY}/{self.FILE_NAME}'
            if self.FILE_NAME != ':memory:'
            else self.FILE_NAME
        )

    @property
    def pragmas(self) -> dict[str, str | int]:
        return {
            'journal_mode': 'WAL',
            'synchronous': 'NORMAL',
            'cache_size': -64000,
            'foreign_keys': 1,
            'temp_store': 'MEMORY',
        }


class RedisConfig(EnvConfig):
    '''
    Env prefix is REDIS_
    '''
    model_config = SettingsConfigDict(env_prefix='REDIS_')

    HOST: str = 'localhost'
    PORT: int = 6379
    DB: int = 0
    USERNAME: str | None = None
    PASSWORD: str | None = None
    SSL: bool = False


class LoggerConfig(EnvConfig):
    '''
    Env prefix is LOGGER_
    '''
    model_config = SettingsConfigDict(env_prefix='LOGGER_')

    LEVEL: LoguruLevels = 'INFO'
    DIRECTORY: str = 'logs'
    ROTATION_MB: int = 100
    RETENTION_DAYS: int = 7
    COMPRESSION: LoguruCompression = 'zip'

    @property
    def stdout_format(self) -> str:
        return (
            '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
            '<level>{level: <8}</level> | '
            'cid=<cyan>{extra[correlation_id]}</cyan> | '
            '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - '
            '<level>{message}</level>'
        )


class AppConfig(EnvConfig):
    '''
    Env prefix is APP_
    '''
    model_config = SettingsConfigDict(env_prefix='APP_')

    DEBUG: bool = False
    TESTING: bool = False
    ALLOW_DOCS: bool = False


class RS256Config(EnvConfig):
    model_config = SettingsConfigDict(secrets_dir='keys')

    PRIVATE_KEY: SecretStr = Field(
        alias='private_key.pem',
        description='Path to the private key file for RS256 signing.',
    )

    PUBLIC_KEY: SecretStr = Field(
        alias='public_key.pem',
        description='Path to the public key file for RS256 verification.',
    )


class CryptoConfig(EnvConfig):
    '''
    Env prefix is CRYPTO_
    '''
    SECRET_KEY: SecretStr

    ENCRYPTION_KEY: SecretStr
    ENCRYPTION_SALT: SecretStr
    PBKDF2_ITERATIONS: int = 100_000
    PBKDF2_LENGTH: int = 32
    BCRYPT_PEPPER: SecretStr

class CORSConfig(EnvConfig):
    '''
    Env prefix is CORS_
    '''
    model_config = SettingsConfigDict(env_prefix='CORS_')

    ALLOW_ORIGINS: list[str] = ['*']
    ALLOW_METHODS: list[str] = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    ALLOW_HEADERS: list[str] = ['*']
    ALLOW_CREDENTIALS: bool = True

class CorrelationIdConfig(EnvConfig):
    '''
    Env prefix is CORRELATION_ID_
    '''
    model_config = SettingsConfigDict(env_prefix='CORRELATION_ID_')

    HEADER_NAME: str = 'X-Request-ID'
    UPDATE_REQUEST_HEADER: bool = True

    def id_factory(self) -> str:
        """
        Generates a new UUID for the correlation ID.

        Returns
        -------
        uuid.UUID
            A new UUID instance.
        """
        return str(uuid.uuid4())

class MidlewareConfig(EnvConfig):

    cors: CORSConfig
    correlation_id: CorrelationIdConfig

    MIDDLEWARE_ALLOWED_HOSTS: list[str] | None = None


class APISettings(EnvConfig):
    app: AppConfig
    jwt: JwtConfig
    db: DatabaseConfig
    redis: RedisConfig
    logger: LoggerConfig
    crypto: CryptoConfig
    rs256: RS256Config
    middleware: MidlewareConfig

@functools.lru_cache
def get_app_settings() -> APISettings:
    return APISettings() # type: ignore[return-value]