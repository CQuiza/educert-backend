"""Módulo."""

from pydantic import BaseModel, ConfigDict, Field


class ModuleCreate(BaseModel):
    course_id: int
    title: str = Field(..., max_length=255)
    order_index: int


class ModuleUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    order_index: int | None = None

    model_config = ConfigDict(extra="forbid")


class ModuleRead(BaseModel):
    id: int
    course_id: int
    title: str
    order_index: int

    model_config = ConfigDict(from_attributes=True)
