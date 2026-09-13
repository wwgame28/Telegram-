import asyncio
import ipaddress
import socket
from urllib.parse import urlparse


BLOCKED_HOSTS = {'localhost', 'localhost.localdomain'}


def _is_public_ip(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified)


async def is_safe_public_url(url: str) -> bool:
    p = urlparse(url)
    if p.scheme not in {'http', 'https'} or not p.hostname:
        return False
    host = p.hostname.strip().lower().rstrip('.')
    if host in BLOCKED_HOSTS or host.endswith('.local') or host.endswith('.internal'):
        return False
    try:
        if _is_public_ip(host):
            return True
        try:
            ipaddress.ip_address(host)
            return False
        except ValueError:
            pass
        loop = asyncio.get_running_loop()
        infos = await loop.run_in_executor(None, lambda: socket.getaddrinfo(host, p.port or (443 if p.scheme == 'https' else 80), type=socket.SOCK_STREAM))
        ips = {info[4][0].split('%')[0] for info in infos}
        return bool(ips) and all(_is_public_ip(ip) for ip in ips)
    except Exception:
        return False
