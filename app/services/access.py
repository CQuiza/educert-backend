"""Comprobaciones de roles y alcance (RBAC)."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import CourseStatus, UserRole
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.user import User
from app.repositories.course_repository import course_repository
from app.repositories.enrollment_repository import course_enrollment_repository
from app.repositories.lesson_repository import lesson_repository
from app.repositories.module_repository import module_repository


def is_super_or_admin(user: User) -> bool:
    return user.role in (UserRole.superuser.value, UserRole.admin.value)


def is_teacher(user: User) -> bool:
    return user.role == UserRole.teacher.value


def is_student(user: User) -> bool:
    return user.role == UserRole.student.value


async def require_course_visible(
    db: AsyncSession,
    user: User | None,
    course_id: int,
    *,
    need_content: bool = False,
) -> None:
    """need_content: estudiante debe estar inscrito; profesor dueño para contenido."""
    course = await course_repository.get_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso no encontrado")

    if user is None:
        if course.status != CourseStatus.published.value:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso no encontrado")
        return

    if is_super_or_admin(user):
        return

    if is_teacher(user):
        if course.teacher_id == user.id:
            return
        if not need_content:
            if course.status != CourseStatus.published.value:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso no encontrado")
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")

    if is_student(user):
        if not need_content:
            if course.status != CourseStatus.published.value:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso no encontrado")
            return
        enr = await course_enrollment_repository.get_by_user_course(db, user.id, course_id)
        if enr:
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No inscrito en este curso")


async def ensure_module_lesson_access(
    db: AsyncSession,
    user: User,
    *,
    module_id: int | None = None,
    lesson_id: int | None = None,
    need_student_enrollment: bool = False,
) -> Module | Lesson:
    if module_id is not None:
        mod = await module_repository.get_by_id(db, module_id)
        if not mod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")
        await require_course_visible(db, user, mod.course_id, need_content=need_student_enrollment)
        return mod

    if lesson_id is not None:
        les = await lesson_repository.get_by_id(db, lesson_id)
        if not les:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lección no encontrada")
        mod = await module_repository.get_by_id(db, les.module_id)
        if not mod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")
        await require_course_visible(db, user, mod.course_id, need_content=need_student_enrollment)
        return les

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="module_id o lesson_id")


async def teacher_owns_module(db: AsyncSession, user: User, module: Module) -> bool:
    course = await course_repository.get_by_id(db, module.course_id)
    return bool(course and course.teacher_id == user.id)


async def teacher_owns_lesson(db: AsyncSession, user: User, lesson: Lesson) -> bool:
    mod = await module_repository.get_by_id(db, lesson.module_id)
    if not mod:
        return False
    return await teacher_owns_module(db, user, mod)


def require_staff(user: User) -> None:
    if not is_super_or_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol admin")


def require_teacher_or_staff(user: User) -> None:
    if is_super_or_admin(user) or is_teacher(user):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
