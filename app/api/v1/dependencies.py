"""Dependencias: OAuth2 JWT y usuarios opcionales."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user_repository import user_repository

_settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{_settings.api_v1_prefix}/auth/token",
    auto_error=False,
)


async def get_token_from_request(request: Request) -> str:
    token = await oauth2_scheme(request)
    if token:
        return token
    token = request.cookies.get("access_token")
    if token:
        return token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_token_from_request(request: Request) -> str | None:
    token = await oauth2_scheme(request)
    if token:
        return token
    return request.cookies.get("access_token")


def _decode_user_id(token: str) -> int:
    try:
        payload = decode_token(token)
        return int(payload.get("sub"))
    except (ValueError, TypeError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(get_token_from_request)],
) -> User:
    uid = _decode_user_id(token)
    user = await user_repository.get_by_id(db, uid)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo o inexistente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_optional_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str | None, Depends(get_optional_token_from_request)],
) -> User | None:
    if not token:
        return None
    try:
        uid = _decode_user_id(token)
    except HTTPException:
        return None
    user = await user_repository.get_by_id(db, uid)
    if not user or not user.is_active:
        return None
    return user
