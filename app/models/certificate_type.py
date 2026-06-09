"""Tipo de certificado."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.certificate import Certificate
    from app.models.course import Course
    from app.models.user import User


class CertificateType(Base):
    __tablename__ = "certificate_types"
    __table_args__ = (
        CheckConstraint(
            "type IN ('basic', 'advanced', 'diploma')",
            name="ck_certificate_types_type",
        ),
        CheckConstraint(
            "validity_type IN ('years', 'months', 'days')",
            name="ck_certificate_types_validity_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    reference: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    hours: Mapped[int] = mapped_column(Integer, nullable=False)
    validity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    validity_value: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    courses_using_type: Mapped[list[Course]] = relationship(
        "Course",
        foreign_keys="Course.certificate_type_id",
        back_populates="certificate_type",
    )
    creator: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[created_by],
    )
    certificates: Mapped[list[Certificate]] = relationship(
        "Certificate",
        back_populates="certificate_type",
    )
