"""Auditoría de envío de correos electrónicos."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import EmailStatus


class EmailAudit(Base):
    __tablename__ = "email_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str | None] = mapped_column(String(255))
    email_to: Mapped[str] = mapped_column(String(255), nullable=False)
    email_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=EmailStatus.pending.value)
    error: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
