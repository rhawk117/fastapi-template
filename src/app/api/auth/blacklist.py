



import redis.asyncio as aioredis


def k_blacklist(jti: str) -> str:
    """
    Generate a Redis key for a JWT ID (JTI) blacklist.
    """
    return f'blacklist:{jti}'

class JtiBlacklistRepo:
    def __init__(self, redis: aioredis.Redis) -> None:
        self.redis: aioredis.Redis = redis

    async def add(self, jti: str, ttl: int) -> None:
        await self.redis.set(k_blacklist(jti), '1', ex=ttl)

    async def has_blacklisted(self, jti: str) -> bool:
        return bool(await self.redis.exists(k_blacklist(jti)))