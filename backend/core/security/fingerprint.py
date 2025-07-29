import dataclasses
import uuid
from typing import Self

import user_agents
from fastapi import Request


def get_request_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.client.host  # type: ignore

    return ip


@dataclasses.dataclass(slots=True)
class UserAgentInfo:
    user_agent: str
    device: str
    os: str
    browser: str
    is_bot: bool

    @classmethod
    def from_request(cls, request: Request) -> Self:
        """
        Creates a UserAgentInfo instance from a FastAPI Request object.

        Parameters
        ----------
        request : Request

        Returns
        -------
        Self
        """
        user_agent_str = request.headers.get('User-Agent', 'unknown')
        ua_info = user_agents.parse(user_agent_str)
        return cls(
            user_agent=user_agent_str,
            os=ua_info.get_os(),
            device=ua_info.get_device(),
            browser=ua_info.get_browser(),
            is_bot=ua_info.is_bot,
        )

    def __eq__(self, other: Self) -> bool:
        return (
            self.device == other.device
            and self.os == other.os
            and self.browser == other.browser
        )

    @property
    def uaid(self) -> str:
        """
        Generates a unique identifier for the user agent based
        on its properties.

        Returns
        -------
        str
            A unique identifier string.
        """
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, self.user_agent))


@dataclasses.dataclass(slots=True)
class ClientFingerprint:
    """
    Represents a unique fingerprint of a client based on IP address and user agent.
    """

    ip_address: str
    user_agent: UserAgentInfo

    @classmethod
    async def from_request(cls, request: Request) -> Self:
        ip = get_request_ip(request)
        user_agent = UserAgentInfo.from_request(request)
        return cls(ip_address=ip, user_agent=user_agent)

    def equals(self, other: Self) -> bool:
        return (
            self.ip_address == other.ip_address and self.user_agent == other.user_agent
        )

    def __eq__(self, other: Self) -> bool:
        return self.equals(other)

    def __repr__(self) -> str:
        return f'ClientFingerprint<ip={self.ip_address}, {self.user_agent}>'
