"""Progreso."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserProgressCreate(BaseModel):
    user_id: int
    lesson_id: int
    completed: bool = False
    completed_at: datetime | None = None


class UserProgressUpdate(BaseModel):
    completed: bool | None = None
    completed_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")


class UserProgressRead(BaseModel):
    id: int
    user_id: int
    lesson_id: int
    completed: bool
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
