"""Listados de cursos según rol."""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.enums import CourseStatus, UserRole
from app.models.user import User
from app.repositories.course_repository import course_repository
from app.repositories.enrollment_repository import course_enrollment_repository


class CourseService:
    async def list_for_actor(
        self,
        db: AsyncSession,
        *,
        actor: User | None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Course]:
        """Anónimo: publicados. Estudiante: publicados en los que está inscrito. Staff: todos."""
        if actor is None:
            return await course_repository.list(
                db,
                skip=skip,
                limit=limit,
                status=CourseStatus.published.value,
            )

        if actor.role in (UserRole.superuser.value, UserRole.admin.value):
            return await course_repository.list(db, skip=skip, limit=limit)

        if actor.role == UserRole.teacher.value:
            return await course_repository.list(
                db,
                skip=skip,
                limit=limit,
                teacher_id=actor.id,
            )

        if actor.role == UserRole.student.value:
            enrollments = await course_enrollment_repository.list_by_user(db, actor.id, skip=0, limit=500)
            course_ids = list({e.course_id for e in enrollments})
            if not course_ids:
                return []
            rows = await course_repository.list_by_ids(db, course_ids)
            published = [c for c in rows if c.status == CourseStatus.published.value]
            return published[skip : skip + limit]

        return await course_repository.list(
            db,
            skip=skip,
            limit=limit,
            status=CourseStatus.published.value,
        )


course_service = CourseService()
