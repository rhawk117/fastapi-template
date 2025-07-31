from datetime import timedelta
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class _TOMLSection(BaseModel):
    pass


class AppDocsConfig(_TOMLSection):
    enabled: Annotated[
        bool, Field(default=True, description='Enable or disable OpenAPI documentation')
    ]
    openapi_url: str = '/openapi.json'
    docs_url: str = '/docs'
    redoc_url: str = '/redoc'


class AppSettings(_TOMLSection):
    env_file: str = '.env'
    debug: Annotated[bool, Field(default=False, description='Enable debug mode')]
    testing: Annotated[bool, Field(default=False, description='Enable testing mode')]

    name: Annotated[
        str, Field(default='FastAPI Template', description='Application name')
    ]
    version: Annotated[str, Field(default='0.1', description='Application version')]
    description: Annotated[
        str,
        Field(
            default='FastAPI Template Application',
            description='Application description',
        ),
    ]
    docs: AppDocsConfig

    def get_docs_urls(self) -> dict:
        dumped = self.docs.model_dump(exclude={'enabled'})
        if not self.docs.enabled:
            return {url: None for url in dumped.keys()}
        return dumped


class LoggerSettings(_TOMLSection):
    level: Annotated[str, Field('DEBUG', description='Global log level')]
    max_megabytes: Annotated[
        int, Field(10, description='Max size before rotation', lt=50)
    ]
    retention_days: Annotated[
        int, Field(5, description='Number of days to retain logs')
    ]
    compression: Annotated[
        Literal['zip', 'gz', 'tar'],
        Field('zip', description='Compression type for rotated files'),
    ]
    otel_enabled: Annotated[
        bool, Field(False, description='Enable OpenTelemetry logging')
    ]
    json_enabled: Annotated[
        bool, Field(False, description='Enable JSON serialization for logs')
    ]

    @property
    def max_bytes(self) -> str:
        return f'{self.max_megabytes} MB'

    @property
    def retention(self) -> str:
        return f'{self.retention_days} days'


class AuthSettings(_TOMLSection):
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 1
    jwt_algorithm: Literal['HS256', 'RS256'] = 'RS256'
    jwt_issuer: str = 'fastapi-template'
    jwt_audience: str = 'fastapi-template'
    redis_token_prefix: str = 'auth:tokens:'
    exclude_routes: list[str] = ['/api/auth/login', '/api/auth/register']

    @property
    def access_token_exp(self) -> timedelta:
        return timedelta(minutes=self.access_token_expire_minutes)

    @property
    def refresh_token_exp(self) -> timedelta:
        return timedelta(days=self.refresh_token_expire_days)


class CrossOriginSettings(_TOMLSection):
    allow_origins: list[str] = ['*']
    allow_credentials: bool = True
    allow_methods: list[str] = ['*']
    allow_headers: list[str] = ['*']
    expose_headers: list[str] = []
    max_age: int | None = None
    supports_credentials: bool = True


class MiddlewareSettings(_TOMLSection):
    correlation_id_header: str = 'X-Request-ID'
    cors: CrossOriginSettings


class RedisClientOptions(_TOMLSection):
    socket_connection_timeout: float = 5.0
    socket_timeout: float = 5.0
    max_connections: int = 10
    health_check_interval: float = 10.0


class SQLAlchemyOptions(_TOMLSection):
    pool_recycle: int = 3600
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_pre_ping: bool = True
    pool_use_lifo: bool = False
    future: Literal[True] = True
    echo: bool = False
