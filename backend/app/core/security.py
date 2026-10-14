"""Cryptographic and Authentication Security Functions.

Provides industry-standard bcrypt password hashing, JWT token lifecycle management,
and brute-force attempt rate limiting.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
import time
from typing import Any, Dict, Optional, Tuple
import bcrypt
import jwt

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an authoritative bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate a high-entropy bcrypt hash with standard work factor."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a signed JWT access token containing minimal necessary claims."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,
        "iss": settings.APP_NAME,
    })

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and cryptographically verify a JWT access token."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        issuer=settings.APP_NAME,
    )


# In-memory sliding window rate limiter for auth abuse protection
class AuthRateLimiter:
    """In-memory rate limiter tracking recent attempts by client identifier."""

    def __init__(self) -> None:
        # Dict mapping identifier -> list of timestamps
        self._attempts: Dict[str, list[float]] = defaultdict(list)

    def is_rate_limited(
        self,
        identifier: str,
        max_attempts: Optional[int] = None,
        window_seconds: Optional[int] = None,
    ) -> bool:
        max_att = max_attempts or settings.AUTH_RATE_LIMIT_MAX_ATTEMPTS
        window = window_seconds or settings.AUTH_RATE_LIMIT_WINDOW_SECONDS
        now = time.time()

        # Filter out expired timestamps
        timestamps = [ts for ts in self._attempts[identifier] if now - ts < window]
        self._attempts[identifier] = timestamps

        return len(timestamps) >= max_att

    def record_attempt(self, identifier: str) -> None:
        """Record an attempt timestamp."""
        self._attempts[identifier].append(time.time())

    def reset(self, identifier: str) -> None:
        """Clear attempts on successful authentication."""
        if identifier in self._attempts:
            del self._attempts[identifier]


auth_rate_limiter = AuthRateLimiter()
