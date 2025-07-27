import base64
from typing import ClassVar

from app.core.config import get_app_config
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from itsdangerous import URLSafeTimedSerializer
from passlib.context import CryptContext

from .const import PBKDF2_ITERATIONS, PBKDF2_KEY_LENGTH

__all__ = ['CryptoUtils']


def _create_fernet() -> Fernet:
    config = get_app_config()
    encoded_salt = config.ENCRYPTION_SALT.encode('utf-8')
    key_bytes = config.ENCRYPTION_KEY.encode('utf-8')
    pdkdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=PBKDF2_KEY_LENGTH,
        salt=encoded_salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key = base64.urlsafe_b64encode(pdkdf.derive(key_bytes))
    return Fernet(key)


def _create_url_serializer() -> URLSafeTimedSerializer:
    config = get_app_config()
    return URLSafeTimedSerializer(
        secret_key=config.SECRET_KEY, salt=config.ENCRYPTION_SALT
    )


def _create_hashing_context() -> CryptContext:
    return CryptContext(schemes=['bcrypt'], deprecated='auto')


class CryptoUtils:
    fernet: ClassVar[Fernet] = _create_fernet()
    url_serializer: ClassVar[URLSafeTimedSerializer] = _create_url_serializer()
    hashing_context: ClassVar[CryptContext] = _create_hashing_context()

    @classmethod
    def encrypt(cls, input_string: str) -> str:
        return cls.fernet.encrypt(input_string.encode()).decode()

    @classmethod
    def decrypt(cls, encrypted_string: str) -> str:
        return cls.fernet.decrypt(encrypted_string.encode()).decode()

    @classmethod
    def hash(cls, input_string: str) -> str:
        return cls.hashing_context.hash(input_string)

    @classmethod
    def verify_hash(cls, *, plain_text: str, hashed_text: str) -> bool:
        return cls.hashing_context.verify(plain_text, hashed_text)

    @classmethod
    def sign(cls, data: str) -> str:
        salt = get_app_config().ENCRYPTION_SALT
        return cls.url_serializer.dumps(data, salt=salt)

    @classmethod
    def unsign(cls, signed_data: str, *, max_age: int | None = None) -> str:
        salt = get_app_config().ENCRYPTION_SALT
        return cls.url_serializer.loads(signed_data, salt=salt, max_age=max_age)
