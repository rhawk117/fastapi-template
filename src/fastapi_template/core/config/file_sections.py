from datetime import timedelta
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class _ConfigFileSection(BaseModel):
    pass


class AppDocsConfig(_ConfigFileSection):
    enabled: Annotated[
        bool, Field(default=True, description='Enable or disable OpenAPI documentation')
    ]
    openapi_url: str = '/openapi.json'
    docs_url: str = '/docs'
    redoc_url: str = '/redoc'


class AppOptions(_ConfigFileSection):
    doc_routes_okay: Annotated[
        bool,
        Field(
            default=False,
            description='Enable or disable OpenAPI documentation routes',
        ),
    ]
    log_level: Annotated[
        Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        Field(default='INFO', description='Logging level for the application'),
    ]

    file_logging_okay: Annotated[
        bool, Field(default=True, description='Enable file logging')
    ]
    env_file: str = '.env'

    openapi_url: str = '/openapi.json'
    docs_url: str = '/docs'
    redoc_url: str = '/redoc'

    @property
    def doc_routes(self) -> dict:
        if self.doc_routes_okay:
            return {
                'openapi_url': self.openapi_url,
                'docs_url': self.docs_url,
                'redoc_url': self.redoc_url,
            }
            
        return {
            'openapi_url': None,
            'docs_url': None,
            'redoc_url': None,
        }


class AppSettings(_ConfigFileSection):
    debug: Annotated[bool, Field(default=False, description='Enable debug mode')]
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
    options: AppOptions

    @property
    def fastapi_kwargs(self) -> dict:
        base_options = self.model_dump(exclude_none=True, exclude={'options'})
        return {
            **base_options,
            **self.options.doc_routes,
        }


class SecuritySettings(_ConfigFileSection):
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


class CrossOriginSettings(_ConfigFileSection):
    allow_origins: list[str] = ['*']
    allow_credentials: bool = True
    allow_methods: list[str] = ['*']
    allow_headers: list[str] = ['*']
    expose_headers: list[str] = []
    max_age: int | None = None
    supports_credentials: bool = True


class MiddlewareSettings(_ConfigFileSection):
    correlation_id_header: str = 'X-Request-ID'
    cors: CrossOriginSettings


class RedisClientOptions(_ConfigFileSection):
    socket_connection_timeout: float = 5.0
    socket_timeout: float = 5.0
    max_connections: int = 10
    health_check_interval: float = 10.0


class SQLAlchemyOptions(_ConfigFileSection):
    pool_recycle: int = 3600
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_pre_ping: bool = True
    pool_use_lifo: bool = False
    future: Literal[True] = True
    echo: bool = False
