"""Esquemas de auditoría de usuarios."""

from datetime import datetime

from pydantic import BaseModel


class UserAuditRead(BaseModel):
    id: int
    user_id: int | None = None
    deleted_at: datetime
    deleted_by: int | None = None
    snapshot: dict

    model_config = {"from_attributes": True}
