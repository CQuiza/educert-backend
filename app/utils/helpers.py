"""Helpers compartidos entre módulos."""

from app.models.user import User


def student_display_name(user: User) -> str:
    parts = [user.name, user.first_last_name, user.second_last_name or ""]
    return " ".join(x for x in parts if x).strip()
