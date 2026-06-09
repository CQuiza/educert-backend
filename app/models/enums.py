"""Enumeraciones alineadas con model.db."""

from enum import Enum


class UserRole(str, Enum):
    superuser = "superuser"
    admin = "admin"
    teacher = "teacher"
    student = "student"


class IdentityType(str, Enum):
    CC = "CC"
    TI = "TI"
    OTHER = "OTHER"


class CourseStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class CertificateTypeKind(str, Enum):
    basic = "basic"
    advanced = "advanced"
    diploma = "diploma"


class ValidityUnit(str, Enum):
    years = "years"
    months = "months"
    days = "days"


class CertificateStatus(str, Enum):
    active = "active"
    revoked = "revoked"
    expired = "expired"


class CertificateAuditAction(str, Enum):
    issued = "issued"
    active = "active"
    revoked = "revoked"
    deleted = "deleted"
    expired = "expired"


class WorkerStatus(str, Enum):
    running = "running"
    success = "success"
    failed = "failed"


class EmailStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"
