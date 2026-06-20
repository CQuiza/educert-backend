from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskSubmissionRead(BaseModel):
    id: int
    task_id: int
    user_id: int
    file_url: str
    original_filename: str
    mime_type: str
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskSubmissionWithUserRead(TaskSubmissionRead):
    user_name: str
    user_email: str


class TaskProgressItem(BaseModel):
    task_id: int
    task_title: str
    submitted: bool
    submission_id: int | None = None
    file_url: str | None = None
    original_filename: str | None = None
    submitted_at: datetime | None = None
