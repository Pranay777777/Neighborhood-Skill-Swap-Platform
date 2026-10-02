"""Per-client rate limits on the endpoints that take a password or send mail.

Counters live in memory: fine for one free-tier instance, reset on restart, not shared
between instances (see README limitations).
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from .config import settings


def client_ip(request: Request) -> str:
    """Behind a trusted proxy (Render), the rightmost X-Forwarded-For entry is the address
    the proxy itself saw and appended - a client cannot forge it. Anywhere else, trust only
    the socket, or a client could pick a fresh "IP" per request."""
    forwarded = request.headers.get("x-forwarded-for")
    if settings.trust_proxy and forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=client_ip, enabled=settings.rate_limit_enabled)


def too_many(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        {"detail": "Too many attempts. Wait a minute and try again."},
        status_code=429,
        headers={"Retry-After": "60"},
    )
