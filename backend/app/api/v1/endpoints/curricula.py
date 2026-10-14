"""Curriculum Taxonomy API Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.taxonomy import BoardCurriculum, GradeStage, Subject
from app.schemas.curriculum import (
    BoardCurriculumResponse,
    GradeStageResponse,
    SubjectResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=List[BoardCurriculumResponse],
    status_code=status.HTTP_200_OK,
    summary="List Supported Educational Curricula",
)
async def list_curricula(
    db: AsyncSession = Depends(get_db),
) -> List[BoardCurriculumResponse]:
    """Retrieve all active curricula, grade stages, and subjects."""
    stmt = (
        select(BoardCurriculum)
        .where(BoardCurriculum.is_active == True)
        .options(
            selectinload(BoardCurriculum.grades)
            .selectinload(GradeStage.subjects)
        )
        .order_by(BoardCurriculum.name.asc())
    )
    result = await db.execute(stmt)
    boards = result.scalars().all()

    response: List[BoardCurriculumResponse] = []
    for board in boards:
        grades_resp: List[GradeStageResponse] = []
        for grade in sorted(board.grades, key=lambda g: g.display_order):
            subjects_resp = [
                SubjectResponse(
                    id=sub.id,
                    grade_stage_id=sub.grade_stage_id,
                    code=sub.code,
                    name=sub.name,
                    icon_url=sub.icon_url,
                    display_order=sub.display_order,
                )
                for sub in sorted(grade.subjects, key=lambda s: s.display_order)
            ]
            grades_resp.append(
                GradeStageResponse(
                    id=grade.id,
                    board_id=grade.board_id,
                    code=grade.code,
                    name=grade.name,
                    display_order=grade.display_order,
                    subjects=subjects_resp,
                )
            )
        response.append(
            BoardCurriculumResponse(
                id=board.id,
                code=board.code,
                name=board.name,
                country_code=board.country_code,
                description=board.description,
                is_active=board.is_active,
                grades=grades_resp,
            )
        )

    return response
