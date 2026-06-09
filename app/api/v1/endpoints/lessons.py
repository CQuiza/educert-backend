"""Lecciones."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.lesson_repository import lesson_repository
from app.repositories.module_repository import module_repository
from app.schemas.lesson import LessonCreate, LessonRead, LessonUpdate
from app.services.access import (
    is_super_or_admin,
    is_teacher,
    require_course_visible,
    teacher_owns_module,
)

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("", response_model=list[LessonRead])
async def list_lessons(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    module_id: Annotated[int | None, Query()] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
) -> list:
    if module_id is None:
        if not is_super_or_admin(current):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parámetro module_id obligatorio",
            )
        rows = await lesson_repository.list(db, skip=skip, limit=limit)
        return list(rows)
    mod = await module_repository.get_by_id(db, module_id)
    if not mod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")
    await require_course_visible(db, current, mod.course_id, need_content=True)
    rows = await lesson_repository.list_by_module(db, module_id, skip=skip, limit=limit)
    return list(rows)


@router.get("/{lesson_id}", response_model=LessonRead)
async def get_lesson(
    lesson_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    le = await lesson_repository.get_by_id(db, lesson_id)
    if not le:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lección no encontrada")
    mod = await module_repository.get_by_id(db, le.module_id)
    if not mod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")
    await require_course_visible(db, current, mod.course_id, need_content=True)
    return le


@router.post("", response_model=LessonRead, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    body: LessonCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    if current.role not in (UserRole.superuser.value, UserRole.admin.value, UserRole.teacher.value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    mod = await module_repository.get_by_id(db, body.module_id)
    if not mod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")
    if is_teacher(current):
        if not await teacher_owns_module(db, current, mod):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No es su curso")
    elif not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    return await lesson_repository.create(
        db,
        module_id=body.module_id,
        title=body.title,
        text_content=body.text_content,
        image_content_url=body.image_content_url,
        video_content_url=body.video_content_url,
        file_content_url=body.file_content_url,
        order_index=body.order_index,
    )


@router.patch("/{lesson_id}", response_model=LessonRead)
async def update_lesson(
    lesson_id: int,
    body: LessonUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    le = await lesson_repository.get_by_id(db, lesson_id)
    if not le:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lección no encontrada")
    mod = await module_repository.get_by_id(db, le.module_id)
    if not mod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")
    if is_teacher(current):
        if not await teacher_owns_module(db, current, mod):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No es su curso")
    elif not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    payload = body.model_dump(exclude_unset=True)
    return await lesson_repository.update(db, le, payload)


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> None:
    le = await lesson_repository.get_by_id(db, lesson_id)
    if not le:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lección no encontrada")
    mod = await module_repository.get_by_id(db, le.module_id)
    if not mod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")
    if is_teacher(current):
        if not await teacher_owns_module(db, current, mod):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No es su curso")
    elif not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    await lesson_repository.delete(db, le)
