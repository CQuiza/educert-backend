"""Progreso por lección."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.lesson_repository import lesson_repository
from app.repositories.module_repository import module_repository
from app.repositories.progress_repository import user_progress_repository
from app.schemas.progress import UserProgressCreate, UserProgressRead, UserProgressUpdate
from app.services.access import is_super_or_admin, require_course_visible

router = APIRouter(prefix="/user-progress", tags=["user-progress"])


@router.get("", response_model=list[UserProgressRead])
async def list_progress(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    user_id: Annotated[int | None, Query()] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
) -> list:
    uid = user_id if user_id is not None else current.id
    if uid != current.id and not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo su propio progreso")
    rows = await user_progress_repository.list_by_user(db, uid, skip=skip, limit=limit)
    return list(rows)


@router.get("/{progress_id}", response_model=UserProgressRead)
async def get_progress(
    progress_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    row = await user_progress_repository.get_by_id(db, progress_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progreso no encontrado")
    if row.user_id != current.id and not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    return row


@router.post("", response_model=UserProgressRead, status_code=status.HTTP_201_CREATED)
async def create_progress(
    body: UserProgressCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    if body.user_id != current.id and not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo puede registrar su progreso")
    if current.role == UserRole.student.value:
        le = await lesson_repository.get_by_id(db, body.lesson_id)
        if not le:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lección no encontrada")
        mod = await module_repository.get_by_id(db, le.module_id)
        if not mod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")
        await require_course_visible(db, current, mod.course_id, need_content=True)
    return await user_progress_repository.create(
        db,
        user_id=body.user_id,
        lesson_id=body.lesson_id,
        completed=body.completed,
        completed_at=body.completed_at,
    )


@router.patch("/{progress_id}", response_model=UserProgressRead)
async def update_progress(
    progress_id: int,
    body: UserProgressUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    row = await user_progress_repository.get_by_id(db, progress_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progreso no encontrado")
    if row.user_id != current.id and not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    if current.role == UserRole.student.value:
        le = await lesson_repository.get_by_id(db, row.lesson_id)
        if not le:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lección no encontrada")
        mod = await module_repository.get_by_id(db, le.module_id)
        if not mod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")
        await require_course_visible(db, current, mod.course_id, need_content=True)
    payload = body.model_dump(exclude_unset=True)
    return await user_progress_repository.update(db, row, payload)


@router.delete("/{progress_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_progress(
    progress_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> None:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")
    row = await user_progress_repository.get_by_id(db, progress_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progreso no encontrado")
    await user_progress_repository.delete(db, row)
