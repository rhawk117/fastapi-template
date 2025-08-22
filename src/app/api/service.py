




import uuid
from datetime import UTC, datetime
from app.security import jwt as jwt_provider



def new_session_id() -> str:
    return uuid.uuid4().hex


def unixnow() -> int:
    """
    Returns the current Unix timestamp in seconds.
    """
    return int(datetime.now(UTC).timestamp())


async def create_session(
    user_id: str,
    *,
    ip: str,
    user_agent: str,
    scopes: list[str] | None = None,
)
