"""Pregunta de evaluación."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.assessment_option import AssessmentOption
    from app.models.module_assessment import ModuleAssessment
    from app.models.user_assessment_attempt import UserAssessmentAnswer


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("module_assessments.id", ondelete="CASCADE")
    )
    question_text: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String(20))
    points: Mapped[int] = mapped_column(Integer, default=1)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    assessment: Mapped[ModuleAssessment] = relationship(
        "ModuleAssessment", back_populates="questions"
    )
    options: Mapped[list[AssessmentOption]] = relationship(
        "AssessmentOption", back_populates="question",
        cascade="all, delete-orphan",
    )
    answers: Mapped[list[UserAssessmentAnswer]] = relationship(
        "UserAssessmentAnswer", back_populates="question",
        cascade="all, delete-orphan",
    )
