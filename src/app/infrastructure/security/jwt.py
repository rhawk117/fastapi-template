from datetime import datetime, UTC
import secrets
import uuid
from pydantic import Field, ConfigDict, BaseModel, field_validator
from enum import StrEnum
from typing import Annotated, Final, NamedTuple, TypedDict
import time
from .settings import jwt_settings, get_crypto_settings
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError, JWTClaimsError


class SessionStatus(StrEnum):
    ACTIVE = 'active'
    EXPIRED = 'expired'
    REVOKED = 'revoked'
    LOCKED = 'locked'


class TokenType(StrEnum):
    ACCESS = 'access'
    REFRESH = 'refresh'


class JwtPayload(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    sub: Annotated[str, Field(description='Subject (user ID)', min_length=1)]
    jti: Annotated[str, Field(description='JWT ID', min_length=1)]
    iat: Annotated[int, Field(description='Issued at timestamp', ge=0)]
    exp: Annotated[int, Field(description='Expiration timestamp', ge=0)]
    iss: Annotated[str, Field(description='Issuer', min_length=1)]
    aud: Annotated[str, Field(description='Audience', min_length=1)]
    token_type: Annotated[TokenType, Field(description='Token type')]
    extras: dict = Field(
        default_factory=dict,
        description='Additional claims or data',
    )


def current_time() -> int:
    return int(datetime.now(UTC).timestamp())


def create_jti() -> str:
    return str(uuid.uuid4())


class JwtToken(NamedTuple):
    token: str
    payload: JwtPayload


class JwtErrorCodes(StrEnum):
    MALFORM_TOKEN = 'malformed_token'
    EXPIRED_TOKEN = 'expired_token'
    INVALID_CLAIMS = 'invalid_signature'
    UNKNOWN_TOKEN_TYPE = 'unknown_token_type'
    WRONG_TOKEN_TYPE = 'wrong_token_type'
    INVALID_PAYLOAD = 'invalid_payload'


class BadJWTError(Exception):
    """Base class for JWT errors."""

    def __init__(
        self, error_code: JwtErrorCodes, message: str, *, expired: bool = False
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.expired = expired
        super().__init__(message)


class DecodedJwtResult(TypedDict):
    success: bool
    error_code: JwtErrorCodes | None
    message: str | None
    claim: JwtPayload | None


class _JwtManager:
    def __init__(self) -> None:
        self.secret_key: str = get_crypto_settings().SECRET_KEY
        self.algorithm: str = jwt_settings.algorithm
        self.issuer: str = jwt_settings.issuer
        self.audience: str = jwt_settings.audience

    def get_token_exp(self, token_type: TokenType) -> int:
        if token_type == TokenType.ACCESS:
            return jwt_settings.access_token_exp
        elif token_type == TokenType.REFRESH:
            return jwt_settings.refresh_token_exp
        else:
            raise ValueError(f'Unknown token type: {token_type}')

    @property
    def decoding_options(self) -> dict:
        return {
            'verify_signature': True,
            'verify_exp': True,
            'verify_iat': True,
            'verify_iss': True,
            'verify_aud': True,
            'require_exp': True,
            'require_iat': True,
            'require_iss': True,
            'require_aud': True,
        }

    def create_jwt_payload(
        self,
        user_id: str,
        token_type: TokenType,
        **kwargs
    ) -> JwtPayload:
        now = current_time()
        jti = create_jti()
        expires = now + self.get_token_exp(token_type)

        return JwtPayload(
            sub=user_id,
            jti=jti,
            iat=now,
            exp=expires,
            iss=self.issuer,
            aud=self.audience,
            token_type=token_type,
            extras=kwargs,
        )

    def create_token(
        self,
        user_id: str,
        session_id: str,
        *,
        token_type: TokenType,
        **kwargs,
    ) -> JwtToken:
        payload = self.create_jwt_payload(
            user_id=user_id, session_id=session_id, token_type=token_type, **kwargs
        )

        payload_dict = payload.model_dump(mode='json')

        return JwtToken(
            token=self.encode(payload_dict),
            payload=payload, 
        )

    def encode(self, payload: dict) -> str:
        return jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )

    def _decode_fail(self, error_code: JwtErrorCodes, message: str) -> DecodedJwtResult:
        return {
            'success': False,
            'error_code': error_code,
            'message': message,
            'claim': None,
        }

    def decode_token(
        self, encoded_token: str, *, token_type: TokenType
    ) -> DecodedJwtResult:
        """
        Decodes a JWT token and returns a JwtPayload instance.

        Parameters
        ----------
        encoded_token : str

        Returns
        -------
        JwtPayload

        Raises
        ------
        BadJWTError
            _when the token is malformed, expired, or has invalid claims_
        """
        try:
            paylod_dict = jwt.decode(
                encoded_token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience,
                options=self.decoding_options,
            )
        except ExpiredSignatureError:
            return self._decode_fail(
                JwtErrorCodes.EXPIRED_TOKEN,
                'Token has expired',
            )
        except JWTClaimsError as exc:
            return self._decode_fail(
                JwtErrorCodes.INVALID_CLAIMS,
                f'Invalid claims: {exc}',
            )
        except JWTError as exc:
            return self._decode_fail(
                JwtErrorCodes.MALFORM_TOKEN,
                f'Malformed token: {exc}',
            )

        try:
            decoded_type = TokenType(paylod_dict.get('token_type'))
            if decoded_type is None or decoded_type not in (
                TokenType.ACCESS,
                TokenType.REFRESH,
            ):
                return self._decode_fail(
                    JwtErrorCodes.UNKNOWN_TOKEN_TYPE,
                    f'Unknown token type: {token_type}',
                )

            if decoded_type != token_type:
                return self._decode_fail(
                    JwtErrorCodes.WRONG_TOKEN_TYPE,
                    f'Expected token type {token_type}, got {decoded_type}',
                )
            claim = JwtPayload.model_validate(paylod_dict)

        except Exception:
            return self._decode_fail(
                JwtErrorCodes.INVALID_PAYLOAD,
                'Invalid token payload',
            )

        return {
            'success': True,
            'error_code': None,
            'message': None,
            'claim': claim,
        }

    def extract_jti(self, encoded_token: str) -> str | None:
        try:
            unverified_payload = jwt.get_unverified_claims(encoded_token)
            return unverified_payload.get('jti')
        except JWTError:
            return None

    def has_token_expired(self, encoded_token: str) -> bool:
        """
        Checks if the token has expired.

        Parameters
        ----------
        encoded_token : str

        Returns
        -------
        bool
            True if the token has expired, False otherwise.
        """
        try:
            unverified_payload = jwt.get_unverified_claims(encoded_token)
            if not (exp := unverified_payload.get('exp')):
                return True
            return current_time() > exp
        except BadJWTError:
            return True


JwtManager: Final[_JwtManager] = _JwtManager()
