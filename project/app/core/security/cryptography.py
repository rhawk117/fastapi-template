import base64
from typing import ClassVar

from app.core.config import get_app_config
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from itsdangerous import URLSafeTimedSerializer
from passlib.context import CryptContext

from .const import PBKDF2_ITERATIONS, PBKDF2_KEY_LENGTH


def create_fernet() -> Fernet:
    app_config = get_app_config()
    encoded_salt = app_config.ENCRYPTION_SALT.encode('utf-8')
    key_bytes = app_config.ENCRYPTION_KEY.encode('utf-8')
    pdkdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=PBKDF2_KEY_LENGTH,
        salt=encoded_salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key = base64.urlsafe_b64encode(pdkdf.derive(key_bytes))
    return Fernet(key)


def create_serializer() -> URLSafeTimedSerializer:
    app_config = get_app_config()
    return URLSafeTimedSerializer(app_config.SECRET_KEY, salt=app_config.SIGNATURE_SALT)


def create_hashing_context() -> CryptContext:
    return CryptContext(schemes=['bcrypt'], deprecated='auto')


class CryptoUtils:
    fernet: ClassVar[Fernet] = create_fernet()
    serializer: ClassVar[URLSafeTimedSerializer] = create_serializer()
    hash_context: ClassVar[CryptContext] = create_hashing_context()

    @classmethod
    def encrypt(cls, input_string: str) -> str:
        return cls.fernet.encrypt(input_string.encode()).decode()

    @classmethod
    def decrypt(cls, input_string: str) -> str:
        return cls.fernet.decrypt(input_string.encode()).decode()

    @classmethod
    def hash(cls, input_string: str) -> str:
        return cls.hash_context.hash(input_string)

    @classmethod
    def verify_hash(cls, *, plain_text: str, hashed_text: str) -> bool:
        return cls.hash_context.verify(plain_text, hashed_text)

    @classmethod
    def sign(cls, value: str) -> str:
        signature_salt = get_app_config().SIGNATURE_SALT
        return cls.serializer.dumps(value, salt=signature_salt)

    @classmethod
    def unsign(cls, value: str, max_age: int) -> str:
        signature_salt = get_app_config().SIGNATURE_SALT
        return cls.serializer.loads(value, salt=signature_salt, max_age=max_age)
