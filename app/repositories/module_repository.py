"""Repositorio de módulos."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.module import Module


class ModuleRepository:
    async def get_by_id(self, db: AsyncSession, module_id: int) -> Module | None:
        r = await db.execute(select(Module).where(Module.id == module_id))
        return r.scalar_one_or_none()

    async def list_by_course(
        self,
        db: AsyncSession,
        course_id: int,
        *,
        skip: int = 0,
        limit: int = 500,
    ) -> Sequence[Module]:
        r = await db.execute(
            select(Module)
            .where(Module.course_id == course_id)
            .order_by(Module.order_index)
            .offset(skip)
            .limit(limit),
        )
        return r.scalars().all()

    async def list(self, db: AsyncSession, *, skip: int = 0, limit: int = 500) -> Sequence[Module]:
        r = await db.execute(select(Module).order_by(Module.id).offset(skip).limit(limit))
        return r.scalars().all()

    async def create(
        self,
        db: AsyncSession,
        *,
        course_id: int,
        title: str,
        order_index: int,
    ) -> Module:
        m = Module(course_id=course_id, title=title, order_index=order_index)
        db.add(m)
        await db.flush()
        await db.refresh(m)
        return m

    async def update(self, db: AsyncSession, module: Module, fields: dict[str, object]) -> Module:
        allowed = {"title", "order_index"}
        for k, v in fields.items():
            if k in allowed:
                setattr(module, k, v)
        await db.flush()
        await db.refresh(module)
        return module

    async def delete(self, db: AsyncSession, module: Module) -> None:
        await db.delete(module)


module_repository = ModuleRepository()
