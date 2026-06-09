"""Repositorio de lecciones."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson


class LessonRepository:
    async def get_by_id(self, db: AsyncSession, lesson_id: int) -> Lesson | None:
        r = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
        return r.scalar_one_or_none()

    async def list_by_module(
        self,
        db: AsyncSession,
        module_id: int,
        *,
        skip: int = 0,
        limit: int = 500,
    ) -> Sequence[Lesson]:
        r = await db.execute(
            select(Lesson)
            .where(Lesson.module_id == module_id)
            .order_by(Lesson.order_index)
            .offset(skip)
            .limit(limit),
        )
        return r.scalars().all()

    async def list(self, db: AsyncSession, *, skip: int = 0, limit: int = 500) -> Sequence[Lesson]:
        r = await db.execute(select(Lesson).order_by(Lesson.id).offset(skip).limit(limit))
        return r.scalars().all()

    async def create(
        self,
        db: AsyncSession,
        *,
        module_id: int,
        title: str,
        text_content: str | None,
        image_content_url: str | None,
        video_content_url: str | None,
        file_content_url: str | None,
        order_index: int,
    ) -> Lesson:
        le = Lesson(
            module_id=module_id,
            title=title,
            text_content=text_content,
            image_content_url=image_content_url,
            video_content_url=video_content_url,
            file_content_url=file_content_url,
            order_index=order_index,
        )
        db.add(le)
        await db.flush()
        await db.refresh(le)
        return le

    async def update(self, db: AsyncSession, lesson: Lesson, fields: dict[str, object]) -> Lesson:
        allowed = {
            "title",
            "text_content",
            "image_content_url",
            "video_content_url",
            "file_content_url",
            "order_index",
        }
        for k, v in fields.items():
            if k in allowed:
                setattr(lesson, k, v)
        await db.flush()
        await db.refresh(lesson)
        return lesson

    async def delete(self, db: AsyncSession, lesson: Lesson) -> None:
        await db.delete(lesson)


lesson_repository = LessonRepository()
