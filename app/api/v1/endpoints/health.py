"""Salud del servicio."""

import asyncio
from fastapi import APIRouter, HTTPException, status

from app.workers.celery_config import celery_app

router = APIRouter(tags=["health"])


@router.get("/health", summary="Estado del API")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/workers", summary="Estado de los workers de Celery")
async def health_workers() -> dict:
    try:
        def _ping():
            inspector = celery_app.control.inspect(timeout=1.0)
            return inspector.ping()

        ping_res = await asyncio.to_thread(_ping)

        if not ping_res:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No celery workers are responding",
            )

        workers_status = {}
        for worker, status_info in ping_res.items():
            workers_status[worker] = (
                status_info.get("ok", "unknown")
                if isinstance(status_info, dict)
                else "unknown"
            )

        return {"status": "healthy", "workers": workers_status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error checking worker health: {str(e)}",
        )

