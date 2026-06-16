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
from app.models.assessment_option import AssessmentOption
from app.models.assessment_question import AssessmentQuestion
from app.models.lesson_file import LessonFile
from app.models.lesson_task import LessonTask
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.module_assessment import ModuleAssessment
from app.models.user_assessment_attempt import UserAssessmentAttempt, UserAssessmentAnswer
from app.models.progress import UserProgress
from app.models.user import User
from app.models.user_audit import UserAudit
from app.models.worker_audit import WorkerAudit

__all__ = [
    "AssessmentOption",
    "AssessmentQuestion",
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
    "LessonFile",
    "LessonTask",
    "Module",
    "ModuleAssessment",
    "User",
    "UserAssessmentAttempt",
    "UserAssessmentAnswer",
    "UserAudit",
    "UserProgress",
    "UserRole",
    "ValidityUnit",
    "WorkerAudit",
    "WorkerStatus",
]
