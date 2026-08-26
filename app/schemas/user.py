"""Esquemas de usuario."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import IdentityType, UserRole
from app.schemas.certificate import CertificateRead


class UserBase(BaseModel):
    email: EmailStr
    name: str | None = None
    first_last_name: str | None = None
    second_last_name: str | None = None
    role: UserRole
    identity_type: IdentityType
    identity_number: str = Field(..., max_length=50)
    phone_number: str | None = Field(default=None, max_length=20)
    is_active: bool = True

    @field_validator("identity_number")
    @classmethod
    def _strip_identity_number(cls, v: str) -> str:
        return v.strip()


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Campos actualizables según model.db."""

    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)
    name: str | None = None
    first_last_name: str | None = None
    second_last_name: str | None = None
    role: UserRole | None = None
    identity_type: IdentityType | None = None
    identity_number: str | None = Field(default=None, max_length=50)
    phone_number: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("identity_number")
    @classmethod
    def _strip_identity_number_update(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return v.strip()


class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str | None
    first_last_name: str | None
    second_last_name: str | None
    role: UserRole
    identity_type: IdentityType
    identity_number: str
    phone_number: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserUpdateResponse(UserRead):
    """Respuesta del PATCH: incluye cuántos certificados se reproducjeron."""

    certificates_regenerated: int = 0




class UserWithCertificatesRead(UserRead):
    certificates: list[CertificateRead] = []


class UserListResponse(BaseModel):
    items: list[UserRead]
    total: int


class UserWithCertificatesListResponse(BaseModel):
    items: list[UserWithCertificatesRead]
    total: int

