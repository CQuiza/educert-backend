"""Módulos."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.course_repository import course_repository
from app.repositories.module_repository import module_repository
from app.schemas.module import ModuleCreate, ModuleRead, ModuleUpdate
from app.services.access import (
    is_super_or_admin,
    is_teacher,
    require_course_visible,
    teacher_owns_module,
)

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("", response_model=list[ModuleRead])
async def list_modules(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    course_id: Annotated[int | None, Query()] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
) -> list:
    if course_id is None:
        if not is_super_or_admin(current):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parámetro course_id obligatorio",
            )
        rows = await module_repository.list(db, skip=skip, limit=limit)
        return list(rows)
    await require_course_visible(db, current, course_id, need_content=True)
    rows = await module_repository.list_by_course(db, course_id, skip=skip, limit=limit)
    return list(rows)


@router.get("/{module_id}", response_model=ModuleRead)
async def get_module(
    module_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    m = await module_repository.get_by_id(db, module_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")
    await require_course_visible(db, current, m.course_id, need_content=True)
    return m


@router.post("", response_model=ModuleRead, status_code=status.HTTP_201_CREATED)
async def create_module(
    body: ModuleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    if current.role not in (UserRole.superuser.value, UserRole.admin.value, UserRole.teacher.value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    if is_teacher(current):
        course = await course_repository.get_by_id(db, body.course_id)
        if not course or course.teacher_id != current.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No es su curso")
    elif not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    return await module_repository.create(
        db,
        course_id=body.course_id,
        title=body.title,
        order_index=body.order_index,
    )


@router.patch("/{module_id}", response_model=ModuleRead)
async def update_module(
    module_id: int,
    body: ModuleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    m = await module_repository.get_by_id(db, module_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")
    if is_teacher(current):
        if not await teacher_owns_module(db, current, m):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No es su curso")
    elif not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    payload = body.model_dump(exclude_unset=True)
    return await module_repository.update(db, m, payload)


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    module_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> None:
    m = await module_repository.get_by_id(db, module_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")
    if is_teacher(current):
        if not await teacher_owns_module(db, current, m):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No es su curso")
    elif not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    await module_repository.delete(db, m)
