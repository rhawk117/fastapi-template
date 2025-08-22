




import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from app.security import jwt as jwt_provider




def unixtznow() -> int:
    """
    Returns the current Unix timestamp in seconds, adjusted to UTC.
    """
    return int(datetime.now(UTC).timestamp())

def make_session_id() -> str:
    """
    Generates a new session ID.
    """
    return uuid.uuid4().hex


def create_token_claims(
    user_id: str,
    *,
    iat: int,
    ip: str,
    user_agent: str,
    scopes: list[str] | None = None,
) -> dict[jwt_provider.TokenType, TokenClaim]:

    session_id = make_session_id()

    refresh_claim = jwt_provider.create_jwt_claim(
        sub=user_id,
        iat=iat,
        token_type=jwt_provider.TokenType.REFRESH,
        scopes=scopes,
    )

    access_claim = jwt_provider.create_jwt_claim(
        sub=user_id,
        iat=iat,
        token_type=jwt_provider.TokenType.ACCESS,
        scopes=scopes,
    )
    encoded_access_token = jwt_provider.encode_jwt_claim(
        base_claim=access_claim,
        extras={
            'session_id': session_id,
        },
    )

    token_extra = {
        'session_id': session_id,
    }




