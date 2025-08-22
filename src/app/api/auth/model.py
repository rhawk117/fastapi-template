


from __future__ import annotations

from enum import StrEnum

from app.core.schema import PydanticSchema


class SessionStatus(StrEnum):
    ACTIVE = 'active'
    REVOKED = 'revoked'


class SessionModel(PydanticSchema):
    session_id: str
    user_id: str
    user_agent: str
    ip_address: str
    created_at: int
    last_seen: int
    refresh_jti: str
    rotation_count: int = 0
    status: SessionStatus = SessionStatus.ACTIVE
    revoked_reason: str | None = None

    @classmethod
    def keys(cls) -> list[str]:
        return list(cls.model_fields.keys())
