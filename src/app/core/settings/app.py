from pydantic import Field

from .base import TomlSettings


class DocsConfig(TomlSettings):
    docs_url: str = Field(
        '/docs', description='The URL for the SwaggerUI documentation route.'
    )

    redoc_url: str = Field(
        '/redoc', description='The URL for the ReDoc documentation route.'
    )

    openapi_url: str = Field(
        '/openapi.json', description='The URL for the OpenAPI schema.'
    )

    allow_docs: bool = Field(
        True, description='Whether to allow the SwaggerUI documentation route or not.'
    )


class OpenAPIConfig(TomlSettings):
    title: str = Field(
        'range-monitor-api',
        description='The name of the application, used in the OpenAPI documentation and other places.',
    )

    description: str = Field(
        'A RESTful API for the Cyber Range Monitor',
        description='The description of the application, used in the OpenAPI documentation.',
    )

    version: str = Field(
        '0.1.0',
        description='The version of the application, used in the OpenAPI documentation.',
    )

    summary: str = Field(
        'Cyber Range Monitor API',
        description='A brief summary of the application, used in the OpenAPI documentation.',
    )


class AppConfig(TomlSettings):
    label: str = Field(
        ...,
        description="The label for the config mapped to the file name (e.g 'dev' -> 'config-dev.yml')",
    )

    debug: bool = Field(
        False,
        description='Enables debug mode for fastapi resulting in tracebacks in responses, DISABLE IN PRODUCTION',
    )

    env_file: str = Field(
        '.env', description='The path to the .env file to load the secrets from.'
    )

    testing: bool = Field(
        False,
        description='Enables testing mode, note if not enabled during testing errors may occur',
    )

    openapi: OpenAPIConfig
    docs: DocsConfig
