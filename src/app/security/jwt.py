



import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import NamedTuple, TypedDict

from jose import jwt
from jose.exceptions import JWTError

from app.core import settings


class JwtClaim(TypedDict):
    iss: str # issuer
    aud: str | list[str]  # audience
    sub: str # subject (user id)
    exp: int # expiration (unix seconds)
    iat: int # issued-at (unix seconds)
    nbf: int # not-before (unix seconds)
    jti: str # unique token id
    token_type: str
    scopes: list[str] | None


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


def create_jwt_claim(
    sub: str,
    token_type: TokenType,
    scopes: list[str] | None = None,
) -> JwtClaim:
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
    now = utc_now()
    issued_at = int(now.timestamp())
    exp_modifier = get_token_type_ttl(token_type, config=config)

    duration = now + timedelta(seconds=exp_modifier)
    expires = int(duration.timestamp())

    return JwtClaim(
        iss=config.ISSUER,
        aud=config.AUDIENCE,
        sub=sub,
        exp=expires,
        iat=issued_at,
        nbf=issued_at,
        jti=generate_jti(),
        token_type=token_type.value,
        scopes=scopes or [],
    )


class JwtToken(NamedTuple):
    '''
    Typed tuple representing an encoded JWT token and
    its payload.
    '''
    token: str
    payload: dict

def encode_jwt_claim(
    base_claim: JwtClaim,
    *,
    extras: dict | None = None,
    headers: dict | None = None,
) -> JwtToken:
    '''
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
    '''
    config = settings.get_app_settings()

    claim: dict = dict(base_claim.copy())
    if extras:
        claim.update(extras)

    _private_key = config.rs256.PRIVATE_KEY.get_secret_value()

    encoded_token = jwt.encode(
        claim,
        key=_private_key,
        algorithm=config.jwt.ALGORITHM,
        headers=headers or {},
    )

    return JwtToken(
        token=encoded_token,
        payload=claim,
    )

def decode_jwt_token(token: str) -> dict | None:
    '''
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
    '''
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
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": True,
                "require_exp": True,
                "require_iat": True,
                "require_nbf": True,
                # "leeway": self.settings.leeway_seconds,
            }
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

