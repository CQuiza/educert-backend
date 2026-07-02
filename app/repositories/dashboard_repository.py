"""Repositorio de estadísticas del dashboard."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certificate import Certificate
from app.models.certificate_type import CertificateType
from app.models.course import Course
from app.models.user import User


class DashboardRepository:
    async def get_stats(self, db: AsyncSession) -> dict[str, int]:
        r = await db.execute(select(func.count(User.id)))
        total_users: int = r.scalar_one()

        r = await db.execute(select(func.count(Certificate.id)))
        total_certificates: int = r.scalar_one()

        r = await db.execute(
            select(func.count(Certificate.id)).where(Certificate.status == "active")
        )
        active_certificates: int = r.scalar_one()

        r = await db.execute(
            select(func.count(Certificate.id)).where(Certificate.status == "expired")
        )
        expired_certificates: int = r.scalar_one()

        r = await db.execute(
            select(func.count(Certificate.id)).where(Certificate.status == "revoked")
        )
        revoked_certificates: int = r.scalar_one()

        r = await db.execute(
            select(func.count(Course.id)).where(Course.status == "published")
        )
        published_courses: int = r.scalar_one()

        r = await db.execute(select(func.count(CertificateType.id)))
        certificate_types: int = r.scalar_one()

        return {
            "total_users": total_users,
            "total_certificates": total_certificates,
            "active_certificates": active_certificates,
            "expired_certificates": expired_certificates,
            "revoked_certificates": revoked_certificates,
            "published_courses": published_courses,
            "certificate_types": certificate_types,
        }


dashboard_repository = DashboardRepository()
