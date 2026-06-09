"""Tipo de certificado."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CertificateTypeKind, ValidityUnit


class CertificateTypeCreate(BaseModel):
    name: str = Field(..., max_length=255)
    reference: str | None = None
    type: CertificateTypeKind
    hours: int = Field(..., ge=0)
    validity_type: ValidityUnit
    validity_value: int = Field(..., ge=1)
    created_by: int | None = None


class CertificateTypeUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    reference: str | None = None
    type: CertificateTypeKind | None = None
    hours: int | None = Field(default=None, ge=0)
    validity_type: ValidityUnit | None = None
    validity_value: int | None = Field(default=None, ge=1)

    model_config = ConfigDict(extra="forbid")


class CertificateTypeRead(BaseModel):
    id: int
    name: str
    reference: str | None
    type: CertificateTypeKind
    hours: int
    validity_type: ValidityUnit
    validity_value: int
    created_by: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
