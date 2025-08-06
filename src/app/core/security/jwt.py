import hashlib
import hmac
from typing import ClassVar, Protocol

import jwt

from app.core.settings import core

from ._keys import AsymmetricKeyPair


def _create_asymmetric_keys() -> AsymmetricKeyPair:
    secrets = core.get_secrets()
    return AsymmetricKeyPair.from_files(
        private_key_file=secrets.private_key_path(),
        public_key_file=secrets.public_key_path(),
        private_key_password=secrets.PRIVATE_KEY_PASSWORD,
    )


class Fingerprint(Protocol):
    def stringify(self) -> str: ...


class _JWTSecurity:
    _jwt_keys: ClassVar[AsymmetricKeyPair] = _create_asymmetric_keys()
    _alogrithm: ClassVar[str] = core.get_secrets().JWT_ALGORITHM

    @classmethod
    def get_public_key(cls) -> bytes:
        """
        Returns the public key used for JWT decoding.
        """
        return cls._jwt_keys.public_key

    @classmethod
    def encode_payload(cls, token_payload: dict) -> str:
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
        return jwt.encode(
            token_payload,
            key=cls._jwt_keys.private_key,
            algorithm=cls._alogrithm,
        )

    @classmethod
    def decode_token(cls, encoded_token: str, *, issuer: str, audience: str) -> dict:
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
        config = core.get_config()
        return jwt.decode(
            encoded_token,
            cls._jwt_keys.public_key,
            algorithms=[config.auth.jwt_algorithm],
            issuer=issuer,
            audience=audience,
            options={
                'verify_signature': True,
                'verify_exp': True,
                'verify_nbf': True,
                'verify_iat': True,
                'verify_aud': True,
                'verify_iss': True,
            },
        )

    @classmethod
    def create_fingerprint(cls, client_fingerprint: Fingerprint) -> str:
        """
        Hashes the client fingerprint using the JWT fingerprint secret.

        Parameters
        ----------
        client_fingerprint : bytes

        Returns
        -------
        str
        """
        enocded_fingerprint = client_fingerprint.stringify().encode()

        secret = core.get_secrets().JWT_FINGERPRINT_SECRET
        return hmac.new(
            secret.encode('utf-8'),
            enocded_fingerprint,
            hashlib.sha256,
        ).hexdigest()

    @classmethod
    def check_fingerprint(
        cls, client_fingerprint: Fingerprint, expected_hash: str | None
    ) -> bool:
        return hmac.compare_digest(
            cls.create_fingerprint(client_fingerprint),
            expected_hash or '',
        )


JWTSecurity = _JWTSecurity()
