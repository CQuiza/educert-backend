"""Certificados emitidos."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certificate import Certificate
from app.models.certificate_type import CertificateType
from app.models.user import User


class CertificateRepository:
    async def get_by_id(self, db: AsyncSession, cert_id: int) -> Certificate | None:
        r = await db.execute(select(Certificate).where(Certificate.id == cert_id))
        return r.scalar_one_or_none()

    async def get_by_uuid(self, db: AsyncSession, uid: UUID) -> Certificate | None:
        r = await db.execute(select(Certificate).where(Certificate.unique_id == uid))
        return r.scalar_one_or_none()

    def _apply_search(self, q, search: str | None, join_user: bool = False):
        if not search:
            return q
        term = f"%{search}%"
        conditions = [
            cast(Certificate.unique_id, String).ilike(term),
            CertificateType.name.ilike(term),
        ]
        if join_user:
            conditions.extend([
                User.name.ilike(term),
                User.email.ilike(term),
                User.identity_number.ilike(term),
            ])
        q = q.join(CertificateType, Certificate.certificate_type_id == CertificateType.id, isouter=True)
        if join_user:
            q = q.join(User, Certificate.user_id == User.id, isouter=True)
        return q.where(or_(*conditions))

    async def count(self, db: AsyncSession, *, search: str | None = None, join_user: bool = False) -> int:
        q = select(func.count(Certificate.id))
        q = self._apply_search(q, search, join_user=join_user)
        r = await db.execute(q)
        return r.scalar_one()

    async def count_by_user(self, db: AsyncSession, user_id: int, *, search: str | None = None) -> int:
        q = select(func.count(Certificate.id)).where(Certificate.user_id == user_id)
        q = self._apply_search(q, search, join_user=False)
        r = await db.execute(q)
        return r.scalar_one()

    async def list_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> Sequence[Certificate]:
        q = select(Certificate).where(Certificate.user_id == user_id)
        q = self._apply_search(q, search, join_user=False)
        r = await db.execute(q.offset(skip).limit(limit))
        return r.scalars().all()

    async def list(self, db: AsyncSession, *, skip: int = 0, limit: int = 100, search: str | None = None) -> Sequence[Certificate]:
        q = select(Certificate)
        q = self._apply_search(q, search, join_user=True)
        r = await db.execute(q.offset(skip).limit(limit))
        return r.scalars().all()

    async def create(
        self,
        db: AsyncSession,
        *,
        certificate_type_id: int | None,
        user_id: int | None,
        issued_at: object | None = None,
        expires_at: object | None = None,
        status: str,
        qr_code_url: str | None,
        pdf_url: str | None,
    ) -> Certificate:
        data: dict[str, object] = dict(
            certificate_type_id=certificate_type_id,
            user_id=user_id,
            status=status,
            qr_code_url=qr_code_url,
            pdf_url=pdf_url,
        )
        if issued_at is not None:
            data["issued_at"] = issued_at
        if expires_at is not None:
            data["expires_at"] = expires_at
        c = Certificate(**data)
        db.add(c)
        await db.flush()
        await db.refresh(c)
        return c

    async def update(self, db: AsyncSession, cert: Certificate, fields: dict[str, object]) -> Certificate:
        allowed = {"status", "qr_code_url", "pdf_url"}
        for k, v in fields.items():
            if k in allowed:
                setattr(cert, k, v)
        await db.flush()
        await db.refresh(cert)
        return cert

    async def delete(self, db: AsyncSession, cert: Certificate) -> None:
        await db.delete(cert)


certificate_repository = CertificateRepository()
