import ipaddress

import user_agents
from fastapi import Request


def get_network_prefix(
    ip_address: str,
    *,
    v4_prefix: int = 24,
    v6_prefix: int = 64,
) -> str:
    network_addr = ip_address

    try:
        addr = ipaddress.ip_address(ip_address)

        prefix = v4_prefix if addr.version == 4 else v6_prefix
        network = ipaddress.ip_network(f'{ip_address}/{prefix}', strict=False)
        network_addr = str(network.network_address)
    except Exception:
        pass

    return network_addr

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


def get_user_agent(request: Request) :
    user_agent_str = request.headers.get('User-Agent')
    return user_agents.parse(user_agent_str)




