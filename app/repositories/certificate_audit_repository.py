"""Auditoría de certificados."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certificate_audit import CertificateAudit


class CertificateAuditRepository:
    async def get_by_id(
        self, db: AsyncSession, audit_id: int
    ) -> CertificateAudit | None:
        r = await db.execute(
            select(CertificateAudit).where(CertificateAudit.id == audit_id)
        )
        return r.scalar_one_or_none()

    async def list(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 500
    ) -> Sequence[CertificateAudit]:
        r = await db.execute(select(CertificateAudit).offset(skip).limit(limit))
        return r.scalars().all()

    async def create(
        self,
        db: AsyncSession,
        *,
        certificate_id: int | None,
        certificate_unique_id: UUID | None = None,
        action: str | None,
        performed_by: int | None,
    ) -> CertificateAudit:
        a = CertificateAudit(
            certificate_id=certificate_id,
            certificate_unique_id=certificate_unique_id,
            action=action,
            performed_by=performed_by,
        )
        db.add(a)
        await db.flush()
        await db.refresh(a)
        return a

    async def update(
        self,
        db: AsyncSession,
        row: CertificateAudit,
        fields: dict[str, object],
    ) -> CertificateAudit:
        allowed = {"certificate_id", "certificate_unique_id", "action", "performed_by"}
        for k, v in fields.items():
            if k in allowed:
                setattr(row, k, v)
        await db.flush()
        await db.refresh(row)
        return row

    async def delete(self, db: AsyncSession, row: CertificateAudit) -> None:
        await db.delete(row)


certificate_audit_repository = CertificateAuditRepository()
