"""Repositorio de cursos."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course


class CourseRepository:
    async def get_by_id(self, db: AsyncSession, course_id: int) -> Course | None:
        r = await db.execute(select(Course).where(Course.id == course_id))
        return r.scalar_one_or_none()

    async def list_by_ids(self, db: AsyncSession, ids: list[int]) -> Sequence[Course]:
        if not ids:
            return []
        r = await db.execute(select(Course).where(Course.id.in_(ids)).order_by(Course.id))
        return r.scalars().all()

    async def list(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        teacher_id: int | None = None,
        status: str | None = None,
    ) -> Sequence[Course]:
        q = select(Course).offset(skip).limit(limit)
        if teacher_id is not None:
            q = q.where(Course.teacher_id == teacher_id)
        if status is not None:
            q = q.where(Course.status == status)
        r = await db.execute(q.order_by(Course.id))
        return r.scalars().all()

    async def create(
        self,
        db: AsyncSession,
        *,
        title: str,
        description: str | None,
        certificate_type_id: int | None,
        teacher_id: int | None,
        status: str,
    ) -> Course:
        c = Course(
            title=title,
            description=description,
            certificate_type_id=certificate_type_id,
            teacher_id=teacher_id,
            status=status,
        )
        db.add(c)
        await db.flush()
        await db.refresh(c)
        return c

    async def update(self, db: AsyncSession, course: Course, fields: dict[str, object]) -> Course:
        allowed = {"title", "description", "certificate_type_id", "teacher_id", "status"}
        for k, v in fields.items():
            if k in allowed:
                setattr(course, k, v)
        await db.flush()
        await db.refresh(course)
        return course

    async def delete(self, db: AsyncSession, course: Course) -> None:
        await db.delete(course)


course_repository = CourseRepository()
