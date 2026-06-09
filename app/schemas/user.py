"""Esquemas de usuario."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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
    phone_number: str = Field(..., max_length=20)
    is_active: bool = True


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




class UserWithCertificatesRead(UserRead):
    certificates: list[CertificateRead] = []

