from datetime import timedelta
import secrets
from typing import Annotated, Literal

from cryptography.fernet import Fernet
from pydantic import Field

from app.core.settings import Settings, TomlSettings, create_toml_settings, load_secret_settings


class CryptoSettings(Settings):
    ENCRYPTION_KEY: str = Field(
        ..., description='The key used for encryption and decryption of sensitive data.'
    )

    ENCRYPTION_SALT: str = Field(
        ...,
        description='The salt used for encryption and decryption of sensitive data.',
    )

    PBKDF2_ITERATIONS: int = Field(
        100_000,
        description='The number of iterations for the PBKDF2 key derivation function.',
    )

    PBKDF2_KEY_LENGTH: int = Field(
        32, description='The length of the key derived from PBKDF2.'
    )

    SECRET_KEY: str = Field(
        ...,
        description='The secret key used for signing tokens and other cryptographic operations.',
    )

    BCRYPT_PEPPER: str = Field(
        ...,
        description='The pepper used for bcrypt hashing of passwords.',
    )


class TemporaryCryptoSecrets(CryptoSettings):
    """Temporary secrets for cryptographic operations."""

    ENCRYPTION_KEY: str = Fernet.generate_key().decode('utf-8')

    ENCRYPTION_SALT: str = secrets.token_urlsafe(32)
    SECRET_KEY: str = secrets.token_urlsafe(32)
    SIGNATURE_SALT: str = secrets.token_urlsafe(32)
    BCRYPT_PEPPER: str = secrets.token_urlsafe(32)


_crypto_settings: CryptoSettings = load_secret_settings(
    settings_class=CryptoSettings,
    testing_fallback_cls=TemporaryCryptoSecrets,
)


def get_crypto_settings() -> CryptoSettings:
    return _crypto_settings


JwtAlgorithm = Literal['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']


class JWTSettings(TomlSettings):
    algorithm: Annotated[
        JwtAlgorithm,
        Field(description='JWT algorithm'),
    ] = 'HS256'

    access_token_expire_mins: Annotated[
        int,
        Field(description='Access token expiration time in minutes'),
    ] = 60

    refresh_token_expire_days: Annotated[
        int,
        Field(description='Refresh token expiration time in days',),
    ] = 1

    issuer: Annotated[
        str,
        Field(description='Issuer of the JWT tokens'),
    ] = 'fastapi-template'

    audience: Annotated[
        str,
        Field(description='Audience of the JWT tokens')
    ]

    @property
    def refresh_token_exp(self) -> int:
        return int(timedelta(days=self.refresh_token_expire_days).total_seconds())

    @property
    def access_token_exp(self) -> int:
        return int(timedelta(minutes=self.access_token_expire_mins).total_seconds())


jwt_settings: JWTSettings = create_toml_settings(
    settings_class=JWTSettings,
    section_name='jwt'
)
