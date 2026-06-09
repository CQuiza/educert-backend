"""Progreso de usuario."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.progress import UserProgress


class UserProgressRepository:
    async def get_by_id(self, db: AsyncSession, progress_id: int) -> UserProgress | None:
        r = await db.execute(select(UserProgress).where(UserProgress.id == progress_id))
        return r.scalar_one_or_none()

    async def get_by_user_lesson(
        self,
        db: AsyncSession,
        user_id: int,
        lesson_id: int,
    ) -> UserProgress | None:
        r = await db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.lesson_id == lesson_id,
            ),
        )
        return r.scalar_one_or_none()

    async def list_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 500,
    ) -> Sequence[UserProgress]:
        r = await db.execute(
            select(UserProgress)
            .where(UserProgress.user_id == user_id)
            .offset(skip)
            .limit(limit),
        )
        return r.scalars().all()

    async def list(self, db: AsyncSession, *, skip: int = 0, limit: int = 500) -> Sequence[UserProgress]:
        r = await db.execute(select(UserProgress).offset(skip).limit(limit))
        return r.scalars().all()

    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        lesson_id: int,
        completed: bool,
        completed_at: object | None,
    ) -> UserProgress:
        p = UserProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            completed=completed,
            completed_at=completed_at,
        )
        db.add(p)
        await db.flush()
        await db.refresh(p)
        return p

    async def update(self, db: AsyncSession, row: UserProgress, fields: dict[str, object]) -> UserProgress:
        allowed = {"completed", "completed_at"}
        for k, v in fields.items():
            if k in allowed:
                setattr(row, k, v)
        await db.flush()
        await db.refresh(row)
        return row

    async def delete(self, db: AsyncSession, row: UserProgress) -> None:
        await db.delete(row)


user_progress_repository = UserProgressRepository()
