import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .settings import get_crypto_settings


def _create_fernet() -> Fernet:
    crypto_settings = get_crypto_settings()
    encoded_enc_salt = crypto_settings.ENCRYPTION_SALT.encode('utf-8')
    key_bytes = crypto_settings.ENCRYPTION_KEY.encode('utf-8')
    pdkdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=crypto_settings.PBKDF2_KEY_LENGTH,
        salt=encoded_enc_salt,
        iterations=crypto_settings.PBKDF2_ITERATIONS,
    )
    key = base64.urlsafe_b64encode(pdkdf.derive(key_bytes))
    return Fernet(key)


_fernet = _create_fernet()


def encrypt_to_bytes(input_str: str) -> bytes:
    return _fernet.encrypt(input_str.encode('utf-8'))


def encrypt_string(input_str: str) -> str:
    return encrypt_to_bytes(input_str).decode('utf-8')


def decrypt_to_bytes(input_str: str, *, ttl: int | None = None) -> bytes:
    return _fernet.decrypt(input_str, ttl=ttl)


def decrypt_string(input_str: str, *, ttl: int | None = None) -> str:
    return decrypt_to_bytes(input_str, ttl=ttl).decode('utf-8')
