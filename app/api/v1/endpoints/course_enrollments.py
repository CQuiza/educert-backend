"""Inscripciones a cursos."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.enrollment_repository import course_enrollment_repository
from app.schemas.enrollment import CourseEnrollmentCreate, CourseEnrollmentRead
from app.services.access import is_super_or_admin

router = APIRouter(prefix="/course-enrollments", tags=["course-enrollments"])


@router.get("", response_model=list[CourseEnrollmentRead])
async def list_enrollments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    user_id: Annotated[int | None, Query()] = None,
    course_id: Annotated[int | None, Query()] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
) -> list:
    if current.role == UserRole.student.value:
        rows = await course_enrollment_repository.list_by_user(db, current.id, skip=skip, limit=limit)
        return list(rows)
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    if user_id is not None:
        rows = await course_enrollment_repository.list_by_user(db, user_id, skip=skip, limit=limit)
        return list(rows)
    if course_id is not None:
        rows = await course_enrollment_repository.list_by_course(db, course_id, skip=skip, limit=limit)
        return list(rows)
    rows = await course_enrollment_repository.list(db, skip=skip, limit=limit)
    return list(rows)


@router.get("/{enrollment_id}", response_model=CourseEnrollmentRead)
async def get_enrollment(
    enrollment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    row = await course_enrollment_repository.get_by_id(db, enrollment_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscripción no encontrada")
    if current.role == UserRole.student.value and row.user_id != current.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    if not is_super_or_admin(current) and row.user_id != current.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    return row


@router.post("", response_model=CourseEnrollmentRead, status_code=status.HTTP_201_CREATED)
async def create_enrollment(
    body: CourseEnrollmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")
    existing = await course_enrollment_repository.get_by_user_course(db, body.user_id, body.course_id)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya inscrito")
    return await course_enrollment_repository.create(db, user_id=body.user_id, course_id=body.course_id)


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_enrollment(
    enrollment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> None:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")
    row = await course_enrollment_repository.get_by_id(db, enrollment_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscripción no encontrada")
    await course_enrollment_repository.delete(db, row)
