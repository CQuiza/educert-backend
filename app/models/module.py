"""Módulo de curso."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.lesson import Lesson


class Module(Base):
    __tablename__ = "modules"
    __table_args__ = (UniqueConstraint("course_id", "order_index", name="uq_module_course_order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    course: Mapped[Course] = relationship("Course", back_populates="modules")
    lessons: Mapped[list[Lesson]] = relationship(
        "Lesson",
        back_populates="module",
        cascade="all, delete-orphan",
    )
