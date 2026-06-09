"""Certificado emitido."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CertificateStatus


class CertificateCreate(BaseModel):
    """Creación directa (normalmente se usa /issue)."""

    certificate_type_id: int | None = None
    user_id: int | None = None
    status: CertificateStatus = CertificateStatus.active
    qr_code_url: str | None = Field(default=None, max_length=255)
    pdf_url: str | None = Field(default=None, max_length=255)


class CertificateIssueRequest(BaseModel):
    """Emisión por administrador — el servicio rellena fechas y URLs."""

    user_id: int
    certificate_type_id: int
    issued_at: datetime | None = Field(
        default=None, description="Fecha personalizada de emisión del certificado"
    )


class CertificateUpdate(BaseModel):
    status: CertificateStatus | None = None
    qr_code_url: str | None = Field(default=None, max_length=255)
    pdf_url: str | None = Field(default=None, max_length=255)

    model_config = ConfigDict(extra="forbid")


class CertificateRead(BaseModel):
    id: int
    unique_id: UUID
    certificate_type_id: int | None
    user_id: int | None
    issued_at: datetime
    expires_at: datetime | None
    status: CertificateStatus
    qr_code_url: str | None
    pdf_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CertificateSearchResult(BaseModel):
    user_name: str | None = None
    identity_number: str | None = None
    certificates: list[CertificateRead]
