"""Student Analytics Trends, Study Adherence, Retention Trends, and Diagnostic Matrix Endpoints."""

from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Set
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_role
from app.core.database import get_db
from app.core.sm2 import get_ist_date, PLANNER_TZ
from app.models.assessment import PracticeSession, Question, QuestionAttempt
from app.models.content import ContentStatus, Lesson, LessonProgress, LessonProgressStatus
from app.models.identity import StudentProfile, StudentProfileSubject, User
from app.models.planner import GoalStatus, StudyGoal, StudyTask, TaskStatus
from app.models.repetition import ReviewItem, ReviewLog, ReviewStatus
from app.models.taxonomy import Chapter, Subject, Topic
from app.schemas.analytics_trends import (
    DailyPlannerTrendItem,
    DailyPracticeTrendItem,
    DiagnosticMatrixResponse,
    DiagnosticTopicItem,
    PlannerTrendsResponse,
    PracticeTrendsResponse,
    RetentionForecastItem,
    RetentionTrendsResponse,
)

router = APIRouter()


@router.get(
    "/trends/practice",
    response_model=PracticeTrendsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Multi-Day Practice Volume and Accuracy Trends",
)
async def get_practice_trends(
    days: int = Query(default=7, ge=1, le=90, description="Window size in days (7 or 14)"),
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> PracticeTrendsResponse:
    """Retrieve consecutive daily practice question counts and observed accuracy in IST.

    Returns complete chronological date buckets with zero-fill and null accuracy for inactive days.
    """
    today_ist = get_ist_date()
    start_date_ist = today_ist - timedelta(days=days - 1)

    # Convert IST calendar window to UTC boundary datetimes for filtering
    start_dt_utc = datetime.combine(
        start_date_ist, datetime.min.time(), tzinfo=PLANNER_TZ
    ).astimezone(timezone.utc).replace(tzinfo=None)
    end_dt_utc = datetime.combine(
        today_ist, datetime.max.time(), tzinfo=PLANNER_TZ
    ).astimezone(timezone.utc).replace(tzinfo=None)

    # Fetch attempts strictly isolated to current_user within the window
    stmt = (
        select(QuestionAttempt)
        .where(
            QuestionAttempt.user_id == current_user.id,
            QuestionAttempt.attempted_at >= start_dt_utc,
            QuestionAttempt.attempted_at <= end_dt_utc,
        )
        .order_by(QuestionAttempt.attempted_at.asc())
    )
    attempts = list((await db.execute(stmt)).scalars().all())

    # Map attempts by IST calendar date
    attempts_by_date: Dict[date, List[QuestionAttempt]] = {}
    for att in attempts:
        att_dt = att.attempted_at
        if att_dt.tzinfo is None:
            att_dt = att_dt.replace(tzinfo=timezone.utc)
        att_ist_date = att_dt.astimezone(PLANNER_TZ).date()
        if start_date_ist <= att_ist_date <= today_ist:
            attempts_by_date.setdefault(att_ist_date, []).append(att)

    daily_trends: List[DailyPracticeTrendItem] = []
    total_q = 0
    total_corr = 0
    total_sec = 0

    cur_date = start_date_ist
    while cur_date <= today_ist:
        day_attempts = attempts_by_date.get(cur_date, [])
        q_count = len(day_attempts)
        c_count = sum(1 for a in day_attempts if a.is_correct)
        s_count = sum(a.time_spent_seconds for a in day_attempts if 0 <= a.time_spent_seconds <= 1800)

        acc_pct: Optional[float] = None
        if q_count > 0:
            acc_pct = round((c_count / q_count) * 100.0, 1)

        practice_mins = round(s_count / 60.0, 1)

        daily_trends.append(
            DailyPracticeTrendItem(
                date=cur_date.isoformat(),
                questions_answered=q_count,
                correct_count=c_count,
                accuracy_percentage=acc_pct,
                practice_minutes=practice_mins,
            )
        )

        total_q += q_count
        total_corr += c_count
        total_sec += s_count
        cur_date += timedelta(days=1)

    overall_acc: Optional[float] = None
    if total_q > 0:
        overall_acc = round((total_corr / total_q) * 100.0, 1)

    return PracticeTrendsResponse(
        days_count=days,
        start_date=start_date_ist.isoformat(),
        end_date=today_ist.isoformat(),
        total_questions_answered=total_q,
        total_correct_count=total_corr,
        overall_accuracy_percentage=overall_acc,
        total_practice_minutes=round(total_sec / 60.0, 1),
        daily_trends=daily_trends,
    )


@router.get(
    "/trends/planner",
    response_model=PlannerTrendsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Multi-Day Study Plan Adherence and Minute Budget Tracking",
)
async def get_planner_trends(
    days: int = Query(default=7, ge=1, le=90, description="Window size in days (7 or 14)"),
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> PlannerTrendsResponse:
    """Retrieve daily study plan adherence and minute budget comparisons in IST.

    Calculates non-punitive weekly goal adherence based on preferred study days.
    """
    today_ist = get_ist_date()
    start_date_ist = today_ist - timedelta(days=days - 1)

    # 1. Fetch active study goal or profile default
    goal_stmt = (
        select(StudyGoal)
        .where(
            StudyGoal.user_id == current_user.id,
            StudyGoal.status == GoalStatus.ACTIVE.value,
        )
        .order_by(StudyGoal.created_at.desc())
    )
    goal = (await db.execute(goal_stmt)).scalar_one_or_none()

    if goal:
        daily_goal_mins = goal.daily_study_minutes
        preferred_days = set(goal.preferred_days or [])
    else:
        prof_stmt = select(StudentProfile.daily_study_goal_minutes).where(
            StudentProfile.user_id == current_user.id
        )
        daily_goal_mins = (await db.execute(prof_stmt)).scalar() or 120
        preferred_days = {"MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"}

    # 2. Fetch scheduled study tasks within the window
    tasks_stmt = (
        select(StudyTask)
        .where(
            StudyTask.user_id == current_user.id,
            StudyTask.scheduled_date >= start_date_ist,
            StudyTask.scheduled_date <= today_ist,
        )
        .order_by(StudyTask.scheduled_date.asc(), StudyTask.display_order.asc())
    )
    tasks = list((await db.execute(tasks_stmt)).scalars().all())

    tasks_by_date: Dict[date, List[StudyTask]] = {}
    for t in tasks:
        tasks_by_date.setdefault(t.scheduled_date, []).append(t)

    daily_trends: List[DailyPlannerTrendItem] = []
    total_planned_m = 0
    total_completed_m = 0

    cur_date = start_date_ist
    while cur_date <= today_ist:
        day_name = cur_date.strftime("%a").upper()
        is_pref = day_name in preferred_days
        day_tasks = tasks_by_date.get(cur_date, [])
        has_plan = len(day_tasks) > 0

        p_mins = sum(t.estimated_minutes for t in day_tasks)
        c_mins = sum(t.estimated_minutes for t in day_tasks if t.is_completed)
        t_count = len(day_tasks)
        comp_count = sum(1 for t in day_tasks if t.is_completed)

        # Goal met logic:
        # If tasks were scheduled: all completed OR completed minutes >= planned minutes
        # Alternatively completed minutes >= daily target minutes
        is_met = False
        if has_plan:
            is_met = (comp_count > 0 and comp_count >= t_count) or (c_mins >= daily_goal_mins) or (p_mins > 0 and c_mins >= p_mins)

        daily_trends.append(
            DailyPlannerTrendItem(
                date=cur_date.isoformat(),
                day_of_week=day_name,
                is_preferred_day=is_pref,
                has_plan=has_plan,
                planned_minutes=p_mins,
                completed_minutes=c_mins,
                tasks_count=t_count,
                completed_tasks_count=comp_count,
                is_goal_met=is_met,
            )
        )

        total_planned_m += p_mins
        total_completed_m += c_mins
        cur_date += timedelta(days=1)

    preferred_days_count = sum(1 for d in daily_trends if d.is_preferred_day)
    goals_met_count = sum(1 for d in daily_trends if d.is_preferred_day and d.is_goal_met)

    adherence_pct: Optional[float] = None
    if preferred_days_count > 0:
        adherence_pct = round((goals_met_count / preferred_days_count) * 100.0, 1)

    return PlannerTrendsResponse(
        daily_study_goal_minutes=daily_goal_mins,
        days_count=days,
        preferred_days_count=preferred_days_count,
        goals_met_count=goals_met_count,
        adherence_rate_percentage=adherence_pct,
        total_planned_minutes=total_planned_m,
        total_completed_minutes=total_completed_m,
        daily_trends=daily_trends,
    )


@router.get(
    "/trends/retention",
    response_model=RetentionTrendsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Spaced Repetition Streaks, Overdue Aging, and 7-Day Forecast",
)
async def get_retention_trends(
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> RetentionTrendsResponse:
    """Retrieve active recall streak, overdue aging categories, and upcoming 7-day review forecast."""
    today_ist = get_ist_date()

    # 1. Streak calculation from ReviewLog entries
    log_stmt = (
        select(ReviewLog.reviewed_at)
        .where(ReviewLog.user_id == current_user.id)
        .order_by(ReviewLog.reviewed_at.desc())
    )
    logs = list((await db.execute(log_stmt)).scalars().all())

    review_dates: Set[date] = set()
    for reviewed_at in logs:
        if reviewed_at.tzinfo is None:
            reviewed_at = reviewed_at.replace(tzinfo=timezone.utc)
        review_dates.add(reviewed_at.astimezone(PLANNER_TZ).date())

    yesterday_ist = today_ist - timedelta(days=1)
    is_streak_active_today = today_ist in review_dates

    streak = 0
    if is_streak_active_today:
        streak = 1
        check_date = yesterday_ist
        while check_date in review_dates:
            streak += 1
            check_date -= timedelta(days=1)
    elif yesterday_ist in review_dates:
        # Active streak maintained from yesterday; can be continued today
        streak = 1
        check_date = yesterday_ist - timedelta(days=1)
        while check_date in review_dates:
            streak += 1
            check_date -= timedelta(days=1)

    last_rev_date_str = max(review_dates).isoformat() if review_dates else None

    # 2. Overdue & Due Today Breakdown from ReviewItem
    items_stmt = select(ReviewItem).where(
        ReviewItem.user_id == current_user.id,
        ReviewItem.status != ReviewStatus.MASTERED.value,
    )
    items = list((await db.execute(items_stmt)).scalars().all())

    due_today_count = 0
    overdue_1_to_3 = 0
    overdue_4_plus = 0

    for item in items:
        if item.due_date == today_ist:
            due_today_count += 1
        elif item.due_date < today_ist:
            days_overdue = (today_ist - item.due_date).days
            if 1 <= days_overdue <= 3:
                overdue_1_to_3 += 1
            else:
                overdue_4_plus += 1

    total_overdue = overdue_1_to_3 + overdue_4_plus

    # 3. 7-Day Forward Forecast (Tomorrow through T+7)
    forecast_counts: Dict[date, int] = {}
    for i in range(1, 8):
        f_date = today_ist + timedelta(days=i)
        forecast_counts[f_date] = 0

    forecast_stmt = select(ReviewItem.due_date).where(
        ReviewItem.user_id == current_user.id,
        ReviewItem.status != ReviewStatus.MASTERED.value,
        ReviewItem.due_date > today_ist,
        ReviewItem.due_date <= today_ist + timedelta(days=7),
    )
    f_dates = list((await db.execute(forecast_stmt)).scalars().all())
    for fd in f_dates:
        if fd in forecast_counts:
            forecast_counts[fd] += 1

    forecast_items: List[RetentionForecastItem] = []
    for i in range(1, 8):
        f_date = today_ist + timedelta(days=i)
        forecast_items.append(
            RetentionForecastItem(
                date=f_date.isoformat(),
                due_count=forecast_counts.get(f_date, 0),
            )
        )

    return RetentionTrendsResponse(
        active_streak_days=streak,
        last_reviewed_date=last_rev_date_str,
        is_streak_active_today=is_streak_active_today,
        due_today_count=due_today_count,
        overdue_1_to_3_days=overdue_1_to_3,
        overdue_4_plus_days=overdue_4_plus,
        total_overdue_count=total_overdue,
        forecast_next_7_days=forecast_items,
    )


@router.get(
    "/diagnostic-matrix",
    response_model=DiagnosticMatrixResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Multi-Dimensional Learning Gap Diagnostic Matrix",
)
async def get_diagnostic_matrix(
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> DiagnosticMatrixResponse:
    """Synthesizes lesson progress, practice calibration, and SM-2 recall status into actionable learning gap diagnoses."""
    today_ist = get_ist_date()

    # 1. Identify enrolled subjects
    prof_stmt = (
        select(StudentProfile)
        .where(StudentProfile.user_id == current_user.id)
        .options(selectinload(StudentProfile.selected_subjects))
    )
    profile = (await db.execute(prof_stmt)).scalar_one_or_none()
    enrolled_subject_ids = (
        [s.subject_id for s in profile.selected_subjects]
        if profile and profile.selected_subjects
        else []
    )

    # 2. Query published topics: prioritize enrolled subjects, fallback to all published topics if no selection
    topic_query = (
        select(Topic)
        .join(Chapter, Topic.chapter_id == Chapter.id)
        .join(Subject, Chapter.subject_id == Subject.id)
        .options(
            selectinload(Topic.chapter).selectinload(Chapter.subject),
            selectinload(Topic.lessons),
        )
    )
    if enrolled_subject_ids:
        topic_query = topic_query.where(Chapter.subject_id.in_(enrolled_subject_ids))

    topic_query = topic_query.order_by(
        Subject.display_order.asc(),
        Chapter.chapter_number.asc(),
        Topic.display_order.asc(),
    )
    topics = list((await db.execute(topic_query)).scalars().all())

    # Fallback: if no topics found under enrolled filter, load published topics with existing activity
    if not topics:
        fallback_query = (
            select(Topic)
            .join(Chapter, Topic.chapter_id == Chapter.id)
            .join(Subject, Chapter.subject_id == Subject.id)
            .options(
                selectinload(Topic.chapter).selectinload(Chapter.subject),
                selectinload(Topic.lessons),
            )
            .order_by(
                Subject.display_order.asc(),
                Chapter.chapter_number.asc(),
                Topic.display_order.asc(),
            )
        )
        topics = list((await db.execute(fallback_query)).scalars().all())

    # 3. Batch load student's lesson progress
    prog_stmt = select(LessonProgress).where(LessonProgress.user_id == current_user.id)
    progress_records = list((await db.execute(prog_stmt)).scalars().all())
    progress_by_lesson: Dict[uuid.UUID, LessonProgress] = {
        p.lesson_id: p for p in progress_records
    }

    # 4. Batch load question attempt aggregates per topic
    att_stmt = (
        select(
            Question.topic_id,
            func.count(QuestionAttempt.id).label("total_attempts"),
            func.sum(case((QuestionAttempt.is_correct == True, 1), else_=0)).label("correct_count"),
        )
        .join(Question, QuestionAttempt.question_id == Question.id)
        .where(QuestionAttempt.user_id == current_user.id)
        .group_by(Question.topic_id)
    )
    att_rows = (await db.execute(att_stmt)).all()
    attempts_by_topic: Dict[uuid.UUID, tuple] = {
        row.topic_id: (row.total_attempts or 0, row.correct_count or 0)
        for row in att_rows
    }

    # 5. Batch load spaced repetition review items
    rev_stmt = select(ReviewItem).where(ReviewItem.user_id == current_user.id)
    review_items = list((await db.execute(rev_stmt)).scalars().all())
    review_by_topic: Dict[uuid.UUID, ReviewItem] = {
        r.topic_id: r for r in review_items
    }

    diagnostic_items: List[DiagnosticTopicItem] = []
    critical_count = 0
    unpracticed_count = 0
    solidifying_count = 0
    mastered_count = 0

    for topic in topics:
        subj = topic.chapter.subject if topic.chapter else None
        subj_name = subj.name if subj else "General Studies"
        subj_id = subj.id if subj else uuid.uuid4()
        chap_title = topic.chapter.title if topic.chapter else "General Chapter"

        # Determine lesson completion status for the topic
        published_lessons = [
            l for l in topic.lessons if l.status == ContentStatus.PUBLISHED.value
        ]
        if not published_lessons:
            lesson_status = "NOT_STARTED"
        else:
            statuses = [
                progress_by_lesson[l.id].status
                for l in published_lessons
                if l.id in progress_by_lesson
            ]
            if not statuses:
                lesson_status = "NOT_STARTED"
            elif all(s == LessonProgressStatus.COMPLETED.value for s in statuses) and len(statuses) == len(published_lessons):
                lesson_status = "COMPLETED"
            elif any(s in (LessonProgressStatus.IN_PROGRESS.value, LessonProgressStatus.COMPLETED.value) for s in statuses):
                lesson_status = "IN_PROGRESS"
            else:
                lesson_status = "NOT_STARTED"

        # Determine practice attempts & accuracy
        total_att, corr_att = attempts_by_topic.get(topic.id, (0, 0))
        accuracy: Optional[float] = None
        if total_att > 0:
            accuracy = round((corr_att / total_att) * 100.0, 1)

        # Categorize practice calibration
        if total_att == 0:
            practice_cat = "UNPRACTICED"
        elif total_att < 5:
            practice_cat = "INSUFFICIENT_DATA"
        elif accuracy is not None and accuracy < 60.0:
            practice_cat = "NEEDS_REVIEW"
        elif accuracy is not None and accuracy < 80.0:
            practice_cat = "DEVELOPING"
        else:
            practice_cat = "STRONG"

        # Check Spaced Repetition status
        rev_item = review_by_topic.get(topic.id)
        rev_status = rev_item.status if rev_item else None
        rev_interval = rev_item.interval_days if rev_item else None
        is_overdue = (rev_item.due_date < today_ist) if rev_item else False

        # Diagnostic state hierarchy
        if (total_att >= 5 and accuracy is not None and accuracy < 60.0) or (rev_item and rev_item.status == ReviewStatus.LEARNING.value and is_overdue):
            diag_state = "CRITICAL_GAP"
            recommendation = "Urgent review required: re-study core lesson concepts and practice fundamental drill questions."
            critical_count += 1
        elif lesson_status in ("COMPLETED", "IN_PROGRESS") and total_att < 5:
            diag_state = "UNPRACTICED_FOUNDATION"
            recommendation = "Foundation studied: complete at least 5 practice questions to calibrate recall and accuracy."
            unpracticed_count += 1
        elif total_att >= 5 and accuracy is not None and accuracy >= 80.0 and rev_status == ReviewStatus.MASTERED.value:
            diag_state = "MASTERED"
            recommendation = "Topic fully mastered: retain high recall through maintenance reviews as scheduled."
            mastered_count += 1
        elif total_att >= 5 or rev_status is not None or lesson_status != "NOT_STARTED":
            diag_state = "SOLIDIFYING"
            recommendation = "Good progress: continue spaced repetition reviews and target challenging practice sets."
            solidifying_count += 1
        else:
            diag_state = "NOT_STARTED"
            recommendation = "Begin your learning journey by studying the introductory lesson."

        diagnostic_items.append(
            DiagnosticTopicItem(
                topic_id=topic.id,
                topic_title=topic.title,
                subject_id=subj_id,
                subject_name=subj_name,
                chapter_title=chap_title,
                lesson_status=lesson_status,
                total_attempts=total_att,
                observed_accuracy_percentage=accuracy,
                practice_category=practice_cat,
                review_status=rev_status,
                review_interval_days=rev_interval,
                is_review_overdue=is_overdue,
                diagnostic_state=diag_state,
                action_recommendation=recommendation,
            )
        )

    return DiagnosticMatrixResponse(
        total_topics_analyzed=len(diagnostic_items),
        critical_gaps_count=critical_count,
        unpracticed_foundations_count=unpracticed_count,
        solidifying_count=solidifying_count,
        mastered_count=mastered_count,
        topics=diagnostic_items,
    )
