import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from .config import settings

_hasher = PasswordHasher()  # Argon2id with the library's recommended parameters
_LEGACY_PREFIX = "pbkdf2_sha256$"  # format: pbkdf2_sha256$<salt>$<hex digest>
_LEGACY_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def legacy_hash(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _LEGACY_ITERATIONS)
    return f"{_LEGACY_PREFIX}{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> tuple[bool, bool]:
    """Return (valid, needs_rehash). Old PBKDF2 hashes verify once, then get upgraded."""
    if stored.startswith(_LEGACY_PREFIX):
        parts = stored.split("$")
        if len(parts) != 3:
            return False, False
        return hmac.compare_digest(legacy_hash(password, parts[1]), stored), True
    try:
        _hasher.verify(stored, password)
    except (VerificationError, InvalidHashError):
        return False, False
    return True, _hasher.check_needs_rehash(stored)


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def new_opaque_token() -> str:
    return secrets.token_urlsafe(32)


def utcnow() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    """SQLite returns naive datetimes; they were stored as UTC."""
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def create_access_token(user_id: int) -> str:
    now = utcnow()
    claims = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_ttl_minutes),
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> int | None:
    try:
        claims = jwt.decode(
            token, settings.jwt_secret, algorithms=["HS256"], options={"require": ["exp", "sub"]}
        )
    except jwt.PyJWTError:
        return None
    if claims.get("type") != "access":
        return None
    return int(claims["sub"])
