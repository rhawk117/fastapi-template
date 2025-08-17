from pydantic import Field, SecretStr
from pydantic_settings import SettingsConfigDict

from .settings_cls import Settings


class RSASecretKeys(Settings):
    model_config = SettingsConfigDict(secrets_dir='keys')

    public_key: SecretStr = Field(
        ...,
        description='The private key used for signing JWT tokens',
        alias='private_key.pem',
    )

    private_key: SecretStr = Field(
        ...,
        description='The public key used for verifying JWT tokens',
        alias='public_key.pem',
    )


class CryptographySecrets(Settings):
    rsa: RSASecretKeys

    hs256_secret: SecretStr = Field(
        ...,
        description='The secret key used for HS256 signing',
    )

    bcrypt_pepper: SecretStr = Field(
        ...,
        description='Pepper for bcrypt hashing',
    )

    secret_key: SecretStr = Field(
        ...,
        description='A secret key used for various cryptographic operations',
    )

    jwt_fingerprint_secret: SecretStr = Field(
        ...,
        description='Secret used for JWT fingerprinting',
    )


class RedisSecrets(Settings):
    model_config = SettingsConfigDict(env_prefix='REDIS_')

    host: str = Field(
        default='localhost',
        description='Redis host address',
    )

    port: int = Field(
        default=6379,
        description='Redis port number',
    )

    username: str | None = Field(
        default=None,
        description='Redis username, if applicable',
    )

    password: str | None = Field(
        default=None,
        description='Redis password, if applicable',
    )

    db: int = Field(
        default=0,
        description='Redis database number',
    )

    ssl: bool = Field(
        default=False,
        description='Whether to use SSL for Redis connection',
    )


class DatabaseSecrets(Settings):
    model_config = SettingsConfigDict(env_prefix='DATABASE_')

    url: str = Field(
        ...,
        description='Database connection URL',
    )
