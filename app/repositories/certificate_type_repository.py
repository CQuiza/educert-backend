"""Tipos de certificado."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certificate_type import CertificateType


class CertificateTypeRepository:
    async def get_by_id(self, db: AsyncSession, ct_id: int) -> CertificateType | None:
        r = await db.execute(select(CertificateType).where(CertificateType.id == ct_id))
        return r.scalar_one_or_none()

    async def list(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 200
    ) -> Sequence[CertificateType]:
        r = await db.execute(select(CertificateType).offset(skip).limit(limit))
        return r.scalars().all()

    async def create(
        self,
        db: AsyncSession,
        *,
        name: str,
        reference: str | None,
        type: str,
        hours: int,
        validity_type: str,
        validity_value: int,
        created_by: int | None,
    ) -> CertificateType:
        ct = CertificateType(
            name=name,
            reference=reference,
            type=type,
            hours=hours,
            validity_type=validity_type,
            validity_value=validity_value,
            created_by=created_by,
        )
        db.add(ct)
        await db.flush()
        await db.refresh(ct)
        return ct

    async def update(
        self, db: AsyncSession, ct: CertificateType, fields: dict[str, object]
    ) -> CertificateType:
        allowed = {
            "name",
            "reference",
            "type",
            "hours",
            "validity_type",
            "validity_value",
        }
        for k, v in fields.items():
            if k in allowed:
                setattr(ct, k, v)
        await db.flush()
        await db.refresh(ct)
        return ct

    async def delete(self, db: AsyncSession, ct: CertificateType) -> None:
        await db.delete(ct)


certificate_type_repository = CertificateTypeRepository()
