"""Tipos de certificado."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, get_optional_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.certificate_type_repository import certificate_type_repository
from app.schemas.certificate_type import (
    CertificateTypeCreate,
    CertificateTypeRead,
    CertificateTypeUpdate,
)
from app.services.access import is_super_or_admin

router = APIRouter(prefix="/certificate-types", tags=["certificate-types"])


@router.get("", response_model=list[CertificateTypeRead])
async def list_certificate_types(
    db: Annotated[AsyncSession, Depends(get_db)],
    optional_user: Annotated[User | None, Depends(get_optional_user)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list:
    rows = await certificate_type_repository.list(db, skip=skip, limit=limit)
    return list(rows)


@router.get("/{type_id}", response_model=CertificateTypeRead)
async def get_certificate_type(
    type_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    ct = await certificate_type_repository.get_by_id(db, type_id)
    if not ct:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tipo no encontrado"
        )
    return ct


@router.post(
    "", response_model=CertificateTypeRead, status_code=status.HTTP_201_CREATED
)
async def create_certificate_type(
    body: CertificateTypeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    created_by = body.created_by if body.created_by is not None else current.id
    return await certificate_type_repository.create(
        db,
        name=body.name,
        reference=body.reference,
        type=body.type.value,
        hours=body.hours,
        validity_type=body.validity_type.value,
        validity_value=body.validity_value,
        created_by=created_by,
    )


@router.patch("/{type_id}", response_model=CertificateTypeRead)
async def update_certificate_type(
    type_id: int,
    body: CertificateTypeUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    ct = await certificate_type_repository.get_by_id(db, type_id)
    if not ct:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tipo no encontrado"
        )
    payload = body.model_dump(exclude_unset=True)
    if "type" in payload and payload["type"] is not None:
        payload["type"] = payload["type"].value
    if "validity_type" in payload and payload["validity_type"] is not None:
        payload["validity_type"] = payload["validity_type"].value
    return await certificate_type_repository.update(db, ct, payload)


@router.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certificate_type(
    type_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> None:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    ct = await certificate_type_repository.get_by_id(db, type_id)
    if not ct:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tipo no encontrado"
        )
    await certificate_type_repository.delete(db, ct)
