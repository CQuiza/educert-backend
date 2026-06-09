"""Inscripciones."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import CourseEnrollment


class CourseEnrollmentRepository:
    async def get_by_id(self, db: AsyncSession, enrollment_id: int) -> CourseEnrollment | None:
        r = await db.execute(select(CourseEnrollment).where(CourseEnrollment.id == enrollment_id))
        return r.scalar_one_or_none()

    async def get_by_user_course(
        self,
        db: AsyncSession,
        user_id: int,
        course_id: int,
    ) -> CourseEnrollment | None:
        r = await db.execute(
            select(CourseEnrollment).where(
                CourseEnrollment.user_id == user_id,
                CourseEnrollment.course_id == course_id,
            ),
        )
        return r.scalar_one_or_none()

    async def list_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 200,
    ) -> Sequence[CourseEnrollment]:
        r = await db.execute(
            select(CourseEnrollment)
            .where(CourseEnrollment.user_id == user_id)
            .offset(skip)
            .limit(limit),
        )
        return r.scalars().all()

    async def list_by_course(
        self,
        db: AsyncSession,
        course_id: int,
        *,
        skip: int = 0,
        limit: int = 500,
    ) -> Sequence[CourseEnrollment]:
        r = await db.execute(
            select(CourseEnrollment)
            .where(CourseEnrollment.course_id == course_id)
            .offset(skip)
            .limit(limit),
        )
        return r.scalars().all()

    async def list(self, db: AsyncSession, *, skip: int = 0, limit: int = 500) -> Sequence[CourseEnrollment]:
        r = await db.execute(select(CourseEnrollment).offset(skip).limit(limit))
        return r.scalars().all()

    async def create(self, db: AsyncSession, *, user_id: int, course_id: int) -> CourseEnrollment:
        e = CourseEnrollment(user_id=user_id, course_id=course_id)
        db.add(e)
        await db.flush()
        await db.refresh(e)
        return e

    async def delete(self, db: AsyncSession, row: CourseEnrollment) -> None:
        await db.delete(row)


course_enrollment_repository = CourseEnrollmentRepository()
