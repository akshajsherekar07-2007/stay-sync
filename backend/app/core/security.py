"""Security utilities — password hashing and JWT token management.

All cryptographic operations are centralized here.  No other module
should import ``passlib`` or ``jose`` directly.

Public API
----------
hash_password(plain)              → bcrypt hash string
verify_password(plain, hashed)    → bool
create_access_token(subject, role, extra) → signed JWT string
create_refresh_token()            → (raw_token, token_hash)
decode_access_token(token)        → payload dict
hash_token(raw)                   → SHA-256 hex digest
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedException

# ── bcrypt context ────────────────────────────────────────────────────────────
# 12 rounds per PROJECT_RULES.md §6.
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of ``plain``.

    Args:
        plain: The raw plaintext password.

    Returns:
        A bcrypt hash string (60 chars, starts with ``$2b$``).
    """
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Compare ``plain`` against a stored bcrypt hash.

    Uses constant-time comparison internally — safe against timing attacks.

    Args:
        plain:  Raw plaintext password supplied by the user.
        hashed: The stored bcrypt hash to compare against.

    Returns:
        ``True`` if the password matches, ``False`` otherwise.
    """
    return _pwd_context.verify(plain, hashed)


# ── JWT access tokens ─────────────────────────────────────────────────────────

def create_access_token(
    subject: str,
    role: str,
    extra: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        subject: The user UUID (stored as ``sub`` claim).
        role:    The user's role string (``student``, ``owner``, ``admin``).
        extra:   Optional additional claims merged into the payload.

    Returns:
        A signed JWT string (HS256).
    """
    settings = get_settings()
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": expire,
        **(extra or {}),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Args:
        token: The raw JWT string (without the ``Bearer `` prefix).

    Returns:
        The decoded payload dictionary.

    Raises:
        UnauthorizedException: If the token is missing, expired, or has an
            invalid signature.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise UnauthorizedException(
            message="Invalid or expired access token",
            code="INVALID_TOKEN",
        ) from exc

    return payload


# ── Refresh tokens ────────────────────────────────────────────────────────────

def create_refresh_token() -> tuple[str, str]:
    """Generate a cryptographically secure refresh token pair.

    The raw token is delivered to the client via an HttpOnly cookie.
    The hash is stored in the database — the raw token is never persisted.

    Returns:
        A tuple of ``(raw_token, token_hash)`` where:
        - ``raw_token``  is a URL-safe base64 string (256-bit entropy).
        - ``token_hash`` is the SHA-256 hex digest of ``raw_token``.
    """
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)


def hash_token(raw: str) -> str:
    """Return the SHA-256 hex digest of a raw token string.

    Used to convert a raw refresh token into the hash stored in the DB.

    Args:
        raw: The raw token string.

    Returns:
        Lowercase hex string of the SHA-256 digest (64 chars).
    """
    return hashlib.sha256(raw.encode()).hexdigest()
