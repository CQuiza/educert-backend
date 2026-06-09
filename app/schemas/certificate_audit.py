"""Auditoría."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CertificateAuditAction


class CertificateAuditCreate(BaseModel):
    certificate_id: int | None = None
    certificate_unique_id: UUID | None = None
    action: CertificateAuditAction | None = None
    performed_by: int | None = None


class CertificateAuditUpdate(BaseModel):
    certificate_id: int | None = None
    certificate_unique_id: UUID | None = None
    action: CertificateAuditAction | None = None
    performed_by: int | None = None

    model_config = ConfigDict(extra="forbid")


class CertificateAuditRead(BaseModel):
    id: int
    certificate_id: int | None
    certificate_unique_id: UUID | None
    action: str | None
    performed_by: int | None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
