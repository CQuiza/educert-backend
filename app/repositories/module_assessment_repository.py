"""Repositorio de evaluaciones de módulo."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assessment_option import AssessmentOption
from app.models.assessment_question import AssessmentQuestion
from app.models.module_assessment import ModuleAssessment


class ModuleAssessmentRepository:
    async def get_by_module(
        self, db: AsyncSession, module_id: int
    ) -> ModuleAssessment | None:
        r = await db.execute(
            select(ModuleAssessment)
            .where(ModuleAssessment.module_id == module_id)
            .options(
                selectinload(ModuleAssessment.questions)
                .selectinload(AssessmentQuestion.options),
            )
        )
        return r.scalar_one_or_none()

    async def create_with_questions(
        self,
        db: AsyncSession,
        module_id: int,
        passing_score: int,
        questions_data: list[dict],
    ) -> ModuleAssessment:
        assessment = ModuleAssessment(
            module_id=module_id,
            passing_score=passing_score,
        )
        db.add(assessment)
        await db.flush()

        for i, qd in enumerate(questions_data):
            q = AssessmentQuestion(
                assessment_id=assessment.id,
                question_text=qd["question_text"],
                question_type=qd["question_type"],
                points=qd.get("points", 1),
                order_index=qd.get("order_index", i),
            )
            db.add(q)
            await db.flush()
            for od in qd.get("options", []):
                o = AssessmentOption(
                    question_id=q.id,
                    option_text=od["option_text"],
                    is_correct=od.get("is_correct", False),
                )
                db.add(o)
            await db.flush()

        return await self.get_by_module(db, assessment.module_id)

    async def update_with_questions(
        self,
        db: AsyncSession,
        assessment_id: int,
        passing_score: int,
        questions_data: list[dict],
    ) -> ModuleAssessment:
        assessment = await db.get(ModuleAssessment, assessment_id)
        if not assessment:
            raise ValueError("Assessment no encontrado")

        assessment.passing_score = passing_score

        old_questions = await db.execute(
            select(AssessmentQuestion).where(
                AssessmentQuestion.assessment_id == assessment_id
            )
        )
        for q in old_questions.scalars():
            await db.delete(q)

        await db.flush()

        for i, qd in enumerate(questions_data):
            q = AssessmentQuestion(
                assessment_id=assessment.id,
                question_text=qd["question_text"],
                question_type=qd["question_type"],
                points=qd.get("points", 1),
                order_index=qd.get("order_index", i),
            )
            db.add(q)
            await db.flush()
            for od in qd.get("options", []):
                o = AssessmentOption(
                    question_id=q.id,
                    option_text=od["option_text"],
                    is_correct=od.get("is_correct", False),
                )
                db.add(o)
            await db.flush()

        return await self.get_by_module(db, assessment.module_id)

    async def delete(self, db: AsyncSession, assessment_id: int) -> None:
        assessment = await db.get(ModuleAssessment, assessment_id)
        if assessment:
            await db.delete(assessment)

    async def get_by_id(
        self, db: AsyncSession, assessment_id: int
    ) -> ModuleAssessment | None:
        r = await db.execute(
            select(ModuleAssessment)
            .where(ModuleAssessment.id == assessment_id)
            .options(
                selectinload(ModuleAssessment.questions)
                .selectinload(AssessmentQuestion.options),
            )
        )
        return r.scalar_one_or_none()


module_assessment_repository = ModuleAssessmentRepository()
