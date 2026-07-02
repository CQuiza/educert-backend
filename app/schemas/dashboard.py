"""Dashboard — estadísticas."""

from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    total_users: int
    total_certificates: int
    active_certificates: int
    expired_certificates: int
    revoked_certificates: int
    published_courses: int
    certificate_types: int
