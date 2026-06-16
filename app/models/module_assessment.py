"""Evaluación de módulo."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.assessment_question import AssessmentQuestion
    from app.models.module import Module
    from app.models.user_assessment_attempt import UserAssessmentAttempt


class ModuleAssessment(Base):
    __tablename__ = "module_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("modules.id", ondelete="CASCADE"), unique=True
    )
    passing_score: Mapped[int] = mapped_column(Integer, default=70)

    module: Mapped[Module] = relationship("Module", back_populates="assessment")
    questions: Mapped[list[AssessmentQuestion]] = relationship(
        "AssessmentQuestion", back_populates="assessment",
        cascade="all, delete-orphan", order_by="AssessmentQuestion.order_index",
    )
    attempts: Mapped[list[UserAssessmentAttempt]] = relationship(
        "UserAssessmentAttempt", back_populates="assessment",
        cascade="all, delete-orphan",
    )
