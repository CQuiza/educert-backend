"""Auditoría de trabajos en segundo plano."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkerAuditCreate(BaseModel):
    task_name: str
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    details: str | None = None


class WorkerAuditRead(BaseModel):
    id: int
    task_name: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    details: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
