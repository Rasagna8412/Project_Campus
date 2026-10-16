"""Student Learning Analytics, Diagnostic Breakdown, and Recommendations Endpoints."""

from datetime import datetime
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_role
from app.core.database import get_db
from app.models.assessment import PracticeSession, Question, QuestionAttempt
from app.models.content import ContentStatus, Lesson, LessonProgress, LessonProgressStatus
from app.models.identity import StudentProfile, StudentProfileSubject, User
from app.models.taxonomy import Chapter, Subject, Topic
from app.schemas.analytics import (
    ActivityItem,
    DashboardAnalyticsResponse,
    LearningRecommendationResponse,
    TopicPerformanceResponse,
)

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=DashboardAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Student Dashboard Progress & Learning Analytics Summary",
)
async def get_dashboard_analytics(
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> DashboardAnalyticsResponse:
    """Dynamically aggregate student progress KPIs and recent activity.

    Strictly isolated to current_user.id. Handles empty state with null accuracy.
    """
    # 1. Lesson Progress Counts
    comp_lessons_stmt = select(func.count(LessonProgress.id)).where(
        LessonProgress.user_id == current_user.id,
        LessonProgress.status == LessonProgressStatus.COMPLETED.value,
    )
    lessons_completed_count = (await db.execute(comp_lessons_stmt)).scalar() or 0

    in_prog_stmt = select(func.count(LessonProgress.id)).where(
        LessonProgress.user_id == current_user.id,
        LessonProgress.status == LessonProgressStatus.IN_PROGRESS.value,
    )
    lessons_in_progress_count = (await db.execute(in_prog_stmt)).scalar() or 0

    # 2. Practice Session Counts
    comp_sess_stmt = select(func.count(PracticeSession.id)).where(
        PracticeSession.user_id == current_user.id,
        PracticeSession.is_completed == True,
    )
    practice_sessions_completed_count = (await db.execute(comp_sess_stmt)).scalar() or 0

    # 3. Question Attempt Counts
    tot_q_stmt = select(func.count(QuestionAttempt.id)).where(
        QuestionAttempt.user_id == current_user.id,
    )
    total_questions_answered = (await db.execute(tot_q_stmt)).scalar() or 0

    corr_q_stmt = select(func.count(QuestionAttempt.id)).where(
        QuestionAttempt.user_id == current_user.id,
        QuestionAttempt.is_correct == True,
    )
    total_correct_answers = (await db.execute(corr_q_stmt)).scalar() or 0

    # 4. Observed Practice Accuracy (null if 0 attempts)
    overall_accuracy_percentage = None
    if total_questions_answered > 0:
        overall_accuracy_percentage = round(
            (total_correct_answers / total_questions_answered) * 100.0, 1
        )

    # 5. Estimated Practice Time (sum valid durations between 0 and 1800s)
    time_stmt = select(func.sum(QuestionAttempt.time_spent_seconds)).where(
        QuestionAttempt.user_id == current_user.id,
        QuestionAttempt.time_spent_seconds >= 0,
        QuestionAttempt.time_spent_seconds <= 1800,
    )
    total_practice_time_seconds = (await db.execute(time_stmt)).scalar() or 0

    # 6. Daily Study Goal from Profile
    prof_stmt = select(StudentProfile.daily_study_goal_minutes).where(
        StudentProfile.user_id == current_user.id
    )
    daily_goal = (await db.execute(prof_stmt)).scalar() or 120

    # 7. Recent Learning Activity (Unified Practice Sessions and Completed Lessons)
    recent_activity: List[ActivityItem] = []

    # Recent practice sessions (up to 4)
    sess_stmt = (
        select(PracticeSession)
        .where(PracticeSession.user_id == current_user.id)
        .options(
            selectinload(PracticeSession.topic)
            .selectinload(Topic.chapter)
            .selectinload(Chapter.subject)
        )
        .order_by(PracticeSession.created_at.desc())
        .limit(4)
    )
    sess_rows = (await db.execute(sess_stmt)).scalars().all()
    for s in sess_rows:
        topic_title = s.topic.title if s.topic else "Practice Drill"
        subj_name = (
            s.topic.chapter.subject.name
            if s.topic and s.topic.chapter and s.topic.chapter.subject
            else None
        )
        acc_pct = (
            round((s.correct_count / s.total_questions) * 100)
            if s.total_questions > 0
            else 0
        )
        recent_activity.append(
            ActivityItem(
                activity_type="PRACTICE_SESSION",
                id=s.id,
                title=f"{topic_title} Practice",
                subject_name=subj_name,
                subtitle=f"{s.total_questions} questions • {s.correct_count} correct ({acc_pct}%)",
                timestamp=s.completed_at or s.created_at,
                is_completed=s.is_completed,
            )
        )

    # Recent completed lessons (up to 4)
    prog_stmt = (
        select(LessonProgress)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .where(
            LessonProgress.user_id == current_user.id,
            LessonProgress.status == LessonProgressStatus.COMPLETED.value,
            Lesson.status == ContentStatus.PUBLISHED.value,
        )
        .options(
            selectinload(LessonProgress.lesson)
            .selectinload(Lesson.topic)
            .selectinload(Topic.chapter)
            .selectinload(Chapter.subject)
        )
        .order_by(LessonProgress.completed_at.desc())
        .limit(4)
    )
    prog_rows = (await db.execute(prog_stmt)).scalars().all()
    for p in prog_rows:
        if p.lesson:
            subj_name = (
                p.lesson.topic.chapter.subject.name
                if p.lesson.topic and p.lesson.topic.chapter and p.lesson.topic.chapter.subject
                else None
            )
            recent_activity.append(
                ActivityItem(
                    activity_type="LESSON_COMPLETED",
                    id=p.lesson.id,
                    title=p.lesson.title,
                    subject_name=subj_name,
                    subtitle=f"Completed {p.lesson.estimated_read_time_minutes} min lesson",
                    timestamp=p.completed_at or p.last_accessed_at,
                    is_completed=True,
                )
            )

    # Sort unified activity descending by timestamp and take top 6
    recent_activity.sort(key=lambda item: item.timestamp, reverse=True)
    recent_activity = recent_activity[:6]

    return DashboardAnalyticsResponse(
        lessons_completed_count=lessons_completed_count,
        lessons_in_progress_count=lessons_in_progress_count,
        practice_sessions_completed_count=practice_sessions_completed_count,
        total_questions_answered=total_questions_answered,
        total_correct_answers=total_correct_answers,
        overall_accuracy_percentage=overall_accuracy_percentage,
        total_practice_time_seconds=total_practice_time_seconds,
        daily_study_goal_minutes=daily_goal,
        recent_activity=recent_activity,
    )


@router.get(
    "/topics",
    response_model=List[TopicPerformanceResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Topic-by-Topic Practice Performance Breakdown",
)
async def get_topic_analytics(
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> List[TopicPerformanceResponse]:
    """Aggregate topic-level practice performance for the authenticated student.

    Categories:
    - INSUFFICIENT_DATA: < 5 attempts
    - NEEDS_REVIEW: >= 5 attempts and accuracy < 60.0%
    - DEVELOPING: >= 5 attempts and 60.0% <= accuracy < 80.0%
    - STRONG: >= 5 attempts and accuracy >= 80.0%
    """
    # Group QuestionAttempt joined with Question by Question.topic_id
    agg_stmt = (
        select(
            Question.topic_id,
            func.count(QuestionAttempt.id).label("total_attempts"),
            func.sum(
                case((QuestionAttempt.is_correct == True, 1), else_=0)
            ).label("correct_attempts"),
            func.max(QuestionAttempt.attempted_at).label("last_practiced_at"),
        )
        .join(Question, QuestionAttempt.question_id == Question.id)
        .where(QuestionAttempt.user_id == current_user.id)
        .group_by(Question.topic_id)
    )
    agg_rows = (await db.execute(agg_stmt)).all()

    topic_summaries: List[TopicPerformanceResponse] = []

    for row in agg_rows:
        topic_id = row.topic_id
        total_attempts = row.total_attempts or 0
        correct_attempts = row.correct_attempts or 0
        incorrect_attempts = total_attempts - correct_attempts
        last_practiced_at = row.last_practiced_at

        # Fetch Topic metadata
        topic = (
            await db.execute(
                select(Topic)
                .where(Topic.id == topic_id)
                .options(selectinload(Topic.chapter).selectinload(Chapter.subject))
            )
        ).scalar_one_or_none()

        if not topic:
            continue

        # Completed practice sessions for this topic
        sess_count_stmt = select(func.count(PracticeSession.id)).where(
            PracticeSession.user_id == current_user.id,
            PracticeSession.topic_id == topic_id,
            PracticeSession.is_completed == True,
        )
        completed_sessions = (await db.execute(sess_count_stmt)).scalar() or 0

        # Calculate accuracy and category
        observed_accuracy = None
        if total_attempts > 0:
            observed_accuracy = round(
                (correct_attempts / total_attempts) * 100.0, 1
            )

        if total_attempts < 5:
            category = "INSUFFICIENT_DATA"
        elif observed_accuracy is not None and observed_accuracy < 60.0:
            category = "NEEDS_REVIEW"
        elif observed_accuracy is not None and observed_accuracy < 80.0:
            category = "DEVELOPING"
        else:
            category = "STRONG"

        chapter_title = topic.chapter.title if topic.chapter else "Chapter"
        subject_name = (
            topic.chapter.subject.name
            if topic.chapter and topic.chapter.subject
            else "Subject"
        )

        topic_summaries.append(
            TopicPerformanceResponse(
                topic_id=topic.id,
                topic_title=topic.title,
                topic_number=topic.topic_number,
                chapter_title=chapter_title,
                subject_name=subject_name,
                total_attempts=total_attempts,
                correct_attempts=correct_attempts,
                incorrect_attempts=incorrect_attempts,
                observed_accuracy_percentage=observed_accuracy,
                completed_sessions_count=completed_sessions,
                last_practiced_at=last_practiced_at,
                status_category=category,
            )
        )

    # Sort: topics with recent practice first, then by topic_number
    topic_summaries.sort(
        key=lambda t: (t.last_practiced_at is not None, t.last_practiced_at),
        reverse=True,
    )

    return topic_summaries


@router.get(
    "/recommendations",
    response_model=List[LearningRecommendationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Rule-Based Next-Step Learning Recommendations",
)
async def get_learning_recommendations(
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> List[LearningRecommendationResponse]:
    """Generate explainable next-step learning suggestions based on actual progress.

    Priorities:
    1. Resume In-Progress Lesson
    2. Revisit Struggling Topic (NEEDS_REVIEW: >= 5 attempts, accuracy < 60%)
    3. Practice Low-Confidence Topic (1 to 4 attempts)
    4. Start Next Unstarted Published Lesson in Enrolled Subjects
    """
    recommendations: List[LearningRecommendationResponse] = []

    # Priority 1: Check for an IN_PROGRESS lesson (most recently accessed)
    in_prog_stmt = (
        select(LessonProgress)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .where(
            LessonProgress.user_id == current_user.id,
            LessonProgress.status == LessonProgressStatus.IN_PROGRESS.value,
            Lesson.status == ContentStatus.PUBLISHED.value,
        )
        .options(
            selectinload(LessonProgress.lesson)
            .selectinload(Lesson.topic)
            .selectinload(Topic.chapter)
            .selectinload(Chapter.subject)
        )
        .order_by(LessonProgress.last_accessed_at.desc())
        .limit(1)
    )
    in_prog_res = (await db.execute(in_prog_stmt)).scalar_one_or_none()

    if in_prog_res and in_prog_res.lesson:
        subj_name = (
            in_prog_res.lesson.topic.chapter.subject.name
            if in_prog_res.lesson.topic
            and in_prog_res.lesson.topic.chapter
            and in_prog_res.lesson.topic.chapter.subject
            else None
        )
        recommendations.append(
            LearningRecommendationResponse(
                type="RESUME_LESSON",
                priority=1,
                title="Continue Reading Lesson",
                reason="You opened this lesson recently. Complete it to finish the concept foundation.",
                target_id=in_prog_res.lesson.id,
                target_title=in_prog_res.lesson.title,
                subject_name=subj_name,
                action_label="Resume Lesson",
            )
        )

    # Priority 2 & 3: Evaluate topic practice analytics for struggling & low-confidence topics
    topic_analytics = await get_topic_analytics(current_user=current_user, db=db)

    # Find struggling topics (NEEDS_REVIEW)
    struggling_topics = [
        t for t in topic_analytics if t.status_category == "NEEDS_REVIEW"
    ]
    struggling_topics.sort(
        key=lambda t: t.observed_accuracy_percentage or 0.0
    )

    if struggling_topics:
        worst_topic = struggling_topics[0]
        recommendations.append(
            LearningRecommendationResponse(
                type="REVISE_TOPIC",
                priority=2,
                title="Targeted Revision Suggested",
                reason=(
                    f"Observed accuracy is {worst_topic.observed_accuracy_percentage}% across "
                    f"{worst_topic.total_attempts} practice questions. Consider practising again to reinforce this topic."
                ),
                target_id=worst_topic.topic_id,
                target_title=worst_topic.topic_title,
                subject_name=worst_topic.subject_name,
                action_label="Practise Topic",
            )
        )

    # Priority 3: Low-confidence topic (1 to 4 attempts)
    low_confidence_topics = [
        t for t in topic_analytics if t.status_category == "INSUFFICIENT_DATA" and t.total_attempts > 0
    ]
    if low_confidence_topics and len(recommendations) < 3:
        target_topic = low_confidence_topics[0]
        recommendations.append(
            LearningRecommendationResponse(
                type="PRACTICE_TOPIC",
                priority=3,
                title="Complete Practice Drill",
                reason=(
                    f"You have answered {target_topic.total_attempts} questions in this topic. "
                    f"Complete a 5-question drill to establish a clear performance baseline."
                ),
                target_id=target_topic.topic_id,
                target_title=target_topic.topic_title,
                subject_name=target_topic.subject_name,
                action_label="Practise Questions",
            )
        )

    # Priority 4: Find next unstarted published lesson in enrolled subjects
    # First get student's enrolled subjects
    prof_stmt = (
        select(StudentProfile)
        .where(StudentProfile.user_id == current_user.id)
        .options(selectinload(StudentProfile.selected_subjects))
    )
    profile = (await db.execute(prof_stmt)).scalar_one_or_none()
    enrolled_subject_ids = (
        [sub.subject_id for sub in profile.selected_subjects]
        if profile and profile.selected_subjects
        else []
    )

    # Get set of all lesson IDs the student has already started or completed
    done_stmt = select(LessonProgress.lesson_id).where(
        LessonProgress.user_id == current_user.id
    )
    done_lesson_ids = set((await db.execute(done_stmt)).scalars().all())

    # Query next published lesson in enrolled subjects (or any published lesson if none enrolled)
    unstarted_lesson_query = (
        select(Lesson)
        .join(Topic, Lesson.topic_id == Topic.id)
        .join(Chapter, Topic.chapter_id == Chapter.id)
        .where(Lesson.status == ContentStatus.PUBLISHED.value)
        .options(
            selectinload(Lesson.topic)
            .selectinload(Topic.chapter)
            .selectinload(Chapter.subject)
        )
    )
    if enrolled_subject_ids:
        unstarted_lesson_query = unstarted_lesson_query.where(
            Chapter.subject_id.in_(enrolled_subject_ids)
        )

    unstarted_lesson_query = unstarted_lesson_query.order_by(
        Chapter.chapter_number.asc(),
        Topic.display_order.asc(),
        Lesson.display_order.asc(),
    )
    all_lessons = (await db.execute(unstarted_lesson_query)).scalars().all()

    for lsn in all_lessons:
        if lsn.id not in done_lesson_ids:
            subj_name = (
                lsn.topic.chapter.subject.name
                if lsn.topic and lsn.topic.chapter and lsn.topic.chapter.subject
                else None
            )
            recommendations.append(
                LearningRecommendationResponse(
                    type="NEXT_LESSON",
                    priority=4,
                    title="Start Next Lesson",
                    reason="Progress through your curriculum by starting the next structured lesson.",
                    target_id=lsn.id,
                    target_title=lsn.title,
                    subject_name=subj_name,
                    action_label="Start Lesson",
                )
            )
            break

    return recommendations[:4]
