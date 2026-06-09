"""Curso e inscripciones."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.certificate_type import CertificateType
    from app.models.module import Module
    from app.models.user import User


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="ck_courses_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    certificate_type_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("certificate_types.id", use_alter=True),
        nullable=True,
    )
    teacher_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    status: Mapped[str] = mapped_column(
        String(20), default="draft", server_default="draft"
    )

    teacher: Mapped[User | None] = relationship(
        "User",
        back_populates="courses_teaching",
        foreign_keys=[teacher_id],
    )
    certificate_type: Mapped[CertificateType | None] = relationship(
        "CertificateType",
        foreign_keys=[certificate_type_id],
        back_populates="courses_using_type",
    )
    modules: Mapped[list["Module"]] = relationship(
        "Module",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    enrollments: Mapped[list[CourseEnrollment]] = relationship(
        "CourseEnrollment",
        back_populates="course",
        cascade="all, delete-orphan",
    )


class CourseEnrollment(Base):
    """Inscripción estudiante–curso (requerido por reglas de negocio; no está en model.db)."""

    __tablename__ = "course_enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_enrollment_user_course"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user: Mapped[User] = relationship("User", back_populates="enrollments")
    course: Mapped[Course] = relationship("Course", back_populates="enrollments")
