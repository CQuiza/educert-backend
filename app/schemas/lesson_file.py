"""Archivo de lección."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LessonFileCreate(BaseModel):
    original_filename: str
    mime_type: str | None = None
    order_index: int = 0


class LessonFileRead(LessonFileCreate):
    id: int
    lesson_id: int
    file_url: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
