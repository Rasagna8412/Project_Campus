"""Curriculum Taxonomy and Content API Endpoints."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.content import ContentStatus, Lesson, LessonSection
from app.models.taxonomy import BoardCurriculum, Chapter, GradeStage, Subject, Topic
from app.schemas.content import (
    ChapterResponse,
    LessonDetailResponse,
    LessonSectionResponse,
    LessonSummaryResponse,
    TopicResponse,
)
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


@router.get(
    "/subjects/{subject_id}/chapters",
    response_model=List[ChapterResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Chapters and Topics for a Subject",
)
async def get_subject_chapters(
    subject_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[ChapterResponse]:
    """Retrieve all chapters and topics under a specific subject."""
    subj = await db.get(Subject, subject_id)
    if not subj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    stmt = (
        select(Chapter)
        .where(Chapter.subject_id == subject_id)
        .options(
            selectinload(Chapter.topics).selectinload(Topic.lessons)
        )
        .order_by(Chapter.chapter_number.asc(), Chapter.display_order.asc())
    )
    result = await db.execute(stmt)
    chapters = result.scalars().all()

    chapters_resp: List[ChapterResponse] = []
    for chapter in chapters:
        topics_resp: List[TopicResponse] = []
        for topic in sorted(chapter.topics, key=lambda t: t.display_order):
            pub_count = sum(
                1 for lesson in topic.lessons
                if lesson.status == ContentStatus.PUBLISHED.value
            )
            topics_resp.append(
                TopicResponse(
                    id=topic.id,
                    chapter_id=topic.chapter_id,
                    topic_number=topic.topic_number,
                    title=topic.title,
                    slug=topic.slug,
                    importance_weight=topic.importance_weight,
                    display_order=topic.display_order,
                    published_lessons_count=pub_count,
                )
            )
        chapters_resp.append(
            ChapterResponse(
                id=chapter.id,
                subject_id=chapter.subject_id,
                chapter_number=chapter.chapter_number,
                title=chapter.title,
                slug=chapter.slug,
                summary=chapter.summary,
                display_order=chapter.display_order,
                topics=topics_resp,
            )
        )

    return chapters_resp


@router.get(
    "/chapters/{chapter_id}/topics",
    response_model=List[TopicResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Topics for a Chapter",
)
async def get_chapter_topics(
    chapter_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[TopicResponse]:
    """Retrieve all topics under a chapter."""
    ch = await db.get(Chapter, chapter_id)
    if not ch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found",
        )

    stmt = (
        select(Topic)
        .where(Topic.chapter_id == chapter_id)
        .options(selectinload(Topic.lessons))
        .order_by(Topic.display_order.asc())
    )
    result = await db.execute(stmt)
    topics = result.scalars().all()

    topics_resp: List[TopicResponse] = []
    for topic in topics:
        pub_count = sum(
            1 for lesson in topic.lessons
            if lesson.status == ContentStatus.PUBLISHED.value
        )
        topics_resp.append(
            TopicResponse(
                id=topic.id,
                chapter_id=topic.chapter_id,
                topic_number=topic.topic_number,
                title=topic.title,
                slug=topic.slug,
                importance_weight=topic.importance_weight,
                display_order=topic.display_order,
                published_lessons_count=pub_count,
            )
        )
    return topics_resp


@router.get(
    "/topics/{topic_id}/lessons",
    response_model=List[LessonSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Published Lessons for a Topic",
)
async def get_topic_lessons(
    topic_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[LessonSummaryResponse]:
    """Retrieve all published lessons for a specific topic."""
    tp = await db.get(Topic, topic_id)
    if not tp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )

    stmt = (
        select(Lesson)
        .where(
            Lesson.topic_id == topic_id,
            Lesson.status == ContentStatus.PUBLISHED.value,
        )
        .order_by(Lesson.display_order.asc())
    )
    result = await db.execute(stmt)
    lessons = result.scalars().all()

    return [LessonSummaryResponse.model_validate(l) for l in lessons]


@router.get(
    "/lessons/{lesson_id}",
    response_model=LessonDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Published Lesson Content and Sections",
)
async def get_lesson_detail(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> LessonDetailResponse:
    """Retrieve detailed content and ordered sections for a published lesson."""
    stmt = (
        select(Lesson)
        .where(
            Lesson.id == lesson_id,
            Lesson.status == ContentStatus.PUBLISHED.value,
        )
        .options(selectinload(Lesson.sections))
    )
    result = await db.execute(stmt)
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found or not published",
        )

    sorted_sections = sorted(lesson.sections, key=lambda s: s.display_order)
    sections_resp = [
        LessonSectionResponse.model_validate(s) for s in sorted_sections
    ]

    return LessonDetailResponse(
        id=lesson.id,
        topic_id=lesson.topic_id,
        title=lesson.title,
        slug=lesson.slug,
        summary=lesson.summary,
        learning_objectives=lesson.learning_objectives,
        estimated_read_time_minutes=lesson.estimated_read_time_minutes,
        status=lesson.status,
        display_order=lesson.display_order,
        provenance=lesson.provenance,
        is_verified=lesson.is_verified,
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
        sections=sections_resp,
    )
