"""Repositorio de auditoría de trabajos en segundo plano."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.worker_audit import WorkerAudit


class WorkerAuditRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        task_name: str,
        status: str,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        details: str | None = None,
    ) -> WorkerAudit:
        audit = WorkerAudit(
            task_name=task_name,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            details=details,
        )
        db.add(audit)
        await db.flush()
        await db.refresh(audit)
        return audit

    async def list(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[WorkerAudit]:
        q = select(WorkerAudit).order_by(WorkerAudit.created_at.desc()).offset(skip).limit(limit)
        r = await db.execute(q)
        return list(r.scalars().all())


worker_audit_repository = WorkerAuditRepository()
