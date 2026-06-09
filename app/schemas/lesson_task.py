"""Tarea de lección."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LessonTaskCreate(BaseModel):
    lesson_id: int
    title: str = Field(..., max_length=255)
    description: str | None = None
    original_filename: str | None = None
    file_type: str = "none"
    file_url: str | None = None
    google_drive_link: str | None = None
    order_index: int = 0


class LessonTaskUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    original_filename: str | None = None
    file_type: str | None = None
    file_url: str | None = None
    google_drive_link: str | None = None
    order_index: int | None = None

    model_config = ConfigDict(extra="forbid")


class LessonTaskRead(BaseModel):
    id: int
    lesson_id: int
    title: str
    description: str | None
    original_filename: str | None
    file_type: str
    file_url: str | None
    google_drive_link: str | None
    order_index: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
