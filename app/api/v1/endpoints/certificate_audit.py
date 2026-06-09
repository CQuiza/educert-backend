"""Auditoría de certificados."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.certificate_audit_repository import certificate_audit_repository
from app.schemas.certificate_audit import (
    CertificateAuditCreate,
    CertificateAuditRead,
    CertificateAuditUpdate,
)
from app.services.access import is_super_or_admin

router = APIRouter(prefix="/certificate-audit", tags=["certificate-audit"])


@router.get("", response_model=list[CertificateAuditRead])
async def list_audit(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
) -> list:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    rows = await certificate_audit_repository.list(db, skip=skip, limit=limit)
    return list(rows)


@router.get("/{audit_id}", response_model=CertificateAuditRead)
async def get_audit(
    audit_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    row = await certificate_audit_repository.get_by_id(db, audit_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado"
        )
    return row


@router.post(
    "", response_model=CertificateAuditRead, status_code=status.HTTP_201_CREATED
)
async def create_audit(
    body: CertificateAuditCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    action = body.action.value if body.action else None
    return await certificate_audit_repository.create(
        db,
        certificate_id=body.certificate_id,
        certificate_unique_id=body.certificate_unique_id,
        action=action,
        performed_by=body.performed_by,
    )


@router.patch("/{audit_id}", response_model=CertificateAuditRead)
async def update_audit(
    audit_id: int,
    body: CertificateAuditUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    row = await certificate_audit_repository.get_by_id(db, audit_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado"
        )
    payload = body.model_dump(exclude_unset=True)
    if "action" in payload and payload["action"] is not None:
        payload["action"] = payload["action"].value
    return await certificate_audit_repository.update(db, row, payload)


@router.delete("/{audit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audit(
    audit_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> None:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    row = await certificate_audit_repository.get_by_id(db, audit_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Registro no encontrado"
        )
    await certificate_audit_repository.delete(db, row)
