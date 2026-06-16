"""Repositorio de auditoría de correos electrónicos."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_audit import EmailAudit


class EmailAuditRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        user_name: str | None = None,
        email_to: str,
        email_type: str,
        status: str = "pending",
        error: str | None = None,
        metadata: dict | None = None,
    ) -> EmailAudit:
        entry = EmailAudit(
            user_name=user_name,
            email_to=email_to,
            email_type=email_type,
            status=status,
            error=error,
            metadata_=metadata,
        )
        db.add(entry)
        await db.flush()
        await db.refresh(entry)
        return entry

    async def list(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[EmailAudit]:
        q = select(EmailAudit).order_by(EmailAudit.created_at.desc()).offset(skip).limit(limit)
        r = await db.execute(q)
        return list(r.scalars().all())

    async def get_by_id(self, db: AsyncSession, audit_id: int) -> EmailAudit | None:
        r = await db.execute(select(EmailAudit).where(EmailAudit.id == audit_id))
        return r.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        entry: EmailAudit,
        fields: dict[str, object],
    ) -> EmailAudit:
        allowed = {"status", "error"}
        for k, v in fields.items():
            if k in allowed:
                setattr(entry, k, v)
        await db.flush()
        await db.refresh(entry)
        return entry


email_audit_repository = EmailAuditRepository()
