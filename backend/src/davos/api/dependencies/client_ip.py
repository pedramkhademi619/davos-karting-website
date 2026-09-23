from __future__ import annotations

from fastapi import Request


def client_ip(request: Request) -> str:
    """The peer address as resolved by the ASGI server.

    Behind the reverse proxy run uvicorn with ``--proxy-headers --forwarded-allow-ips=<proxy>`` so
    this is the real client and X-Forwarded-For from untrusted peers is ignored.
    """
    return request.client.host if request.client else "unknown"
