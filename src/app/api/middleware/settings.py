import uuid

from pydantic import Field

from app.core.settings import TomlSettings, create_toml_settings

SECTION_NAME = 'middleware'


class CORSConfig(TomlSettings):
    allow_origins: list[str] = Field(
        default=['*'], description='The allowed origins for CORS requests'
    )

    allow_methods: list[str] = Field(
        default=['*'], description='The allowed methods for CORS requests'
    )

    allow_headers: list[str] = Field(
        default=['*'], description='The allowed headers for CORS requests'
    )

    allow_credentials: bool = Field(
        default=True, description='Whether to allow credentials for CORS requests'
    )


class CorrelationIdConfig(TomlSettings):
    header_name: str = Field(
        default='X-Request-ID',
        description='The name of the header used for correlation IDs',
    )

    update_request_header: bool = Field(
        default=True,
        description='Whether to update the request header with the correlation ID',
    )

    return_header: bool = Field(
        default=True,
        description='Whether to return the correlation ID in the response header',
    )

    def id_factory(self) -> uuid.UUID:
        """
        Generates a new UUID for the correlation ID.

        Returns
        -------
        uuid.UUID
            A new UUID instance.
        """
        return uuid.uuid4()


class MiddlewareSetttings(TomlSettings):
    cors: CORSConfig
    correlation_id: CorrelationIdConfig

    allowed_hosts: list[str] | None = Field(
        default=None,
        description='List of allowed hosts for the application. If None, all hosts are allowed.',
    )


middleware_settings: MiddlewareSetttings = create_toml_settings(
    MiddlewareSetttings,
    section_name=SECTION_NAME,
)
