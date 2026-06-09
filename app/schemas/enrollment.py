"""Inscripción a curso."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CourseEnrollmentCreate(BaseModel):
    user_id: int
    course_id: int


class CourseEnrollmentRead(BaseModel):
    id: int
    user_id: int
    course_id: int
    enrolled_at: datetime

    model_config = ConfigDict(from_attributes=True)
