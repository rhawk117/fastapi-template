from __future__ import annotations

import time
from datetime import datetime
from typing import TYPE_CHECKING

from .const import SESSION_EXPIRATION, SESSION_MAX_LIFETIME
from .repository import SessionRepository
from .schema import SessionData, SessionHealth, SessionInfo

if TYPE_CHECKING:
    from backend.core.security.fingerprint import ClientFingerprint


def has_expired(start_time: float, duration: float) -> bool:
    elapsed = time.time() - start_time
    remaining = duration - elapsed
    return remaining <= 0


class SessionService:
    """
    The SessionService is responsible for creating, storing, and retrieving Session IDs
    from the redis repository. The Session Service is also responsible for checking if the
    Session ID has reached the maximum lifetime and revoking the API Key if it has been
    hijacked.

    Everytime a key is retrieved and is valid the lifetime or time before it expires is
    extended in redis
    """

    def __init__(self, session_store: SessionRepository) -> None:
        self._repository: SessionRepository = session_store

    async def create_session(
        self,
        *,
        username: str,
        role: str,
        client: ClientFingerprint
    ) -> str:
        """
        Creates a session key, encrypts the SessionData before storing it in redis and
        returns a signed session key.

        The server generates a key that is digitally signed and salted by the
        server corresponding to a an unsigned key to an encrypted redis dictionary based
        on "SessionData" which is set to expire after an hour.

        If the client sends another request to the API within the SESSION_EXPIRATION
        (1 hour), the key is then extended to expire after another hour.


        Parameters
        ----------
        username : str
        role : str
        client : ClientFingerprint

        Returns
        -------
        str
        """
        session_payload = SessionData.create(
            username=username, role=role, client=client
        )
        signed_key = await self._repository.register_session(
            payload=session_payload.model_dump(),
            ex=SESSION_EXPIRATION,  # NOTE: it's important that this is NOT the max age
        )
        return signed_key

    async def load_session(
        self, signed_key: str, inbound_client: ClientFingerprint
    ) -> SessionData | None:
        """
        gets the session data from the signed_key from the client cookies and checks
        if the max lifetime is reached, if it was issued by the server and exists in the
        redis session store. The API key if the max lifetime hasn't been reached refreshes
        the session expiration in the redis store

        returns none if the session is invalid or expired

        Parameters
        ----------
        signed_key : str
        inbound_client : ClientFingerprint

        Returns
        -------
        SessionData | None
        """

        session_payload = await self._repository.get_session(
            signed_key=signed_key, max_age=SESSION_MAX_LIFETIME
        )
        if not session_payload:
            return None

        try:
            session_payload = SessionData(**session_payload)
        except Exception:
            return None

        session_highjacked = not session_payload.trusts_client(inbound_client)
        session_expired = has_expired(session_payload.created_at, SESSION_MAX_LIFETIME)

        if session_expired or session_highjacked:
            await self._repository.delete_session(signed_key, SESSION_MAX_LIFETIME)
            return None

        await self._repository.extend_session(
            signed_key=signed_key,
            ex=SESSION_EXPIRATION,
            max_age=SESSION_MAX_LIFETIME,  # NOTE: this is the max age not the expiration
        )

        return session_payload

    async def revoke(self, signed_key: str | None) -> None:
        """
        Revokes the session id by deleting it from the redis store

        Parameters
        ----------
        signed_key : str | None
        """
        if signed_key:
            await self._repository.delete_session(signed_key, SESSION_MAX_LIFETIME)

    async def get_session_health(self, signed_key: str) -> SessionInfo | None:
        """
        Gets the time to live of the api key in redis

        Parameters
        ----------
        signed_key : str

        Returns
        -------
        SessionInfo | None
            the session info if the key is valid, otherwise None
        """
        session_dump = await self._repository.get_session(
            signed_key, SESSION_MAX_LIFETIME
        )
        if not session_dump:
            return None
        try:
            session_payload = SessionData(**session_dump)
        except Exception:
            return None

        health = await self.inspect_session_health(session_payload, signed_key)
        return SessionInfo(owner=session_payload.identity, health=health)

    async def inspect_session_health(
        self, session_payload: SessionData, signed_key: str
    ) -> SessionHealth:
        next_exp_ms = await self._repository.get_session_ttl(
            signed_session_id=signed_key, max_age=SESSION_MAX_LIFETIME
        )
        next_exp = time.time() + next_exp_ms
        max_age_exp_seconds = session_payload.created_at + SESSION_MAX_LIFETIME

        return SessionHealth(
            max_age_at=datetime.fromtimestamp(max_age_exp_seconds),
            expires_next=datetime.fromtimestamp(next_exp),
            issued_at=datetime.fromtimestamp(session_payload.created_at),
        )
