"""Tarea asociada a una lección."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lesson import Lesson


class LessonTask(Base):
    __tablename__ = "lesson_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lesson_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(
        String(20), default="none", server_default="none"
    )
    file_url: Mapped[str | None] = mapped_column(Text)
    google_drive_link: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    lesson: Mapped[Lesson] = relationship("Lesson", back_populates="tasks")
