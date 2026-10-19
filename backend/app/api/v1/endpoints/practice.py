"""Assessment, Question Bank, Practice Engine, and Errata Endpoints."""

import math
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.assessment import (
    PracticeSession,
    Question,
    QuestionAnswerKey,
    QuestionAttempt,
    QuestionErrataReport,
    QuestionOption,
    QuestionType,
)
from app.core.review_service import trigger_review_item_on_practice_complete
from app.models.content import ContentStatus
from app.models.identity import User
from app.models.taxonomy import Topic
from app.schemas.assessment import (
    CreateErrataRequest,
    CreatePracticeSessionRequest,
    ErrataResponse,
    PracticeSessionResponse,
    PracticeSessionSummaryResponse,
    QuestionEvaluationResponse,
    QuestionOptionResponse,
    QuestionStudentResponse,
    SubmitAnswerRequest,
)

router = APIRouter()


@router.get(
    "/topics/{topic_id}/questions",
    response_model=List[QuestionStudentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Published Practice Questions for a Topic",
)
async def get_topic_questions(
    topic_id: uuid.UUID,
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> List[QuestionStudentResponse]:
    """Retrieve published questions for practice under a specific topic.

    CRITICAL: Never leaks answer keys, correct answers, or teacher explanations.
    Filters strictly for PUBLISHED status (omits DRAFT or IN_REVIEW).
    """
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )

    stmt = (
        select(Question)
        .where(
            Question.topic_id == topic_id,
            Question.status == ContentStatus.PUBLISHED.value,
        )
        .options(selectinload(Question.options))
        .order_by(Question.created_at.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    questions = result.scalars().all()

    return [
        QuestionStudentResponse(
            id=q.id,
            topic_id=q.topic_id,
            lesson_id=q.lesson_id,
            question_type=q.question_type,
            difficulty=q.difficulty,
            content_latex=q.content_latex,
            hints=q.hints,
            diagram_url=q.diagram_url,
            provenance=q.provenance,
            is_verified=q.is_verified,
            options=[
                QuestionOptionResponse(
                    id=opt.id,
                    option_key=opt.option_key,
                    content_latex=opt.content_latex,
                    display_order=opt.display_order,
                )
                for opt in sorted(q.options, key=lambda o: o.display_order)
            ],
        )
        for q in questions
    ]


@router.post(
    "/sessions",
    response_model=PracticeSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start an Interactive Topic Practice Session",
)
async def create_practice_session(
    payload: CreatePracticeSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PracticeSessionResponse:
    """Create a practice session batch of questions for the authenticated student."""
    if payload.topic_id:
        topic = await db.get(Topic, payload.topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found",
            )

    # Query published questions matching filters
    query = (
        select(Question)
        .where(Question.status == ContentStatus.PUBLISHED.value)
        .options(selectinload(Question.options))
    )

    if payload.topic_id:
        query = query.where(Question.topic_id == payload.topic_id)
    if payload.lesson_id:
        query = query.where(Question.lesson_id == payload.lesson_id)
    if payload.difficulty:
        query = query.where(Question.difficulty == payload.difficulty)

    query = query.order_by(Question.created_at.asc()).limit(payload.limit)
    res = await db.execute(query)
    questions = res.scalars().all()

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published questions available for the selected topic criteria",
        )

    # Create session
    session = PracticeSession(
        user_id=current_user.id,
        topic_id=payload.topic_id,
        session_type="TOPIC_PRACTICE",
        total_questions=len(questions),
        correct_count=0,
        is_completed=False,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Return session with student-facing questions
    student_questions = [
        QuestionStudentResponse(
            id=q.id,
            topic_id=q.topic_id,
            lesson_id=q.lesson_id,
            question_type=q.question_type,
            difficulty=q.difficulty,
            content_latex=q.content_latex,
            hints=q.hints,
            diagram_url=q.diagram_url,
            provenance=q.provenance,
            is_verified=q.is_verified,
            options=[
                QuestionOptionResponse(
                    id=opt.id,
                    option_key=opt.option_key,
                    content_latex=opt.content_latex,
                    display_order=opt.display_order,
                )
                for opt in sorted(q.options, key=lambda o: o.display_order)
            ],
        )
        for q in questions
    ]

    return PracticeSessionResponse(
        id=session.id,
        user_id=session.user_id,
        topic_id=session.topic_id,
        session_type=session.session_type,
        total_questions=session.total_questions,
        correct_count=session.correct_count,
        is_completed=session.is_completed,
        started_at=session.created_at,
        completed_at=session.completed_at,
        questions=student_questions,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=PracticeSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Practice Session Status",
)
async def get_practice_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PracticeSessionResponse:
    """Retrieve session details for the authenticated student (IDOR protected)."""
    session = await db.get(PracticeSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice session not found",
        )

    # Fetch questions for this session topic
    questions = []
    if session.topic_id:
        stmt = (
            select(Question)
            .where(
                Question.topic_id == session.topic_id,
                Question.status == ContentStatus.PUBLISHED.value,
            )
            .options(selectinload(Question.options))
            .order_by(Question.created_at.asc())
            .limit(session.total_questions)
        )
        res = await db.execute(stmt)
        questions = res.scalars().all()

    student_questions = [
        QuestionStudentResponse(
            id=q.id,
            topic_id=q.topic_id,
            lesson_id=q.lesson_id,
            question_type=q.question_type,
            difficulty=q.difficulty,
            content_latex=q.content_latex,
            hints=q.hints,
            diagram_url=q.diagram_url,
            provenance=q.provenance,
            is_verified=q.is_verified,
            options=[
                QuestionOptionResponse(
                    id=opt.id,
                    option_key=opt.option_key,
                    content_latex=opt.content_latex,
                    display_order=opt.display_order,
                )
                for opt in sorted(q.options, key=lambda o: o.display_order)
            ],
        )
        for q in questions
    ]

    return PracticeSessionResponse(
        id=session.id,
        user_id=session.user_id,
        topic_id=session.topic_id,
        session_type=session.session_type,
        total_questions=session.total_questions,
        correct_count=session.correct_count,
        is_completed=session.is_completed,
        started_at=session.created_at,
        completed_at=session.completed_at,
        questions=student_questions,
    )


@router.post(
    "/submit",
    response_model=QuestionEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Answer for Atomic Evaluation and Receive Explanation",
)
async def submit_answer(
    payload: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuestionEvaluationResponse:
    """Evaluate submitted student answer atomically and return verified educator solution."""
    stmt = (
        select(Question)
        .where(
            Question.id == payload.question_id,
            Question.status == ContentStatus.PUBLISHED.value,
        )
        .options(
            selectinload(Question.answer_key),
            selectinload(Question.options),
        )
    )
    result = await db.execute(stmt)
    question = result.scalar_one_or_none()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found or not published",
        )

    # Validate session if provided
    session: Optional[PracticeSession] = None
    if payload.session_id:
        session = await db.get(PracticeSession, payload.session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Practice session not found",
            )
        if session.is_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Practice session is already completed",
            )
        if session.topic_id and question.topic_id != session.topic_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question does not belong to this practice session topic",
            )

        # Prevent duplicate submissions for the same question within the session
        dup_stmt = select(QuestionAttempt.id).where(
            QuestionAttempt.session_id == session.id,
            QuestionAttempt.question_id == question.id,
        )
        dup_res = await db.execute(dup_stmt)
        if dup_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question already submitted in this session",
            )

    answer_key: Optional[QuestionAnswerKey] = question.answer_key
    if not answer_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Question answer key not configured",
        )

    # 1. Deterministic Evaluation Logic
    is_correct = False
    q_type = question.question_type

    if q_type in (QuestionType.SINGLE_CHOICE.value, QuestionType.MULTIPLE_CHOICE.value):
        if payload.selected_options:
            valid_keys = {opt.option_key for opt in question.options}
            if not set(payload.selected_options).issubset(valid_keys):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected options do not belong to this question",
                )

        if q_type == QuestionType.SINGLE_CHOICE.value:
            if (
                payload.selected_options
                and len(payload.selected_options) == 1
                and answer_key.correct_options
            ):
                is_correct = payload.selected_options[0] in answer_key.correct_options

        elif q_type == QuestionType.MULTIPLE_CHOICE.value:
            if payload.selected_options and answer_key.correct_options:
                is_correct = sorted(payload.selected_options) == sorted(answer_key.correct_options)

    elif q_type == QuestionType.NUMERICAL.value:
        if payload.submitted_numerical is not None:
            if not math.isfinite(payload.submitted_numerical):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Submitted numerical value must be a finite number",
                )
            if answer_key.numerical_value is not None:
                tol = (
                    answer_key.numerical_tolerance
                    if answer_key.numerical_tolerance is not None
                    else 0.01
                )
                # Use tol + 1e-9 to avoid binary floating-point roundoff at exact boundary
                is_correct = abs(payload.submitted_numerical - answer_key.numerical_value) <= (tol + 1e-9)

    elif q_type == QuestionType.INTEGER.value:
        if (
            payload.submitted_integer is not None
            and answer_key.integer_value is not None
        ):
            is_correct = payload.submitted_integer == answer_key.integer_value

    score = 1.0 if is_correct else 0.0

    # 2. Record Attempt
    attempt = QuestionAttempt(
        session_id=session.id if session else None,
        user_id=current_user.id,
        question_id=question.id,
        selected_options=payload.selected_options,
        submitted_numerical=payload.submitted_numerical,
        submitted_integer=payload.submitted_integer,
        is_correct=is_correct,
        time_spent_seconds=payload.time_spent_seconds,
    )
    db.add(attempt)

    # 3. Update Session Progress if attached
    if session:
        if is_correct:
            session.correct_count += 1

        # Count total attempts in session
        count_stmt = select(func.count(QuestionAttempt.id)).where(
            QuestionAttempt.session_id == session.id
        )
        count_res = await db.execute(count_stmt)
        attempt_count = (count_res.scalar() or 0) + 1  # include current attempt

        if attempt_count >= session.total_questions:
            session.is_completed = True
            session.completed_at = datetime.now(timezone.utc)
            # Trigger review item creation for spaced repetition tracking if qualifying
            await trigger_review_item_on_practice_complete(
                current_user.id,
                session.topic_id,
                session.correct_count,
                session.total_questions,
                db,
            )

    await db.commit()

    return QuestionEvaluationResponse(
        question_id=question.id,
        is_correct=is_correct,
        score=score,
        correct_options=answer_key.correct_options,
        correct_numerical=answer_key.numerical_value,
        numerical_tolerance=answer_key.numerical_tolerance,
        correct_integer=answer_key.integer_value,
        explanation_latex=answer_key.explanation_latex,
        time_spent_seconds=payload.time_spent_seconds,
    )


