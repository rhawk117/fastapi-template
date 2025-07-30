import json
import secrets

from backend.core.security.cryptography import CryptoUtils
from backend.redis.client import redis_client


def session_key(key: str) -> str:
    return f'auth:sessions:{key}'


class SessionRepository:
    """Class to interact with the redis key store for API Keys"""

    def resolve_signature(self, signed_session_id: str, max_age: int) -> str | None:
        """
        Resolves the signed session ID to the unsigned session ID
        that can be used in the redis store

        Parameters
        ----------
        signed_session_id : str
            the signed session id
        max_age : int
            the max age of the key

        Returns
        -------
        str | None
            the unsigned api key or none if the signature is invalid
        """

        try:
            unsigned_session_id = CryptoUtils.unsign(signed_session_id, max_age)
        except Exception:
            return None

        return unsigned_session_id

    def create_session_id(self) -> str:
        """
        Creates a new session id

        Returns
        -------
        str
            the session id
        """
        return secrets.token_urlsafe(32)

    async def register_session(self, payload: dict, ex: int | None = None) -> str:
        """
        Creates a session id and stores the payload in the redis store
        and returns the signed key that should be issued to the client.

        Parameters
        ----------
        payload : dict
            the payload to be stored in the redis store
        ex : int | None, optional
            the seconds before the key expires, by default None

        Returns
        -------
        str
            the signed key to be issued to the client
        """
        unsigned_session_id = self.create_session_id()
        payload_str = json.dumps(payload)
        await redis_client.set(session_key(unsigned_session_id), payload_str, ex=ex)
        return CryptoUtils.sign(unsigned_session_id)

    async def get_session(self, signed_session_id: str, max_age: int) -> dict | None:
        """
        resolves the signed session id to the payload stored in redis

        Parameters
        ----------
        signed_session_id : str
            the client's signed session id
        max_age : int
            the max age of the key

        Returns
        -------
        dict | None
            the payload stored in redis or None if the key is invalid
        """
        unsigned_session_id = self.resolve_signature(signed_session_id, max_age)
        if not unsigned_session_id:
            return None

        json_payload = await redis_client.get(session_key(unsigned_session_id))
        if not json_payload:
            return None

        payload = None
        try:
            payload = json.loads(json_payload)
        except Exception:
            pass

        return payload

    async def delete_session(self, signed_session_id: str, max_age: int) -> None:
        """
        Deletes the session id from the redis store

        Parameters
        ----------
        signed_session_id : str
        max_age : int
        """
        unsigned_session_id = self.resolve_signature(signed_session_id, max_age)
        if not unsigned_session_id:
            return
        await redis_client.delete(session_key(unsigned_session_id))

    async def extend_session(
        self, signed_session_id: str, ex: int, max_age: int
    ) -> None:
        """
        Extends the session id in the redis store

        Parameters
        ----------
        signed_session_id : str
        ex : int
        max_age : int
        """
        unsigned_session_id = self.resolve_signature(signed_session_id, max_age)
        if not unsigned_session_id:
            return
        await redis_client.expire(session_key(unsigned_session_id), ex)

    async def get_session_ttl(self, signed_session_id: str, max_age: int) -> int:
        """
        Gets the time to live of the session id in the redis store

        Parameters
        ----------
        signed_session_id : str
        max_age : int

        Returns
        -------
        int
            the time to live of the session id in seconds, or 0 if the key is invalid
        """
        unsigned_session_id = self.resolve_signature(signed_session_id, max_age)
        if not unsigned_session_id:
            return 0
        ttl = await redis_client.ttl(session_key(unsigned_session_id))
        return ttl if ttl >= 0 else 0
