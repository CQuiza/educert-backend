"""Intento de evaluación por usuario."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.assessment_question import AssessmentQuestion
    from app.models.module_assessment import ModuleAssessment
    from app.models.user import User


class UserAssessmentAttempt(Base):
    __tablename__ = "user_assessment_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("module_assessments.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    assessment: Mapped[ModuleAssessment] = relationship(
        "ModuleAssessment", back_populates="attempts"
    )
    user: Mapped[User] = relationship()
    answers: Mapped[list[UserAssessmentAnswer]] = relationship(
        "UserAssessmentAnswer", back_populates="attempt",
        cascade="all, delete-orphan",
    )


class UserAssessmentAnswer(Base):
    __tablename__ = "user_assessment_answers"
    __table_args__ = (UniqueConstraint("attempt_id", "question_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_assessment_attempts.id", ondelete="CASCADE")
    )
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assessment_questions.id", ondelete="CASCADE")
    )
    selected_option_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assessment_options.id", ondelete="CASCADE")
    )
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    attempt: Mapped[UserAssessmentAttempt] = relationship(
        "UserAssessmentAttempt", back_populates="answers"
    )
    question: Mapped[AssessmentQuestion] = relationship(
        "AssessmentQuestion", back_populates="answers"
    )
