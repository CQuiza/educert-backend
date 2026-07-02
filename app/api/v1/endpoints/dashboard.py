"""Dashboard — estadísticas."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.dashboard_repository import dashboard_repository
from app.schemas.dashboard import DashboardStatsResponse
from app.services.access import require_teacher_or_staff

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> DashboardStatsResponse:
    require_teacher_or_staff(current)
    stats = await dashboard_repository.get_stats(db)
    return DashboardStatsResponse(**stats)
