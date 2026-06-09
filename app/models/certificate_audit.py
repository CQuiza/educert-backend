"""Auditoría de certificados."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.certificate import Certificate
    from app.models.user import User


class CertificateAudit(Base):
    __tablename__ = "certificate_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    certificate_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("certificates.id", ondelete="SET NULL"),
    )
    certificate_unique_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
    )
    action: Mapped[str | None] = mapped_column(String(50))
    performed_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    certificate: Mapped[Certificate | None] = relationship(
        "Certificate",
        back_populates="audit_entries",
    )
    performer: Mapped[User | None] = relationship("User", foreign_keys=[performed_by])
