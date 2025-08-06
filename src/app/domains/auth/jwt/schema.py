import uuid
from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class TokenType(StrEnum):
    ACCESS = 'access'
    REFRESH = 'refresh'


class JwtClaim(BaseModel):
    sub: str
    token_type: TokenType
    jti: uuid.UUID = Field(default_factory=uuid.uuid4)
    iat: int
    exp: int
    iss: str
    aud: str
    fingerprint_hash: str

    @field_validator('iat', 'exp', mode='before')
    @classmethod
    def _to_utc(cls, v):
        if isinstance(v, (int, float)):  # epoch seconds
            v = datetime.fromtimestamp(v, tz=timezone.utc)
        if v.tzinfo is None:  # naive → UTC
            v = v.replace(tzinfo=timezone.utc)
        return v


class AccessTokenClaims(JwtClaim):
    token_type: TokenType = TokenType.ACCESS


class RefreshTokenClaims(JwtClaim):
    token_type: TokenType = TokenType.REFRESH
