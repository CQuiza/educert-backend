"""JWT, hashing de contraseñas y refresh tokens (OAuth2 compatible)."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import bcrypt
from jose import JWTError, jwt

from app.core.settings import get_settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Hashea con bcrypt. El coste se controla con rounds (default 12)."""
    settings = get_settings()
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(UTC) + expires_delta
    to_encode: dict[str, Any] = {
        "exp": expire,
        "sub": str(subject),
        "jti": str(uuid4()),
        "iat": datetime.now(UTC),
    }
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as e:
        raise ValueError("Token inválido") from e


def generate_refresh_token() -> str:
    """Genera un token opaco (no-JWT) para refresh."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """SHA-256 del refresh token para almacenar en BD."""
    return hashlib.sha256(token.encode()).hexdigest()


REFRESH_TOKEN_DAYS = 30


def refresh_token_expires_at() -> datetime:
    return datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_DAYS)
