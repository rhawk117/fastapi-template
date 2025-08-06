from pydantic import Field, SecretStr
from pydantic_settings import (
    SettingsConfigDict,
)

from .settings_cls import Settings, TomlConfigFile
from .static import (
    AppSettings,
    AuthSettings,
    CrossOriginSettings,
    RedisOptions,
    SqlAlchemyOptions,
)


class AppConfig(TomlConfigFile):
    model_config = SettingsConfigDict(toml_file='config.toml')

    app: AppSettings
    auth: AuthSettings
    cors: CrossOriginSettings
    sqlalchemy: SqlAlchemyOptions
    redis: RedisOptions




class JwtSecrets(Settings):
    model_config = SettingsConfigDict(secrets_dir='keys')

    PRIVATE_KEY: SecretStr = Field(
        ...,
        description='The RSA private key used for signing JWT tokens',
        alias='private_key.pem',
    )

    PUBLIC_KEY: SecretStr = Field(
        ...,
        description='The RSA public key used for verifying JWT tokens',
        alias='public_key.pem',
    )

    PRIVATE_KEY_PASSWORD: SecretStr | None = Field(
        None,
        description='Optional password for the private key if it is encrypted',
        alias='private_key_password',
    )

    JWT_FINGERPRINT_SECRET: SecretStr = Field(
        ...,
        description='Secret used for JWT fingerprinting',
        alias='jwt_fingerprint'
    )





class SecuritySettings(Settings):
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    ENCRYPTION_SALT: str

    JWT_FINGERPRINT_SECRET: str = Field(
        ...,
        description='Secret used for JWT fingerprinting',
    )

    JWT_ALGORITHM: str = Field(
        ...,
        description='Algorithm used for signing JWT tokens',
    )




# class SecretSettings(_EnvSettings):
#     """
#     Environment variable secrets
#     """

#     SECRET_KEY: str

#     ENCRYPTION_KEY: str
#     ENCRYPTION_SALT: str

#     JWT_ALGORITHM: Literal['HS256', 'RS256']
#     JWT_FINGERPRINT_SECRET: str

#     PRIVATE_KEY_PASSWORD: str | None = None
#     PRIVATE_KEY_FILE: str
#     PUBLIC_KEY_FILE: str
#     BCRYPT_PEPPER: str | None = None

#     DATABASE_URL: str

#     REDIS_HOST: str = 'localhost'

#     REDIS_PASSWORD: str | None = None
#     REDIS_USERNAME: str | None = None

#     REDIS_PORT: int = 6379
#     REDIS_DB: int = 0

#     @property
#     def __keys_dir(self) -> Path:
#         root = Path(__file__).parent.parent.parent.resolve()
#         return root / 'keys'

#     def private_key_path(self) -> Path:
#         return self.__keys_dir / self.PRIVATE_KEY_FILE

#     def public_key_path(self) -> Path:
#         return self.__keys_dir / self.PUBLIC_KEY_FILE

#     @property
#     def private_key_password(self) -> bytes | None:
#         if self.PRIVATE_KEY_PASSWORD:
#             return self.PRIVATE_KEY_PASSWORD.encode('utf-8')
#         return None