@router.post(
    "/questions/{question_id}/report-errata",
    response_model=ErrataResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report Errata or Issue on a Question",
)
async def report_question_errata(
    question_id: uuid.UUID,
    payload: CreateErrataRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ErrataResponse:
    """Submit an errata report for pedagogical review according to Content Quality SLA."""
    question = await db.get(Question, question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    errata = QuestionErrataReport(
        question_id=question.id,
        user_id=current_user.id,
        issue_type=payload.issue_type,
        description=payload.description,
        status="OPEN",
    )
    db.add(errata)
    await db.commit()
    await db.refresh(errata)

    return ErrataResponse(
        id=errata.id,
        question_id=errata.question_id,
        issue_type=errata.issue_type,
        description=errata.description,
        status=errata.status,
        created_at=errata.created_at,
    )


@router.get(
    "/history",
    response_model=List[PracticeSessionSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Recent Practice History for Current Student",
)
async def get_practice_history(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[PracticeSessionSummaryResponse]:
    """Retrieve history of completed and in-progress practice sessions."""
    stmt = (
        select(PracticeSession)
        .where(PracticeSession.user_id == current_user.id)
        .order_by(PracticeSession.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    sessions = res.scalars().all()

    summaries = []
    for s in sessions:
        acc = (s.correct_count / s.total_questions * 100.0) if s.total_questions > 0 else 0.0
        summaries.append(
            PracticeSessionSummaryResponse(
                id=s.id,
                topic_id=s.topic_id,
                total_questions=s.total_questions,
                correct_count=s.correct_count,
                accuracy_percentage=round(acc, 1),
                is_completed=s.is_completed,
                started_at=s.created_at,
                completed_at=s.completed_at,
            )
        )
    return summaries
