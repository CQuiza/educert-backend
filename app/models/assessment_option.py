"""Opción de respuesta."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.assessment_question import AssessmentQuestion


class AssessmentOption(Base):
    __tablename__ = "assessment_options"
    __table_args__ = (UniqueConstraint("question_id", "option_text"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assessment_questions.id", ondelete="CASCADE")
    )
    option_text: Mapped[str] = mapped_column(String(255))
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    question: Mapped[AssessmentQuestion] = relationship(
        "AssessmentQuestion", back_populates="options"
    )
