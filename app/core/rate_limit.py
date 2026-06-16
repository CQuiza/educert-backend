"""Limiter compartido para rate limiting."""

from slowapi import Limiter
from starlette.requests import Request


def _rate_limit_key(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    ip = forwarded.split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )
    ua = request.headers.get("User-Agent", "unknown")[:50]
    return f"{ip}:{ua}"


limiter = Limiter(key_func=_rate_limit_key)
