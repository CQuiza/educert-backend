"""Esquemas de auditoría de correos electrónicos."""

from datetime import datetime

from pydantic import BaseModel


class EmailAuditRead(BaseModel):
    id: int
    user_name: str | None = None
    email_to: str
    email_type: str
    status: str
    error: str | None = None
    created_at: datetime
    sent_at: datetime | None = None

    model_config = {"from_attributes": True}
