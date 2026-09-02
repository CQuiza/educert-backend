"""Evaluaciones por módulo y progreso."""

import random
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.course_repository import course_repository
from app.repositories.enrollment_repository import course_enrollment_repository
from app.repositories.module_assessment_repository import (
    module_assessment_repository,
)
from app.repositories.module_repository import module_repository
from app.repositories.user_assessment_repository import (
    user_assessment_repository,
)
from app.schemas.module_assessment import (
    AllProgressSummary,
    AssessmentSubmit,
    AttemptResult,
    AnswerResult,
    CourseProgressSummary,
    ModuleAssessmentCreate,
    ModuleAssessmentRead,
    ModuleAssessmentReadTeacher,
    ModuleProgressItem,
)
from app.services.access import (
    is_super_or_admin,
    is_teacher,
    require_teacher_or_staff,
)

router = APIRouter(tags=["assessments"])


async def _get_assessment_or_404(
    db: AsyncSession, assessment_id: int
) -> object:
    assessment = await module_assessment_repository.get_by_id(
        db, assessment_id
    )
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluación no encontrada",
        )
    return assessment


async def _assert_enrolled(
    db: AsyncSession, user: User, module_id: int
) -> None:
    mod = await module_repository.get_by_id(db, module_id)
    if not mod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado"
        )
    if is_super_or_admin(user) or is_teacher(user):
        return
    enr = await course_enrollment_repository.get_by_user_course(
        db, user.id, mod.course_id
    )
    if not enr:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No inscrito en este curso",
        )


# --- Teacher/Admin: CRUD assessment ---

@router.get(
    "/modules/{module_id}/assessment",
)
async def get_module_assessment(
    module_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    assessment = await module_assessment_repository.get_by_module(db, module_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Este módulo no tiene evaluación configurada",
        )
    await _assert_enrolled(db, current, module_id)

    if is_super_or_admin(current) or is_teacher(current):
        return ModuleAssessmentReadTeacher.model_validate(assessment)

    data = ModuleAssessmentRead.model_validate(assessment)
    for q in data.questions:
        q.options = random.sample(q.options, len(q.options))
    return data


@router.post(
    "/modules/{module_id}/assessment",
    response_model=ModuleAssessmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_module_assessment(
    module_id: int,
    body: ModuleAssessmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> object:
    require_teacher_or_staff(current)
    existing = await module_assessment_repository.get_by_module(db, module_id)
    questions_data = [q.model_dump() for q in body.questions]

    if existing:
        return await module_assessment_repository.update_with_questions(
            db, existing.id, body.passing_score, questions_data
        )
    return await module_assessment_repository.create_with_questions(
        db, module_id, body.passing_score, questions_data
    )


@router.delete(
    "/assessments/{assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_assessment(
    assessment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> None:
    require_teacher_or_staff(current)
    await module_assessment_repository.delete(db, assessment_id)


# --- Student: submit & attempts ---

@router.post(
    "/assessments/{assessment_id}/submit",
    response_model=AttemptResult,
)
async def submit_assessment(
    assessment_id: int,
    body: AssessmentSubmit,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> dict:
    assessment = await _get_assessment_or_404(db, assessment_id)

    if current.role == UserRole.student.value:
        mod = await module_repository.get_by_id(db, assessment.module_id)
        if mod:
            await _assert_enrolled(db, current, mod.id)

    attempt = await user_assessment_repository.create_attempt(
        db, assessment_id, current.id
    )
    answers_data = [a.model_dump() for a in body.answers]
    attempt = await user_assessment_repository.submit_answers(
        db, attempt.id, answers_data
    )

    attempt_loaded = await user_assessment_repository.get_attempt(
        db, attempt.id
    )

    answers_result = []
    for ans in (attempt_loaded.answers if attempt_loaded else []):
        q = next((q for q in assessment.questions if q.id == ans.question_id), None)
        if not q:
            continue
        selected_opt = next(
            (o for o in q.options if o.id == ans.selected_option_id), None
        )
        correct_opt = next((o for o in q.options if o.is_correct), None)
        answers_result.append(
            AnswerResult(
                question_id=ans.question_id,
                question_text=q.question_text,
                selected_option_id=ans.selected_option_id,
                is_correct=ans.is_correct,
                correct_option_id=correct_opt.id if correct_opt else None,
                selected_option_text=selected_opt.option_text if selected_opt else None,
                correct_option_text=correct_opt.option_text if correct_opt else None,
            ).model_dump()
        )

    return {
        "attempt_id": attempt.id,
        "score": float(attempt.score),
        "passed": attempt.passed,
        "total_points": sum(q.points for q in assessment.questions),
        "earned_points": float(attempt.score) / 100 * sum(q.points for q in assessment.questions) if attempt.score else 0,
        "answers": answers_result,
    }


@router.get(
    "/assessments/{assessment_id}/attempts",
)
async def get_attempts(
    assessment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list:
    attempts = await user_assessment_repository.get_attempts_by_assessment(
        db, assessment_id, current.id
    )
    return list(attempts)


# --- Progreso ---

@router.get(
    "/progress/summary",
    response_model=AllProgressSummary,
)
async def get_all_progress(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    user_id: Annotated[int | None, Query()] = None,
) -> dict:
    uid = current.id
    if user_id is not None:
        if user_id != current.id and not (is_super_or_admin(current) or is_teacher(current)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso"
            )
        uid = user_id

    courses_data = await user_assessment_repository.get_all_progress(db, uid)
    total_mods = sum(c["total_modules"] for c in courses_data)
    completed_mods = sum(c["completed_modules"] for c in courses_data)
    overall = (completed_mods / total_mods * 100) if total_mods > 0 else 0.0

    return {
        "courses": [
            CourseProgressSummary(**c).model_dump()
            for c in courses_data
        ],
        "overall_percent": round(overall, 1),
    }


@router.get(
    "/progress/summary/{course_id}",
    response_model=CourseProgressSummary,
)
async def get_course_progress(
    course_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    user_id: Annotated[int | None, Query()] = None,
) -> dict:
    uid = current.id
    if user_id is not None:
        if user_id != current.id and not (is_super_or_admin(current) or is_teacher(current)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Sin permiso"
            )
        uid = user_id

    course = await course_repository.get_by_id(db, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Curso no encontrado"
        )

    modules_data = await user_assessment_repository.get_course_progress(
        db, uid, course_id
    )
    total = len(modules_data)
    completed = sum(1 for m in modules_data if m["passed"])
    pct = (completed / total * 100) if total > 0 else 0.0

    return {
        "course_id": course.id,
        "course_title": course.title,
        "total_modules": total,
        "completed_modules": completed,
        "progress_percent": round(pct, 1),
        "modules": [
            ModuleProgressItem(**m).model_dump() for m in modules_data
        ],
    }
