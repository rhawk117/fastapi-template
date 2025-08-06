import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Protocol

import jwt

from app.core.settings import AuthSettings, JwtSecrets

from .schema import JwtClaim, TokenType


class Fingerprintable(Protocol):
    def stringify(self) -> str: ...


class JwtService:
    def __init__(self, secrets: JwtSecrets, auth_settings: AuthSettings) -> None:
        self._secrets: JwtSecrets = secrets
        self._auth_settings: AuthSettings = auth_settings

    def _get_token_type_exp(self, token_type: TokenType) -> timedelta:
        if token_type == TokenType.ACCESS:
            return self._auth_settings.access_token_exp
        elif token_type == TokenType.REFRESH:
            return self._auth_settings.refresh_token_exp
        else:
            raise ValueError(f'Unknown token type: {token_type}')

    def create_jwt_claim(
        self, *, token_type: TokenType, sub: str, fingerprint: Fingerprintable
    ) -> JwtClaim:
        now = datetime.now(timezone.utc)

        claim_fingerprint = self.create_fingerprint(fingerprint)
        expires_at = now + self._get_token_type_exp(token_type)

        return JwtClaim(
            iss=self._auth_settings.jwt_issuer,
            token_type=token_type,
            sub=sub,
            exp=int(expires_at.timestamp()),
            aud=self._auth_settings.jwt_audience,
            fingerprint_hash=claim_fingerprint,
            iat=int(now.timestamp()),
        )

    def create_fingerprint(self, fingerprint: Fingerprintable) -> str:
        """
        Creates a fingerprint string from the provided Fingerprintable object.

        Parameters
        ----------
        fingerprint : Fingerprintable
            An object that implements the stringify method.

        Returns
        -------
        str
            The fingerprint string.
        """
        encoded_fingerprint = fingerprint.stringify().encode('utf-8')
        secret = self._secrets.JWT_FINGERPRINT_SECRET.get_secret_value()
        return hmac.new(
            secret.encode('utf-8'),
            encoded_fingerprint,
            hashlib.sha256,
        ).hexdigest()

    def check_fingerprint(
        self, client_fingerprint: Fingerprintable, token_payload: dict
    ) -> bool:
        client_hash = self.create_fingerprint(client_fingerprint)
        expected_hash = token_payload.get('fingerprint_hash', '')

        return hmac.compare_digest(client_hash, expected_hash)

    def encode_payload(self, token_payload: dict) -> str:
        """
        Encodes the JWT payload using the configured JWT algorithm.

        Parameters
        ----------
        token_payload : dict
            The payload to encode.

        Returns
        -------
        str
            The encoded JWT token.
        """
        private_key = self._secrets.PRIVATE_KEY.get_secret_value()
        return jwt.encode(
            payload=token_payload,
            key=private_key,
            algorithm=self._auth_settings.jwt_algorithm,
        )

    def decode_payload(self, encoded_token: str) -> JwtClaim | None:
        """
        Decodes the JWT token and returns the claim.

        Parameters
        ----------
        encoded_token : str
            The JWT token to decode.

        Returns
        -------
        JwtClaim
            The decoded JWT claim.
        """
        public_key = self._secrets.PUBLIC_KEY.get_secret_value()

        try:
            payload = jwt.decode(
                jwt=encoded_token,
                key=public_key,
                algorithms=[self._auth_settings.jwt_algorithm],
                audience=self._auth_settings.jwt_audience,
                issuer=self._auth_settings.jwt_issuer,
                options={
                    'require': ['exp', 'aud', 'iss'],
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_nbf': True,
                    'verify_iat': True,
                    'verify_aud': True,
                    'verify_iss': True,
                },
            )
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

        return self.try_load_jwt_claim(payload)

    def try_load_jwt_claim(self, payload: dict) -> JwtClaim | None:
        """
        Attempts to load a JWT claim from the provided payload.

        Parameters
        ----------
        payload : dict
            The JWT payload to load the claim from.

        Returns
        -------
        JwtClaim | None
            The loaded JWT claim or None if the payload is invalid.
        """
        try:
            return JwtClaim.model_validate(payload)
        except Exception:
            return None

    def get_public_key(self) -> str:
        """
        Returns the public key used for JWT verification.

        Returns
        -------
        str
            The public key.
        """
        return self._secrets.PUBLIC_KEY.get_secret_value()


async def get_jwt_service(
    jwt_secrets: JwtSecrets, auth_settings: AuthSettings
) -> JwtService:
    """
    Asynchronously creates and returns an instance of JwtService.

    Parameters
    ----------
    jwt_secrets : JwtSecrets
        The JWT secrets configuration.
    auth_settings : AuthSettings
        The authentication settings configuration.

    Returns
    -------
    JwtService
        An instance of JwtService.
    """
    return JwtService(secrets=jwt_secrets, auth_settings=auth_settings)
