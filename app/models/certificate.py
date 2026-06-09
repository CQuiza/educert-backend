"""Certificado emitido."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.certificate_audit import CertificateAudit
    from app.models.certificate_type import CertificateType
    from app.models.user import User


class Certificate(Base):
    __tablename__ = "certificates"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'revoked', 'expired')",
            name="ck_certificates_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unique_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        unique=True,
        nullable=False,
        server_default=func.gen_random_uuid(),
    )
    certificate_type_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("certificate_types.id"),
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(20), default="active", server_default="active"
    )
    qr_code_url: Mapped[str | None] = mapped_column(String(255))
    pdf_url: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    certificate_type: Mapped[CertificateType | None] = relationship(
        "CertificateType",
        back_populates="certificates",
    )
    user: Mapped[User | None] = relationship("User", back_populates="certificates")
    audit_entries: Mapped[list[CertificateAudit]] = relationship(
        "CertificateAudit",
        back_populates="certificate",
    )
