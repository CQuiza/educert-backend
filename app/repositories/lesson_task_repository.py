"""Repositorio de tareas de lección."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson_task import LessonTask


class LessonTaskRepository:
    async def get_by_id(self, db: AsyncSession, task_id: int) -> LessonTask | None:
        r = await db.execute(select(LessonTask).where(LessonTask.id == task_id))
        return r.scalar_one_or_none()

    async def list_by_lesson(
        self,
        db: AsyncSession,
        lesson_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[LessonTask]:
        r = await db.execute(
            select(LessonTask)
            .where(LessonTask.lesson_id == lesson_id)
            .order_by(LessonTask.order_index)
            .offset(skip)
            .limit(limit),
        )
        return r.scalars().all()

    async def create(
        self,
        db: AsyncSession,
        *,
        lesson_id: int,
        title: str,
        description: str | None = None,
        original_filename: str | None = None,
        file_type: str = "none",
        file_url: str | None = None,
        google_drive_link: str | None = None,
        order_index: int = 0,
    ) -> LessonTask:
        t = LessonTask(
            lesson_id=lesson_id,
            title=title,
            description=description,
            original_filename=original_filename,
            file_type=file_type,
            file_url=file_url,
            google_drive_link=google_drive_link,
            order_index=order_index,
        )
        db.add(t)
        await db.flush()
        await db.refresh(t)
        return t

    async def update(
        self, db: AsyncSession, task: LessonTask, fields: dict[str, object]
    ) -> LessonTask:
        allowed = {
            "title",
            "description",
            "original_filename",
            "file_type",
            "file_url",
            "google_drive_link",
            "order_index",
        }
        for k, v in fields.items():
            if k in allowed:
                setattr(task, k, v)
        await db.flush()
        await db.refresh(task)
        return task

    async def delete(self, db: AsyncSession, task: LessonTask) -> None:
        await db.delete(task)


lesson_task_repository = LessonTaskRepository()
