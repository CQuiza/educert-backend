from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.task_submission import TaskSubmission
from app.models.user import User


class TaskSubmissionRepository:
    async def get_by_id(
        self, db: AsyncSession, submission_id: int
    ) -> TaskSubmission | None:
        r = await db.execute(
            select(TaskSubmission)
            .where(TaskSubmission.id == submission_id)
            .options(joinedload(TaskSubmission.user))
        )
        return r.unique().scalar_one_or_none()

    async def get_by_task_and_user(
        self, db: AsyncSession, task_id: int, user_id: int
    ) -> TaskSubmission | None:
        r = await db.execute(
            select(TaskSubmission).where(
                TaskSubmission.task_id == task_id,
                TaskSubmission.user_id == user_id,
            )
        )
        return r.scalar_one_or_none()

    async def list_by_task(
        self, db: AsyncSession, task_id: int
    ) -> Sequence[tuple[TaskSubmission, User]]:
        r = await db.execute(
            select(TaskSubmission)
            .where(TaskSubmission.task_id == task_id)
            .options(joinedload(TaskSubmission.user))
            .order_by(TaskSubmission.submitted_at.desc())
        )
        return r.unique().scalars().all()

    async def create(
        self,
        db: AsyncSession,
        *,
        task_id: int,
        user_id: int,
        file_url: str,
        original_filename: str,
        mime_type: str = "application/pdf",
    ) -> TaskSubmission:
        s = TaskSubmission(
            task_id=task_id,
            user_id=user_id,
            file_url=file_url,
            original_filename=original_filename,
            mime_type=mime_type,
        )
        db.add(s)
        await db.flush()
        await db.refresh(s)
        return s

    async def delete(self, db: AsyncSession, submission: TaskSubmission) -> None:
        await db.delete(submission)


task_submission_repository = TaskSubmissionRepository()
