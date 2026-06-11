"""Repositorio de archivos de lección."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson_file import LessonFile


class LessonFileRepository:
    async def get_by_id(self, db: AsyncSession, file_id: int) -> LessonFile | None:
        r = await db.execute(select(LessonFile).where(LessonFile.id == file_id))
        return r.scalar_one_or_none()

    async def list_by_lesson(
        self,
        db: AsyncSession,
        lesson_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[LessonFile]:
        r = await db.execute(
            select(LessonFile)
            .where(LessonFile.lesson_id == lesson_id)
            .order_by(LessonFile.order_index)
            .offset(skip)
            .limit(limit),
        )
        return r.scalars().all()

    async def create(
        self,
        db: AsyncSession,
        *,
        lesson_id: int,
        original_filename: str,
        mime_type: str | None = None,
        order_index: int = 0,
    ) -> LessonFile:
        f = LessonFile(
            lesson_id=lesson_id,
            original_filename=original_filename,
            mime_type=mime_type,
            order_index=order_index,
        )
        db.add(f)
        await db.flush()
        await db.refresh(f)
        return f

    async def update(
        self, db: AsyncSession, file: LessonFile, fields: dict[str, object]
    ) -> LessonFile:
        allowed = {
            "original_filename",
            "mime_type",
            "file_url",
            "order_index",
        }
        for k, v in fields.items():
            if k in allowed:
                setattr(file, k, v)
        await db.flush()
        await db.refresh(file)
        return file

    async def delete(self, db: AsyncSession, file: LessonFile) -> None:
        await db.delete(file)


lesson_file_repository = LessonFileRepository()
