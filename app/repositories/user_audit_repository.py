"""Repositorio de auditoría de usuarios."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_audit import UserAudit


class UserAuditRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: int | None,
        deleted_by: int | None,
        snapshot: dict,
    ) -> UserAudit:
        entry = UserAudit(
            user_id=user_id,
            deleted_by=deleted_by,
            snapshot=snapshot,
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
    ) -> list[UserAudit]:
        q = select(UserAudit).order_by(UserAudit.deleted_at.desc()).offset(skip).limit(limit)
        r = await db.execute(q)
        return list(r.scalars().all())

    async def get_by_id(self, db: AsyncSession, audit_id: int) -> UserAudit | None:
        r = await db.execute(select(UserAudit).where(UserAudit.id == audit_id))
        return r.scalar_one_or_none()


user_audit_repository = UserAuditRepository()
