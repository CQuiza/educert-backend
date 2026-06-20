"""Repositorio de intentos de evaluación por usuario."""

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assessment_option import AssessmentOption
from app.models.assessment_question import AssessmentQuestion
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.lesson_task import LessonTask
from app.models.module import Module
from app.models.module_assessment import ModuleAssessment
from app.models.task_submission import TaskSubmission
from app.models.user_assessment_attempt import (
    UserAssessmentAnswer,
    UserAssessmentAttempt,
)


class UserAssessmentRepository:
    async def create_attempt(
        self,
        db: AsyncSession,
        assessment_id: int,
        user_id: int,
    ) -> UserAssessmentAttempt:
        attempt = UserAssessmentAttempt(
            assessment_id=assessment_id,
            user_id=user_id,
            started_at=datetime.now(UTC),
        )
        db.add(attempt)
        await db.flush()
        await db.refresh(attempt)
        return attempt

    async def submit_answers(
        self,
        db: AsyncSession,
        attempt_id: int,
        answers_data: list[dict],
    ) -> UserAssessmentAttempt:
        attempt = await db.get(UserAssessmentAttempt, attempt_id)
        if not attempt:
            raise ValueError("Intento no encontrado")

        assessment = await db.execute(
            select(ModuleAssessment)
            .where(ModuleAssessment.id == attempt.assessment_id)
            .options(
                selectinload(ModuleAssessment.questions)
                .selectinload(AssessmentQuestion.options),
            )
        )
        assessment_model = assessment.scalar_one_or_none()
        if not assessment_model:
            raise ValueError("Assessment no encontrado")

        question_map: dict[int, AssessmentQuestion] = {}
        option_map: dict[int, AssessmentOption] = {}
        for q in assessment_model.questions:
            question_map[q.id] = q
            for o in q.options:
                option_map[o.id] = o

        total_points = sum(q.points for q in assessment_model.questions)
        earned_points = 0

        for ad in answers_data:
            qid = ad["question_id"]
            oid = ad["selected_option_id"]

            if qid not in question_map:
                continue
            if oid not in option_map or option_map[oid].question_id != qid:
                continue

            is_correct = option_map[oid].is_correct
            if is_correct:
                earned_points += question_map[qid].points

            answer = UserAssessmentAnswer(
                attempt_id=attempt_id,
                question_id=qid,
                selected_option_id=oid,
                is_correct=is_correct,
            )
            db.add(answer)

        if total_points > 0:
            score = float(Decimal(earned_points) / Decimal(total_points) * 100)
        else:
            score = 0.0

        attempt.score = round(Decimal(str(score)), 2)
        attempt.passed = score >= assessment_model.passing_score
        attempt.finished_at = datetime.now(UTC)

        await db.flush()
        await db.refresh(attempt)
        return attempt

    async def get_attempt(
        self, db: AsyncSession, attempt_id: int
    ) -> UserAssessmentAttempt | None:
        r = await db.execute(
            select(UserAssessmentAttempt)
            .where(UserAssessmentAttempt.id == attempt_id)
            .options(
                selectinload(UserAssessmentAttempt.answers)
                .selectinload(UserAssessmentAnswer.question),
            )
        )
        return r.scalar_one_or_none()

    async def get_attempts_by_assessment(
        self,
        db: AsyncSession,
        assessment_id: int,
        user_id: int,
    ) -> Sequence[UserAssessmentAttempt]:
        r = await db.execute(
            select(UserAssessmentAttempt)
            .where(
                UserAssessmentAttempt.assessment_id == assessment_id,
                UserAssessmentAttempt.user_id == user_id,
            )
            .order_by(UserAssessmentAttempt.started_at.desc())
        )
        return r.scalars().all()

    async def _get_module_task_progress(
        self,
        db: AsyncSession,
        module_id: int,
        user_id: int,
    ) -> tuple[int, int, list[dict]]:
        """Returns (total_tasks, submitted_tasks, tasks_detail) for a module."""
        r = await db.execute(
            select(Lesson).where(Lesson.module_id == module_id)
        )
        lesson_ids = [les.id for les in r.scalars().all()]
        if not lesson_ids:
            return 0, 0, []

        r2 = await db.execute(
            select(LessonTask)
            .where(LessonTask.lesson_id.in_(lesson_ids))
            .order_by(LessonTask.order_index)
        )
        tasks = r2.scalars().all()
        if not tasks:
            return 0, 0, []

        task_ids = [t.id for t in tasks]
        r3 = await db.execute(
            select(TaskSubmission).where(
                TaskSubmission.task_id.in_(task_ids),
                TaskSubmission.user_id == user_id,
            )
        )
        submissions = r3.scalars().all()
        sub_map = {s.task_id: s for s in submissions}

        tasks_detail = []
        for t in tasks:
            s = sub_map.get(t.id)
            tasks_detail.append({
                "task_id": t.id,
                "task_title": t.title,
                "submitted": s is not None,
                "submission_id": s.id if s else None,
                "file_url": s.file_url if s else None,
                "original_filename": s.original_filename if s else None,
                "submitted_at": s.submitted_at if s else None,
            })

        return len(tasks), len(submissions), tasks_detail

    async def has_passed(
        self,
        db: AsyncSession,
        assessment_id: int,
        user_id: int,
    ) -> bool:
        r = await db.execute(
            select(func.exists().where(
                UserAssessmentAttempt.assessment_id == assessment_id,
                UserAssessmentAttempt.user_id == user_id,
                UserAssessmentAttempt.passed.is_(True),
            ))
        )
        return r.scalar() or False

    async def get_course_progress(
        self,
        db: AsyncSession,
        user_id: int,
        course_id: int,
    ) -> list[dict]:
        r = await db.execute(
            select(Module)
            .where(Module.course_id == course_id)
            .order_by(Module.order_index)
            .options(
                selectinload(Module.assessment)
                .selectinload(ModuleAssessment.questions),
            )
        )
        modules = r.scalars().all()

        assessment_ids = [m.assessment.id for m in modules if m.assessment]
        attempts_map: dict[int, list[UserAssessmentAttempt]] = {}
        if assessment_ids:
            a_r = await db.execute(
                select(UserAssessmentAttempt)
                .where(
                    UserAssessmentAttempt.assessment_id.in_(assessment_ids),
                    UserAssessmentAttempt.user_id == user_id,
                )
                .order_by(UserAssessmentAttempt.finished_at.desc())
            )
            for a in a_r.scalars().all():
                attempts_map.setdefault(a.assessment_id, []).append(a)

        result = []
        for mod in modules:
            assessment = mod.assessment
            total_questions = len(assessment.questions) if assessment else 0
            attempts = attempts_map.get(assessment.id, []) if assessment else []
            attempts_count = len(attempts)
            last_score = float(attempts[0].score) if attempts else None
            passed = any(a.passed for a in attempts)

            total_tasks, submitted_tasks, tasks = (
                await self._get_module_task_progress(db, mod.id, user_id)
            )

            result.append({
                "module_id": mod.id,
                "module_title": mod.title,
                "module_order": mod.order_index,
                "total_assessment_questions": total_questions,
                "attempts_count": attempts_count,
                "last_score": last_score,
                "passed": passed,
                "total_tasks": total_tasks,
                "submitted_tasks": submitted_tasks,
                "tasks": tasks,
            })

        return result

    async def get_all_progress(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> list[dict]:
        from app.models.course import CourseEnrollment

        enr_r = await db.execute(
            select(CourseEnrollment.course_id).where(
                CourseEnrollment.user_id == user_id
            )
        )
        enrolled_ids = {row[0] for row in enr_r.all()}
        if not enrolled_ids:
            return []

        r = await db.execute(
            select(Course)
            .where(Course.id.in_(enrolled_ids))
            .order_by(Course.title)
            .options(
                selectinload(Course.modules)
                .selectinload(Module.assessment)
                .selectinload(ModuleAssessment.questions),
            )
        )
        courses = r.scalars().all()

        all_assessment_ids = [
            m.assessment.id for c in courses
            for m in c.modules if m.assessment
        ]
        attempts_map: dict[int, list[UserAssessmentAttempt]] = {}
        if all_assessment_ids:
            a_r = await db.execute(
                select(UserAssessmentAttempt)
                .where(
                    UserAssessmentAttempt.assessment_id.in_(all_assessment_ids),
                    UserAssessmentAttempt.user_id == user_id,
                )
                .order_by(UserAssessmentAttempt.finished_at.desc())
            )
            for a in a_r.scalars().all():
                attempts_map.setdefault(a.assessment_id, []).append(a)

        result = []
        for course in courses:
            modules_data = []
            for mod in course.modules:
                assessment = mod.assessment
                total_questions = len(assessment.questions) if assessment else 0
                attempts = attempts_map.get(assessment.id, []) if assessment else []
                attempts_count = len(attempts)
                last_score = float(attempts[0].score) if attempts else None
                passed = any(a.passed for a in attempts)

                total_tasks, submitted_tasks, tasks = (
                    await self._get_module_task_progress(db, mod.id, user_id)
                )

                modules_data.append({
                    "module_id": mod.id,
                    "module_title": mod.title,
                    "module_order": mod.order_index,
                    "total_assessment_questions": total_questions,
                    "attempts_count": attempts_count,
                    "last_score": last_score,
                    "passed": passed,
                    "total_tasks": total_tasks,
                    "submitted_tasks": submitted_tasks,
                    "tasks": tasks,
                })

            total = len(modules_data)
            completed = sum(1 for m in modules_data if m["passed"])
            pct = (completed / total * 100) if total > 0 else 0.0

            result.append({
                "course_id": course.id,
                "course_title": course.title,
                "total_modules": total,
                "completed_modules": completed,
                "progress_percent": round(pct, 1),
                "modules": modules_data,
            })

        return result


user_assessment_repository = UserAssessmentRepository()
