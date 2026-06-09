"""Certificados emitidos."""

import asyncio
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from minio.error import S3Error
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.settings import get_settings
from app.models.enums import CertificateStatus, UserRole
from app.models.user import User
from app.repositories.certificate_repository import certificate_repository
from app.repositories.user_repository import user_repository
from app.schemas.certificate import (
    CertificateIssueRequest,
    CertificateRead,
    CertificateSearchResult,
    CertificateUpdate,
)
from app.services.access import is_super_or_admin
from app.services.certificate_lifecycle import certificate_lifecycle
from app.utils.minio_client import get_minio_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.get("", response_model=list[CertificateRead])
async def list_certificates(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    user_id: Annotated[int | None, Query()] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list:
    if current.role == UserRole.student.value:
        rows = await certificate_repository.list_by_user(
            db, current.id, skip=skip, limit=limit
        )
        return list(rows)
    uid = user_id
    if uid is None:
        if not is_super_or_admin(current):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Indique user_id o sea admin",
            )
        rows = await certificate_repository.list(db, skip=skip, limit=limit)
        return list(rows)
    if uid != current.id and not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    rows = await certificate_repository.list_by_user(db, uid, skip=skip, limit=limit)
    return list(rows)


@router.get("/view/{certificate_uuid}")
@limiter.limit("30/minute")
async def view_certificate_pdf_public(request: Request, certificate_uuid: UUID) -> Response:
    """Sirve el PDF desde MinIO para visualización en el front (público, solo UUID)."""
    logger.info("Solicitando PDF público — uuid=%s", certificate_uuid)
    settings = get_settings()
    if not (settings.minio_access_key and settings.minio_secret_key):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Almacenamiento de certificados no configurado.",
        )
    prefix = settings.minio_path_pdf.strip().strip("/")
    key = f"{prefix}/{certificate_uuid}.pdf" if prefix else f"{certificate_uuid}.pdf"

    def load() -> bytes:
        return get_minio_client(settings).download_bytes(key)

    try:
        data = await asyncio.to_thread(load)
    except S3Error as e:
        code = str(getattr(e, "code", "") or "").lower()
        if code in ("nosuchkey", "notfound"):
            logger.warning("PDF no encontrado — uuid=%s", certificate_uuid)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificado no encontrado",
            )
        logger.error("S3Error al servir PDF — uuid=%s: %s", certificate_uuid, e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Error al servir PDF — uuid=%s: %s", certificate_uuid, e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    logger.info("PDF servido — uuid=%s, size=%s", certificate_uuid, len(data))
    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{certificate_uuid}.pdf"',
        },
    )


@router.get("/view/{certificate_uuid}/qr")
@limiter.limit("30/minute")
async def view_certificate_qr_public(request: Request, certificate_uuid: UUID) -> Response:
    """Sirve el PNG del QR desde MinIO (público)."""
    logger.info("Solicitando QR público — uuid=%s", certificate_uuid)
    settings = get_settings()
    if not (settings.minio_access_key and settings.minio_secret_key):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Almacenamiento de certificados no configurado.",
        )
    prefix = settings.minio_path_qr.strip().strip("/")
    key = f"{prefix}/{certificate_uuid}.png" if prefix else f"{certificate_uuid}.png"

    def load() -> bytes:
        return get_minio_client(settings).download_bytes(key)

    try:
        data = await asyncio.to_thread(load)
    except S3Error as e:
        code = str(getattr(e, "code", "") or "").lower()
        if code in ("nosuchkey", "notfound"):
            logger.warning("QR no encontrado — uuid=%s", certificate_uuid)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Código QR no encontrado",
            )
        logger.error("S3Error al servir QR — uuid=%s: %s", certificate_uuid, e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Error al servir QR — uuid=%s: %s", certificate_uuid, e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    logger.info("QR servido — uuid=%s", certificate_uuid)
    return Response(
        content=data,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=86400",
        },
    )


@router.get("/{certificate_id}", response_model=CertificateRead)
async def get_certificate(
    certificate_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    cert = await certificate_repository.get_by_id(db, certificate_id)
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Certificado no encontrado"
        )
    if current.role == UserRole.student.value:
        if cert.user_id != current.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso"
            )
        return cert
    if not is_super_or_admin(current) and cert.user_id != current.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    return cert


@router.post("", response_model=CertificateRead, status_code=status.HTTP_201_CREATED)
async def create_certificate(
    body: CertificateIssueRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
) -> object:
    try:
        return await certificate_lifecycle.issue_certificate(
            db,
            admin=current,
            user_id=body.user_id,
            certificate_type_id=body.certificate_type_id,
            issued_at=body.issued_at,
            background_tasks=background_tasks,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.patch("/{certificate_id}", response_model=CertificateRead)
async def update_certificate(
    certificate_id: int,
    body: CertificateUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    if not is_super_or_admin(current):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores"
        )
    cert = await certificate_repository.get_by_id(db, certificate_id)
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Certificado no encontrado"
        )
    payload = body.model_dump(exclude_unset=True)
    new_status = payload.pop("status", None)

    try:
        if new_status == CertificateStatus.revoked:
            return await certificate_lifecycle.revoke_certificate(
                db, admin=current, cert=cert
            )
        elif new_status == CertificateStatus.active:
            return await certificate_lifecycle.activate_certificate(
                db, admin=current, cert=cert
            )
        elif payload:
            return await certificate_lifecycle.update_certificate_fields(
                db, admin=current, cert=cert, fields=payload
            )
        return cert
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.delete("/{certificate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certificate(
    certificate_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> None:
    if not is_super_or_admin(current):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores"
        )
    cert = await certificate_repository.get_by_id(db, certificate_id)
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Certificado no encontrado"
        )
    try:
        await certificate_lifecycle.delete_certificate(db, admin=current, cert=cert)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.get("/search-by-identity/{identity_number}", response_model=list[CertificateSearchResult])
@limiter.limit("5/minute")
async def search_certificates_by_identity(
    request: Request, identity_number: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """Público: busca certificados por número de identidad del estudiante."""
    user = await user_repository.get_by_identity_number(db, identity_number)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron certificados para esta identidad")
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.certificate import Certificate
    stmt = (
        select(Certificate)
        .where(
            Certificate.user_id == user.id,
            Certificate.status.in_([CertificateStatus.active.value, CertificateStatus.expired.value]),
        )
        .order_by(Certificate.issued_at.desc())
    )
    result = await db.execute(stmt)
    certs = result.scalars().all()
    if not certs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron certificados para esta identidad")
    return [
        {
            "user_name": user.name,
            "identity_number": user.identity_number,
            "certificates": certs,
        }
    ]
