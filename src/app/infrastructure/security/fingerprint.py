import ipaddress
import hashlib
import user_agents
from dataclasses import dataclass

from fastapi import Request
from fastapi import Request

from typing import Self
from app.core.pydantic import CustomBaseModel


@dataclass(slots=True, frozen=True)
class IpInfo:
    """
    Utility class for storing and manipulating client IP addresses.
    """

    ip_address: str

    def get_network_prefix(
        self,
        ip_address: str,
        *,
        v4_prefix: int = 24,
        v6_prefix: int = 64,
    ) -> str:
        network_addr = self.ip_address

        try:
            addr = ipaddress.ip_address(ip_address)

            prefix = v4_prefix if addr.version == 4 else v6_prefix
            network = ipaddress.ip_network(f'{ip_address}/{prefix}', strict=False)
            network_addr = str(network.network_address)
        except Exception:
            pass

        return network_addr


def get_request_ip(
    request: Request,
    *,
    request_header: str | None,
) -> str:
    """
    Extracts the client's IP address from the request.

    Parameters
    ----------
    request : Request
    request_header : str | None, optional
        _if none uses X-Forwarded-For_, by default None

    Returns
    -------
    str
    """
    hdr = request_header or 'X-Forwarded-For'

    x_forwarded_for = request.headers.get(hdr)
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.client.host  # type: ignore

    return ip


@dataclass(slots=True, frozen=True)
class UserAgentInfo:
    """Parsed user agent string from the request headers."""

    user_agent: str
    device: str
    os: str
    browser: str
    is_bot: bool

    def __repr__(self) -> str:
        return (
            f'UserAgentInfo<os={self.os}_device={self.device}'
            f'browser={self.browser}_is_bot={self.is_bot}>'
        )

    def identifier(self) -> str:
        return f'{self.os}.{self.device}.{self.browser}'


async def parse_user_agent(request: Request) -> UserAgentInfo:
    user_agent_str = request.headers.get('User-Agent')
    ua_info = user_agents.parse(user_agent_str)
    return UserAgentInfo(
        user_agent=user_agent_str or 'unknown',
        os=ua_info.get_os(),
        device=ua_info.get_device(),
        browser=ua_info.get_browser(),
        is_bot=ua_info.is_bot,
    )


async def parse_request_ip(
    request: Request,
    *,
    request_header: str | None = None,
) -> IpInfo:
    ip_address = get_request_ip(request, request_header=request_header)
    return IpInfo(ip_address=ip_address)


def get_request_path(request: Request) -> str:
    """
    Extracts the path from the request URL.

    Parameters
    ----------
    request : Request

    Returns
    -------
    str
        The path of the request URL.
    """
    return (
        request.url.path
        if not request.url.query
        else request.url.path + '/' + request.url.query
    )


class RequestFingerprint(CustomBaseModel):
    ip: IpInfo
    user_agent: UserAgentInfo
    salt: str | None = None
    request_path: str | None = None

    @property
    def id(self) -> str:
        return f'{self.ip.ip_address}.{self.user_agent.identifier()}'

    @classmethod
    async def parse_request(
        cls,
        request: Request,
        *,
        ip_header: str | None = None,
    ) -> Self:
        """
        Parses the request to extract the fingerprint information.

        Parameters
        ----------
        request : Request
            The FastAPI request object.
        """
        ip = await parse_request_ip(request, request_header=ip_header)
        user_agent = await parse_user_agent(request)
        request_path = get_request_path(request)
        return cls(
            ip=ip,
            user_agent=user_agent,
            request_path=request_path,
        )


def hash_fingerprint(
    fingerprint: RequestFingerprint, *, salt: str | None = None
) -> str:
    encoded = fingerprint.id
    if salt:
        encoded = f'{salt}{encoded}'
    return hashlib.sha256(encoded.encode('utf-8')).hexdigest()


def check_fingerprint(
    fingerprint: RequestFingerprint, fingerprint_hash: str, *, salt: str | None = None
) -> bool:
    """
    Checks if the fingerprint matches the given hash.

    Parameters
    ----------
    fingerprint : RequestFingerprint
        The fingerprint to check.
    fingerprint_hash : str
        The hash to compare against.
    salt : str | None
        An optional salt to use in the hash comparison.

    Returns
    -------
    bool
        True if the fingerprint matches the hash, False otherwise.
    """
    return hash_fingerprint(fingerprint, salt=salt) == fingerprint_hash
