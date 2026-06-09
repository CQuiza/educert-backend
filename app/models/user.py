"""Usuario."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.certificate import Certificate
    from app.models.course import Course, CourseEnrollment
    from app.models.progress import UserProgress


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('superuser', 'admin', 'teacher', 'student')",
            name="ck_users_role",
        ),
        CheckConstraint(
            "identity_type IN ('CC', 'TI', 'OTHER')",
            name="ck_users_identity_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    first_last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    second_last_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    identity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    identity_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    refresh_token_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    courses_teaching: Mapped[list[Course]] = relationship(
        "Course",
        back_populates="teacher",
        foreign_keys="Course.teacher_id",
    )
    progress_rows: Mapped[list[UserProgress]] = relationship(
        "UserProgress",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    certificates: Mapped[list[Certificate]] = relationship(
        "Certificate",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    enrollments: Mapped[list[CourseEnrollment]] = relationship(
        "CourseEnrollment",
        back_populates="user",
        cascade="all, delete-orphan",
    )
