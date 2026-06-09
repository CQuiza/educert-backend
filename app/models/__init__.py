"""Modelos ORM — importar para registrar metadatos."""

from app.core.database import Base
from app.models.certificate import Certificate
from app.models.certificate_audit import CertificateAudit
from app.models.certificate_type import CertificateType
from app.models.course import Course, CourseEnrollment
from app.models.email_audit import EmailAudit
from app.models.enums import (
    CertificateAuditAction,
    CertificateStatus,
    CertificateTypeKind,
    CourseStatus,
    IdentityType,
    UserRole,
    ValidityUnit,
    WorkerStatus,
)
from app.models.lesson_task import LessonTask
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.progress import UserProgress
from app.models.user import User
from app.models.user_audit import UserAudit
from app.models.worker_audit import WorkerAudit

__all__ = [
    "Base",
    "Certificate",
    "CertificateAudit",
    "CertificateType",
    "CertificateAuditAction",
    "CertificateStatus",
    "CertificateTypeKind",
    "Course",
    "CourseEnrollment",
    "CourseStatus",
    "EmailAudit",
    "IdentityType",
    "Lesson",
    "LessonTask",
    "Module",
    "User",
    "UserAudit",
    "UserProgress",
    "UserRole",
    "ValidityUnit",
    "WorkerAudit",
    "WorkerStatus",
]
