"""Auditoría de usuarios eliminados."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.user_audit_repository import user_audit_repository
from app.schemas.user_audit import UserAuditRead
from app.services.access import is_super_or_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-audit", tags=["user-audit"])


@router.get("", response_model=list[UserAuditRead])
async def list_user_audit(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
) -> list:
    if not is_super_or_admin(current):
        logger.warning("Acceso denegado a user-audit — user=%s", current.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    rows = await user_audit_repository.list(db, skip=skip, limit=limit)
    logger.info("user-audit listado — count=%s, by=%s", len(rows), current.email)
    return list(rows)
