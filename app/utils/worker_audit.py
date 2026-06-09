"""Helper para registrar acciones de trabajos en segundo plano."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.worker_audit_repository import worker_audit_repository


async def log_worker_action(
    db: AsyncSession,
    *,
    task_name: str,
    status: str,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    details: str | None = None,
) -> None:
    """Crea un registro de auditoría para un trabajo en segundo plano."""
    await worker_audit_repository.create(
        db,
        task_name=task_name,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        details=details,
    )
