"""Usuarios."""

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status

logger = logging.getLogger(__name__)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.user import (
    UserCreate,
    UserListResponse,
    UserRead,
    UserUpdate,
    UserUpdateResponse,
    UserWithCertificatesListResponse,
    UserWithCertificatesRead,
)
from app.services.access import is_super_or_admin
from app.services.certificate_lifecycle import certificate_lifecycle
from app.services.user_service import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    role: UserRole | None = None,
    user_id: Annotated[int | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> UserListResponse:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    if role == UserRole.superuser and current.role != UserRole.superuser.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo superusuarios pueden listar superusuarios")
    exclude_superuser = current.role != UserRole.superuser.value
    if user_id is not None:
        u = await user_repository.get_by_id(db, user_id)
        if not u:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return UserListResponse(items=[u], total=1)
    total = await user_repository.count(db, role=role, exclude_superuser=exclude_superuser, search=search)
    rows = await user_repository.list(db, skip=skip, limit=limit, role=role, exclude_superuser=exclude_superuser, search=search)
    return UserListResponse(items=list(rows), total=total)


@router.get("/certified", response_model=UserWithCertificatesListResponse)
@limiter.limit("10/minute")
async def list_certified_students(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    search: Annotated[str | None, Query()] = None,
) -> UserWithCertificatesListResponse:
    if not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    total = await user_repository.count_certified_students(db, search=search)
    rows = await user_repository.list_certified_students(db, skip=skip, limit=limit, search=search)
    return UserWithCertificatesListResponse(items=list(rows), total=total)


@router.get("/{user_id}", response_model=UserRead)

async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> User:
    if not is_super_or_admin(current) and current.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    u = await user_repository.get_by_id(db, user_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return u


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
) -> User:
    if not is_super_or_admin(current):
        logger.warning("Intento de crear usuario sin permiso — by=%s", current.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    if body.role == UserRole.superuser and current.role != UserRole.superuser.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo un superusuario puede crear otro superusuario")
    try:
        u = await user_service.create_user(db, body, background_tasks=background_tasks, requesting_role=current.role)
        await db.commit()
        logger.info("Usuario creado vía API — id=%s, email=%s, by=%s", u.id, u.email, current.email)
        return u
    except ValueError as e:
        logger.warning("Error creando usuario — email=%s, error=%s", body.email, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{user_id}", response_model=UserUpdateResponse)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    if not is_super_or_admin(current) and current.id != user_id:
        logger.warning("Intento de actualizar usuario sin permiso — target=%s, by=%s", user_id, current.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso")
    if current.id == user_id and body.role is not None and not is_super_or_admin(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puede cambiar su propio rol")
    if body.role == UserRole.superuser and current.role != UserRole.superuser.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo un superusuario puede asignar el rol superusuario")
    u = await user_repository.get_by_id(db, user_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if u.role == UserRole.superuser.value and current.role != UserRole.superuser.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo un superusuario puede modificar a otro superusuario")
    updated = await user_service.update_user(db, u, body, requesting_role=current.role)

    # Reproducción atómica de certificados activos si cambian datos de identidad
    certificates_regenerated = 0
    changed = set(body.model_dump(exclude_unset=True))
    identity_fields = {"name", "first_last_name", "second_last_name", "identity_number", "identity_type"}
    if changed & identity_fields and u.role == UserRole.student.value:
        certificates_regenerated = await certificate_lifecycle.reproduce_active_for_student(
            db, student_id=updated.id, admin=current
        )

    await db.commit()
    logger.info("Usuario actualizado vía API — id=%s, by=%s, certs_reproducidos=%s",
                updated.id, current.email, certificates_regenerated)
    response = UserUpdateResponse.model_validate(updated)
    response.certificates_regenerated = certificates_regenerated
    return response


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> dict:
    if not is_super_or_admin(current):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar usuarios. Solo administradores.",
        )
    u = await user_repository.get_by_id(db, user_id)
    if not u:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado. El usuario que intentas eliminar no existe.",
        )
    if u.role == UserRole.superuser.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se puede eliminar un superusuario.",
        )
    if current.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminarte a ti mismo.",
        )
    try:
        await user_service.delete_user(db, u, deleted_by=current.id)
        await db.commit()
        logger.info("Usuario %s (id=%s) eliminado por %s", u.email, u.id, current.email)
        return {"message": f"Usuario {u.email} eliminado exitosamente."}
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Error inesperado al eliminar usuario %s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al eliminar el usuario. Intente nuevamente.",
        )
