"""Progreso por lección."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lesson import Lesson
    from app.models.user import User


class UserProgress(Base):
    __tablename__ = "user_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_progress_user_lesson"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"))
    completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship("User", back_populates="progress_rows")
    lesson: Mapped[Lesson] = relationship("Lesson", back_populates="progress_rows")
