



import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Self, TypedDict

from jose import jwt
from jose.exceptions import JWTError
from msgspec import field

from app.core import settings


class JwtParams(TypedDict):
    iss: str # issuer
    aud: str | list[str]  # audience
    sub: str # subject (user id)
    exp: int # expiration (unix seconds)
    iat: int # issued-at (unix seconds)
    nbf: int  # not-before (unix seconds)
    jti: str  # unique token id
    token_type: str


def utc_now() -> datetime:
    """
    Returns the current UTC datetime.
    """
    return datetime.now(UTC)


class TokenType(StrEnum):
    ACCESS = 'access'
    REFRESH = 'refresh'


def get_token_type_ttl(
    token_type: TokenType,
    *,
    config: settings.JwtConfig | None = None
) -> int:

    jwt_settings = config or settings.get_app_settings().jwt
    return (
        jwt_settings.access_token_ttl
        if token_type == TokenType.ACCESS
        else jwt_settings.refresh_token_ttl
    )

def generate_jti() -> str:
    return str(uuid.uuid4())


def _jwt_parameterize(
    sub: str,
    iat: int,
    token_type: TokenType,
) -> JwtParams:
    '''
    Creates a JWT claim with the given subject, token type, and optional scopes.

    Parameters
    ----------
    sub : str
    token_type : TokenType
    scopes : list[str] | None, optional

    Returns
    -------
    JwtClaim
    '''
    config = settings.get_app_settings().jwt
    exp_modifier = get_token_type_ttl(token_type, config=config)

    exp = iat + exp_modifier

    return JwtParams(
        iss=config.ISSUER,
        aud=config.AUDIENCE,
        sub=sub,
        exp=exp,
        iat=iat,
        nbf=iat,
        jti=generate_jti(),
        token_type=token_type.value,
    )




def generate_sid() -> str:
    """
    Generates a new session ID.
    """
    return uuid.uuid4().hex


def encode_payload(
    base_claim: dict,
    *,
    headers: dict | None = None,
) -> str:
    """
    Given a base JWT claim, it will then be encoded into a
    JWT token.

    Parameters
    ----------
    base_claim : JwtClaim
    extras : dict | None, optional
    headers : dict | None, optional

    Returns
    -------
    JwtToken
    """
    config = settings.get_app_settings()

    claim: dict = dict(base_claim.copy())

    _private_key = config.rs256.PRIVATE_KEY.get_secret_value()
    return jwt.encode(
        claim,
        key=_private_key,
        algorithm=config.jwt.ALGORITHM,
        headers=headers or {},
    )

def decode_jwt_token(token: str) -> dict | None:
    """
    Decodes a JWT token and verifies its claims, returns None if verification fails

    Parameters
    ----------
    token : str
        _description_
    expected_type : Literal[&#39;access&#39;, &#39;refresh&#39;] | None, optional
        _description_, by default None

    Returns
    -------
    dict | None
        _description_
    """
    config = settings.get_app_settings()
    public_key = config.rs256.PUBLIC_KEY.get_secret_value()
    try:
        claim_payload = jwt.decode(
            token,
            key=public_key,
            algorithms=[config.jwt.ALGORITHM],
            audience=config.jwt.AUDIENCE,
            issuer=config.jwt.ISSUER,
            options={
                'verify_signature': True,
                'verify_exp': True,
                'verify_nbf': True,
                'verify_iat': True,
                'verify_aud': True,
                'require_exp': True,
                'require_iat': True,
                'require_nbf': True,
                # "leeway": self.settings.leeway_seconds,
            },
        )
    except JWTError:
        return None

    return claim_payload





def validate_jwt_claim(
    claim_payload: dict | None,
    *,
    expected_type: TokenType
) -> bool:
    '''
    Validates the JWT claim payload to ensure it has
    the correct token type.

    Parameters
    ----------
    claim_payload : dict | None
    expected_type : Literal['access', 'refresh']

    Returns
    -------
    bool
    '''
    if not claim_payload:
        return False

    if not (claim_type := claim_payload.get('token_type')):
        return False

    if claim_type not in (TokenType.ACCESS.value, TokenType.REFRESH.value):
        return False

    if claim_type != expected_type.value:
        return False

    return True


def unsafe_jwt_decode(token: str) -> dict | None:
    try:
        return jwt.get_unverified_claims(token)
    except JWTError:
        return None

