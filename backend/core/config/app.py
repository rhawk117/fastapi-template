import functools
from typing import Annotated

from pydantic import Field

from .base import BaseAppSettings


class AppConfig(BaseAppSettings):
    DEBUG: Annotated[
        bool,
        Field(
            default=False,
            description='Whether or not the application is running in debug mode.',
        ),
    ]

    TESTING: Annotated[
        bool,
        Field(
            default=False,
            description='Whether or not the application is running in testing mode.',
        ),
    ]

    ALLOW_OPENAPI_ROUTES: Annotated[
        bool,
        Field(
            default=True,
            description='Whether or not to allow OpenAPI routes in the application.',
        ),
    ]

    SECRET_KEY: Annotated[
        str,
        Field(
            default='secret_key',
            description='Secret key for the application, used for cryptography',
        ),
    ]

    CSRF_KEY: Annotated[
        str,
        Field(
            default='csrf_key',
            description='CSRF key for the application, used for CSRF protection',
        ),
    ]

    ENCRYPTION_KEY: Annotated[
        str,
        Field(
            ...,
            description='Encryption key for the application, used for data encryption',
        ),
    ]

    ENCRYPTION_SALT: Annotated[
        str,
        Field(
            ...,
            description='Salt for the encryption key, used to enhance security',
        ),
    ]

    CORS_ALLOW_ORIGINS: Annotated[
        list[str],
        Field(
            default=['*'],
            description='List of allowed origins for CORS. Use "*" to allow all origins.',
        ),
    ]

    CORS_ALLOW_METHODS: Annotated[
        list[str],
        Field(
            default=['*'],
            description='List of allowed HTTP methods for CORS.',
        ),
    ]
    CORS_ALLOW_HEADERS: Annotated[
        list[str],
        Field(
            default=['*'],
            description='List of allowed headers for CORS. Use "*" to allow all headers.',
        ),
    ]
    CORS_ALLOW_CREDENTIALS: Annotated[
        bool,
        Field(
            default=True,
            description='Whether to allow credentials in CORS requests.',
        ),
    ]
    SIGNATURE_SALT: Annotated[
        str,
        Field(
            default='signature_salt',
            description='Salt used for signing data, enhancing security against tampering.',
        ),
    ]


@functools.lru_cache(maxsize=1)
def get_app_config() -> AppConfig:
    return AppConfig()  # type: ignore[return-value]
