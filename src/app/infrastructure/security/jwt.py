import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any, NamedTuple, Protocol, Self

import jwt
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.settings import AuthSettings, CryptographySecrets


class TokenType(StrEnum):
    ACCESS = 'access'
    REFRESH = 'refresh'


class JwtPayload(BaseModel):
    """Comprehensive JWT payload model with all standard claims."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
        populate_by_name=True,
    )

    # (RFC 7519)
    sub: str = Field(..., description='Subject (user identifier)')

    iat: datetime = Field(..., description='Issued at time')

    exp: datetime = Field(..., description='Expiration time')

    nbf: datetime | None = Field(default=None, description='Not before time')

    iss: str = Field(..., description='Issuer')

    aud: list[str] = Field(..., description='Audience')

    jti: str = Field(
        ...,
        description='JWT ID for token revocation',
    )

    token_type: TokenType = Field(
        ...,
        description='Type of the token (access, refresh, email)',
    )

    fingerprint: str = Field(
        ...,
        description='Fingerprint hash of the user or device',
    )

    @field_validator('exp', 'nbf', mode='before')
    @classmethod
    def parse_timestamp(cls, v: int | float | datetime) -> datetime:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v, tz=timezone.utc)
        return v

    @model_validator(mode='after')
    def validate_temporal_claims(self) -> Self:
        if self.nbf and self.nbf > self.exp:
            raise ValueError("'nbf' must be before 'exp'")

        if self.iat > self.exp:
            raise ValueError("'iat' must be before 'exp'")

        return self

    def dump(self) -> dict[str, Any]:
        data = self.model_dump(exclude_none=True, mode='json')

        for field in ['iat', 'exp', 'nbf']:
            if field in data and data[field]:
                data[field] = int(datetime.fromisoformat(data[field]).timestamp())

        return data

    @classmethod
    def load(cls, data: dict[str, Any]) -> Self:
        for field in ['iat', 'exp', 'nbf']:
            if field in data and isinstance(data[field], (int, float)):
                data[field] = datetime.fromtimestamp(data[field], tz=timezone.utc)

        return cls(**data)


class JwtToken(NamedTuple):
    payload: JwtPayload
    encoded: str


class Fingerprintable(Protocol):
    def stringify(self) -> str: ...


class JwtClaimsService:
    def __init__(self, auth_settings: AuthSettings) -> None:
        self._auth_settings: AuthSettings = auth_settings

    def get_token_type_exp(self, token_type: TokenType) -> timedelta:
        if token_type == TokenType.ACCESS:
            return self._auth_settings.access_token_exp
        elif token_type == TokenType.REFRESH:
            return self._auth_settings.refresh_token_exp
        else:
            raise ValueError(f'Unknown token type: {token_type}')

    def create_claim(
        self,
        token_type: TokenType,
        *,
        fingerprint_hash: str,
        subject: str,
    ) -> JwtPayload:
        now = datetime.now(timezone.utc)

        exp = now + self.get_token_type_exp(token_type)

        jti = str(uuid.uuid4())

        payload = JwtPayload(
            sub=subject,
            iat=now,
            exp=exp,
            iss=self._auth_settings.jwt_issuer,
            aud=[self._auth_settings.jwt_audience],
            jti=jti,
            token_type=token_type,
            fingerprint=fingerprint_hash,
        )

        return payload


class JwtService:
    def __init__(
        self,
        *,
        crypto: CryptographySecrets,
        auth_settings: AuthSettings,
    ) -> None:
        self._crypto: CryptographySecrets = crypto
        self._settings: AuthSettings = auth_settings
        self._claims_maker: JwtClaimsService = JwtClaimsService(auth_settings)

    @property
    def _private_key(self) -> str:
        return self._crypto.rsa.private_key.get_secret_value()

    @property
    def public_key(self) -> str:
        return self._crypto.rsa.public_key.get_secret_value()

    @property
    def _jwt_fingerprint_secret(self) -> str:
        return self._crypto.jwt_fingerprint_secret.get_secret_value()

    @property
    def _fingerprint_secret(self) -> str:
        return self._crypto.jwt_fingerprint_secret.get_secret_value()

    def hash_fingerprint(self, fingerprintable: Fingerprintable) -> str:
        encoded_fingerprint = fingerprintable.stringify().encode('utf-8')
        secret = self._fingerprint_secret.encode('utf-8')
        return hmac.new(
            secret,
            encoded_fingerprint,
            hashlib.sha256,
        ).hexdigest()

    def check_fingerprint(
        self,
        *,
        client_fingerprint: Fingerprintable,
        token_payload: dict[str, Any]
    ) -> bool:
        claim_fingerprint = token_payload.get('fingerprint')
        if not claim_fingerprint:
            return False

        expected_fingerprint = self.hash_fingerprint(client_fingerprint)
        return hmac.compare_digest(expected_fingerprint, claim_fingerprint)

    def create_token(
        self,
        token_type: TokenType,
        *,
        fingerprint: Fingerprintable,
        subject: str,
    ) -> JwtToken:
        fingerprint_hash = self.hash_fingerprint(fingerprint)
        claims = self._claims_maker.create_claim(
            token_type=token_type,
            fingerprint_hash=fingerprint_hash,
            subject=subject,
        )

        token_dump = claims.dump()

        encoded_jwt = jwt.encode(
            token_dump,
            self._private_key,
            algorithm=self._settings.jwt_algorithm,
        )

        return JwtToken(payload=claims, encoded=encoded_jwt)

    def _validate_jwt(
        self,
        expected_type: TokenType,
        client_fingerprint: Fingerprintable,
        decoded_jwt: dict[str, Any],
    ) -> JwtPayload | None:
        if decoded_jwt.get('token_type') != expected_type:
            return None

        if not self.check_fingerprint(
            client_fingerprint=client_fingerprint,
            token_payload=decoded_jwt,
        ):
            return None

        return self.try_load_payload(decoded_jwt)

    def decode_jwt(
        self, encoded_jwt: str, *, verify_exp: bool = True
    ) -> dict[str, Any] | None:
        try:
            decoded_jwt = jwt.decode(
                encoded_jwt,
                self.public_key,
                algorithms=[self._settings.jwt_algorithm],
                options={
                    'verify_exp': verify_exp,
                    'verify_iat': True,
                    'verify_nbf': True,
                    'require_exp': True,
                    'require_iat': True,
                    'require_sub': True,
                },
            )
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

        return decoded_jwt

    def try_load_payload(self, data: dict[str, Any]) -> JwtPayload | None:
        try:
            return JwtPayload.load(data)
        except ValueError:
            return None

    def load_jwt(
        self,
        encoded_jwt: str,
        client_fingerprint: Fingerprintable,
        *,
        expected_type: TokenType,
        verify_exp: bool = True,
    ) -> JwtPayload | None:
        decoded_jwt = self.decode_jwt(encoded_jwt, verify_exp=verify_exp)
        if not decoded_jwt:
            return None

        return self._validate_jwt(
            expected_type=expected_type,
            client_fingerprint=client_fingerprint,
            decoded_jwt=decoded_jwt,
        )


async def get_jwt_service(
    crypto: CryptographySecrets,
    auth_settings: AuthSettings,
) -> JwtService:
    return JwtService(crypto=crypto, auth_settings=auth_settings)
