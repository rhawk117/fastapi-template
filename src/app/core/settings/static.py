from datetime import timedelta
from typing import Literal, TypeAlias

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class StaticFileConfig(BaseSettings): ...


LevelNames: TypeAlias = Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


class AppSettings(StaticFileConfig):
    model_config = SettingsConfigDict(env_prefix='APP_')

    log_level: LevelNames = Field(
        default='INFO',
        description='The root logger log level for the entire application',
    )

    file_logging_okay: bool = Field(
        default=True, description='Enables file logging of JSON data'
    )

    name: str = 'FastAPI Template Application'

    version: str = '0.1.0'

    description: str = (
        'An extendable FastAPI application template with Authentication, Redis, '
        'SQLAlchemy, RBAC and User Management.'
    )

    summary: str = 'A custom FastAPI template'

    docs_url: str = '/docs'
    openapi_url: str = '/openapi.json'
    redoc_url: str = '/redoc'

    debug: bool = Field(
        default=False,
        description='Enables debug mode for the application',
    )

    docs_okay: bool = Field(
        default=True,
        description='Enables the OpenAPI documentation and schema generation',
    )

    testing: bool = Field(
        default=False,
        description='Indicates if the application is running in a testing environment',
    )


class AuthSettings(StaticFileConfig):
    model_config = SettingsConfigDict(env_prefix='AUTH_')

    access_token_exp_minutes: int = Field(
        default=15,
        description='Access token expiration time in minutes',
    )

    refresh_token_exp_days: int = Field(
        default=1,
        description='Refresh token expiration time in days',
    )

    jwt_issuer: str = Field(
        default='fastapi-template',
        description='Issuer of the JWT tokens',
    )

    jwt_audience: str = Field(
        default='fastapi-template',
        description='Audience of the JWT tokens',
    )

    jwt_algorithm: str = Field(
        default='RS256',
        description='Algorithm used for signing JWT tokens',
    )

    redis_token_prefix: str = Field(
        default='auth:tokens:',
        description='Prefix for Redis keys used to store tokens',
    )

    @property
    def access_token_exp(self) -> timedelta:
        return timedelta(minutes=self.access_token_exp_minutes)

    @property
    def refresh_token_exp(self) -> timedelta:
        return timedelta(days=self.refresh_token_exp_days)


class CrossOriginSettings(StaticFileConfig):
    model_config = SettingsConfigDict(env_prefix='CORS_')

    allow_origins: list[str] = Field(
        default=['*'],
        description='List of origins that are allowed to make cross-origin requests',
    )

    allow_credentials: bool = Field(
        default=True,
        description='Indicates whether cookies are allowed to in cors requests',
    )

    allow_methods: list[str] = Field(
        default=['*'],
        description='List of HTTP methods that are allowed in cross-origin requests',
    )

    allow_headers: list[str] = Field(
        default=['*'],
        description='List of HTTP headers that are allowed in cross-origin requests',
    )

    expose_headers: list[str] = Field(
        default=[], description='List of HTTP headers that are exposed in cors requests'
    )

    max_age: int = Field(
        default=600,
        description='Maximum age in seconds for preflight requests to be cached',
    )

    allow_origins_regex: str | None = Field(
        default=None,
        description='Regular expression for matching allowed origins',
    )


class RedisOptions(StaticFileConfig):


    socket_connection_timeout: float = Field(
        default=5.0,
        description='Timeout for socket connections to Redis',
    )
    socket_timeout: float = Field(
        default=5.0,
        description='Timeout for socket operations with Redis',
    )
    max_connections: int = Field(
        default=10,
        description='Maximum number of connections to Redis',
    )
    health_check_interval: float = Field(
        default=30.0,
        description='Interval in seconds for health checks on Redis connections',
    )


class SqlAlchemyOptions(StaticFileConfig):
    model_config = SettingsConfigDict(
        env_prefix='SQLALCHEMY_'
    )

