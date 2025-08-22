

from datetime import datetime

import redis.asyncio as aioredis

from app.api.auth.model import SessionModel, SessionStatus


def rkey(*args: str) -> str:
    """
    Generate a Redis key by joining the provided arguments with a colon.
    """
    return ':'.join(args)

def k_session(session_id: str) -> str:
    """
    Generate a Redis key for a session using the session ID.
    """
    return rkey('session', session_id)

def k_user_sessions(user_id: str) -> str:
    """
    Generate a Redis key for user sessions using the user ID.
    """
    return rkey('user', 'sessions', user_id)

def k_touched(session_id: str) -> str:
    """
    Generate a Redis key for tracking the last touched time of a session.
    """
    return rkey('session', 'touched', session_id)

def unixstamped(dt: datetime) -> int:
    """
    Get the current Unix timestamp in seconds.
    """
    return int(dt.timestamp())


class SessionRepo:

    def __init__(self, redis: aioredis.Redis) -> None:
        self.redis: aioredis.Redis = redis

    async def create(self, session: SessionModel) -> None:
        pipeline = self.redis.pipeline()
        session_key = k_session(session.session_id)
        user_sessions_key = k_user_sessions(session.user_id)

        pipeline.hset(session_key, mapping=session.dump())
        pipeline.zadd(user_sessions_key, {
            session.session_id: session.last_seen
        })
        await pipeline.execute()

    async def get(self, session_id: str) -> SessionModel | None:
        data = await self.redis.hgetall(k_session(session_id)) # type: ignore
        if not data:
            return None
        return SessionModel.convert(data)

    async def list_sessions(self, user_id: str, *, limit: int = 50) -> list[SessionModel]:
        user_key = k_user_sessions(user_id)
        session_ids = await self.redis.zrevrange(user_key, 0, limit - 1)
        if not session_ids:
            return []
        pipeline = self.redis.pipeline()
        for session_id in session_ids:
            pipeline.hgetall(k_session(session_id))
        rows = await pipeline.execute()

        sessions = []
        for dump in rows:
            if not dump:
                continue
            sessions.append(SessionModel.convert(dump))

        return sessions

    async def touch_last_seen(
        self,
        session_id: str,
        user_id: str,
        now_unix: int,
        *,
        throttle_sec: int = 60
    ) -> None:

        touch_key = k_touched(session_id)
        if not await self.redis.set(touch_key, now_unix, ex=throttle_sec, nx=True):
            return

        session_key = k_session(session_id)
        user_sessions_key = k_user_sessions(user_id)
        pipeline = self.redis.pipeline()
        pipeline.hset(session_key, mapping={
            'last_seen': now_unix,
        })
        pipeline.zadd(user_sessions_key, {
            session_id: now_unix
        })
        await pipeline.execute()

    async def remove(self, session_id: str, *, reason: str | None = None) -> None:
        session = await self.get(session_id)
        if not session:
            return
        session_key = k_session(session_id)
        user_sessions_key = k_user_sessions(session.user_id)
        pipeline = self.redis.pipeline()
        pipeline.hset(session_key, mapping={
            'status': SessionStatus.REVOKED,
            'revoked_reason': reason or 'revoked',
        })
        pipeline.zrem(user_sessions_key, session_id)
        await pipeline.execute()

    async def remove_all(self, user_id: str, *, reason: str | None = None) -> None:

        user_key = k_user_sessions(user_id)
        session_ids = await self.redis.zrange(user_key, 0, -1)
        if not session_ids:
            return
        pipeline = self.redis.pipeline()
        for session_id in session_ids:
            pipeline.hset(
                k_session(session_id),
                mapping={
                    'status': SessionStatus.REVOKED,
                    'revoked_reason': reason or 'revoked',
                }
            )
        pipeline.delete(user_key)
        await pipeline.execute()
