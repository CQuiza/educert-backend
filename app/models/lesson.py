"""Lección."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lesson_task import LessonTask
    from app.models.module import Module
    from app.models.progress import UserProgress


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("module_id", "order_index", name="uq_lesson_module_order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[int] = mapped_column(Integer, ForeignKey("modules.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    text_content: Mapped[str | None] = mapped_column(Text)
    image_content_url: Mapped[str | None] = mapped_column(Text)
    video_content_url: Mapped[str | None] = mapped_column(Text)
    file_content_url: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    module: Mapped[Module] = relationship("Module", back_populates="lessons")
    progress_rows: Mapped[list[UserProgress]] = relationship(
        "UserProgress",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list[LessonTask]] = relationship(
        "LessonTask",
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="LessonTask.order_index",
    )
