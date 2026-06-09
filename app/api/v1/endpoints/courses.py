"""Cursos."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, get_optional_user
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.course_repository import course_repository
from app.schemas.course import CourseCreate, CoursePublicRead, CourseRead, CourseUpdate
from app.services.access import is_super_or_admin, is_student, require_course_visible
from app.services.course_service import course_service

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CoursePublicRead])
async def list_courses(
    db: Annotated[AsyncSession, Depends(get_db)],
    optional_user: Annotated[User | None, Depends(get_optional_user)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list:
    rows = await course_service.list_for_actor(db, actor=optional_user, skip=skip, limit=limit)
    return list(rows)


@router.get("/{course_id}", response_model=CourseRead)
async def get_course(
    course_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    optional_user: Annotated[User | None, Depends(get_optional_user)],
) -> object:
    need_enrollment = optional_user is not None and is_student(optional_user)
    await require_course_visible(db, optional_user, course_id, need_content=need_enrollment)
    c = await course_repository.get_by_id(db, course_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso no encontrado")
    return c


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(
    body: CourseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    if current.role not in (UserRole.superuser.value, UserRole.admin.value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")
    return await course_repository.create(
        db,
        title=body.title,
        description=body.description,
        certificate_type_id=body.certificate_type_id,
        teacher_id=body.teacher_id,
        status=body.status.value,
    )


@router.patch("/{course_id}", response_model=CourseRead)
async def update_course(
    course_id: int,
    body: CourseUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")
    c = await course_repository.get_by_id(db, course_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso no encontrado")
    payload = body.model_dump(exclude_unset=True)
    if "status" in payload and payload["status"] is not None:
        payload["status"] = payload["status"].value
    return await course_repository.update(db, c, payload)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> None:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")
    c = await course_repository.get_by_id(db, course_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curso no encontrado")
    await course_repository.delete(db, c)
