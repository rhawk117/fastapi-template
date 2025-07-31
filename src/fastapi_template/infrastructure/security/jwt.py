import functools
import hashlib
import hmac
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from fastapi_template.core import settings


def _read_key_file_bytes(file_path: Path) -> bytes:
    if not file_path.exists():
        raise FileNotFoundError(f'Key file {file_path} does not exist.')
    with file_path.open('rb') as key_file:
        return key_file.read()


def _read_private_key(private_key_password: bytes | None) -> rsa.RSAPrivateKey:
    private_key_file = settings.get_secrets().private_key_path()
    private_key_data = _read_key_file_bytes(private_key_file)
    return serialization.load_pem_private_key(
        private_key_data,
        password=private_key_password,  # type: ignore
    )


def _read_public_key() -> rsa.RSAPublicKey:
    public_key_file = settings.get_secrets().public_key_path()
    public_key_data = _read_key_file_bytes(public_key_file)
    return serialization.load_pem_public_key(public_key_data)  # type: ignore


@functools.lru_cache(maxsize=None)
def _get_private_key(private_key_password: bytes | None = None) -> bytes:
    return _read_private_key(private_key_password).private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


@functools.lru_cache(maxsize=None)
def get_public_key() -> bytes:
    return _read_public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def encode_jwt_payload(token_payload: dict) -> str:
    """
    Encodes the JWT token with the provided payload and
    cryptographic context.

    Parameters
    ----------
    token_payload : dict
    context : _JWTCryptography

    Returns
    -------
    str
    """
    algorithm = settings.get_config_file().auth.jwt_algorithm
    return jwt.encode(
        token_payload,
        _get_private_key(),
        algorithm=algorithm,
    )


def decode_jwt_payload(encoded_token: str) -> dict:
    """
    Simply decodes the JWT token and returns the payload, does not verify the
    fingerprint only the claims like issuer, audience, etc. It is the caller's responsibility
    to do so.

    Parameters
    ----------
    encoded_token : str
    context : _JWTCryptography

    Returns
    -------
    dict

    Raises
    ------
    jwt.DecodeError: If the token is invalid or expired.
    jwt.ExpiredSignatureError: If the token has expired.
    """
    config = settings.get_config_file()
    return jwt.decode(
        encoded_token,
        get_public_key(),
        algorithms=[config.auth.jwt_algorithm],
        issuer=config.auth.jwt_issuer,
        audience=config.auth.jwt_audience,
        options={
            'verify_signature': True,
            'verify_exp': True,
            'verify_nbf': True,
            'verify_iat': True,
            'verify_aud': True,
            'verify_iss': True,
        },
    )


def hash_client_fingerprint(client_fingerprint: bytes) -> str:
    """
    Hashes the client fingerprint using the JWT fingerprint secret.

    Parameters
    ----------
    client_fingerprint : bytes

    Returns
    -------
    str
    """
    secret = settings.get_secrets().JWT_FINGERPRINT_SECRET
    return hmac.new(
        secret.encode('utf-8'),
        client_fingerprint,
        hashlib.sha256,
    ).hexdigest()


def check_client_fingerprint(
    client_fingerprint: bytes, expected_fingerprint: str
) -> bool:
    """
    Checks if the client fingerprint matches the expected fingerprint.
    Parameters
    ----------
    client_fingerprint : bytes
    expected_fingerprint : str
    Returns
    -------
    bool
    """
    actual_fingerprint = hash_client_fingerprint(client_fingerprint)
    return hmac.compare_digest(actual_fingerprint, expected_fingerprint)


class TokenType(StrEnum):
    """
    Enum for the different types of tokens.
    """

    ACCESS = 'access'
    REFRESH = 'refresh'


@dataclass(slots=True, kw_only=True, frozen=True)
class TokenClaim:
    token_type: TokenType
    jti: str
    iat: int
    exp: int
    aud: str
    iss: str


def create_token_claim(token_type: TokenType) -> TokenClaim:
    config = settings.get_config_file()
    now = datetime.now(timezone.utc)

    if token_type == TokenType.ACCESS:
        expires_at = now + config.auth.access_token_exp
    else:
        expires_at = now + config.auth.refresh_token_exp

    return TokenClaim(
        token_type=token_type,
        jti=str(uuid.uuid4()),
        iat=int(now.timestamp()),
        exp=int(expires_at.timestamp()),
        aud=config.auth.jwt_audience,
        iss=config.app.name,
    )
