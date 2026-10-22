"""Study Planner, Daily Tasks, and Curriculum Roadmap API Endpoints."""

import asyncio
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_role
from app.api.v1.endpoints.analytics import get_topic_analytics
from app.core.database import get_db
from app.models.content import ContentStatus, Lesson, LessonProgress, LessonProgressStatus
from app.models.identity import StudentProfile, StudentProfileSubject, User
from app.models.planner import GoalStatus, StudyGoal, StudyTask, TaskStatus, TaskType
from app.models.repetition import ReviewItem
from app.models.taxonomy import Chapter, Subject, Topic
from app.schemas.planner import (
    ChapterRoadmapItem,
    CurriculumRoadmapResponse,
    DailyStudyPlanResponse,
    StudyGoalCreateRequest,
    StudyGoalResponse,
    StudyTaskResponse,
    SubjectRoadmapItem,
    TaskCompleteRequest,
    TaskRescheduleRequest,
)

router = APIRouter()

# Standard project timezone for India (IST: UTC+5:30)
PLANNER_TZ = timezone(timedelta(hours=5, minutes=30))


def get_planner_date(now_dt: Optional[datetime] = None) -> date:
    """Return the current calendar date in the platform's target timezone (IST)."""
    if now_dt is None:
        now_dt = datetime.now(PLANNER_TZ)
    elif now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=PLANNER_TZ)
    else:
        now_dt = now_dt.astimezone(PLANNER_TZ)
    return now_dt.date()


# In-process mutex per student and date to serialize concurrent daily plan generations
_task_gen_locks: Dict[Tuple[uuid.UUID, date], asyncio.Lock] = {}


async def _get_student_date_lock(user_id: uuid.UUID, target_date: date) -> asyncio.Lock:
    key = (user_id, target_date)
    if key not in _task_gen_locks:
        _task_gen_locks[key] = asyncio.Lock()
    return _task_gen_locks[key]


async def _acquire_user_lock(user_id: uuid.UUID, db: AsyncSession) -> None:
    """Acquire a row-level lock on the User record to serialize planner transactions across worker processes.

    In PostgreSQL, this holds an exclusive row lock on the user until the transaction commits or rolls back.
    In SQLite, row locks are no-ops and write transactions rely on SQLite database locking and unique constraints.
    """
    stmt = select(User.id).where(User.id == user_id).with_for_update()
    await db.execute(stmt)


async def _get_or_create_goal(
    user_id: uuid.UUID, db: AsyncSession, for_update: bool = False
) -> StudyGoal:
    """Retrieve the student's active goal or initialize a sensible default.

    When for_update=True, acquires a database row-level lock (PostgreSQL FOR UPDATE)
    to serialize concurrent daily plan operations across worker processes.
    """
    stmt = (
        select(StudyGoal)
        .where(
            StudyGoal.user_id == user_id,
            StudyGoal.status == GoalStatus.ACTIVE.value,
        )
        .order_by(StudyGoal.created_at.desc())
    )
    if for_update:
        stmt = stmt.with_for_update()
    goal = (await db.execute(stmt)).scalar_one_or_none()

    if not goal:
        # Check student profile for preferred daily study minutes
        prof_stmt = select(StudentProfile.daily_study_goal_minutes).where(
            StudentProfile.user_id == user_id
        )
        daily_mins = (await db.execute(prof_stmt)).scalar() or 120

        goal = StudyGoal(
            user_id=user_id,
            title="Academic Preparation",
            daily_study_minutes=daily_mins,
            preferred_days=["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
            status=GoalStatus.ACTIVE.value,
        )
        db.add(goal)
        await db.flush()
        await db.refresh(goal)

    return goal


async def _roll_forward_past_tasks(
    user_id: uuid.UUID, today: date, db: AsyncSession
) -> None:
    """Anti-snowball policy: mark past uncompleted pending or rescheduled tasks as SKIPPED.

    Preserves task history and prevents an overwhelming accumulation of overdue tasks.
    """
    stmt = select(StudyTask).where(
        StudyTask.user_id == user_id,
        StudyTask.scheduled_date < today,
        StudyTask.is_completed == False,
        StudyTask.status.in_([TaskStatus.PENDING.value, TaskStatus.RESCHEDULED.value]),
    )
    past_tasks = (await db.execute(stmt)).scalars().all()
    for t in past_tasks:
        t.status = TaskStatus.SKIPPED.value
    if past_tasks:
        await db.flush()


async def _generate_tasks_for_date(
    user_id: uuid.UUID,
    target_date: date,
    goal: StudyGoal,
    db: AsyncSession,
    existing_tasks: Optional[List[StudyTask]] = None,
) -> List[StudyTask]:
    """Deterministically synthesize up to 4 daily study tasks within the daily time budget.

    Guards against concurrency races, enforces the 4-task ceiling, caps resume-lesson tasks at 1,
    and isolates task generation strictly to the student's enrolled subjects.
    """
    # Re-query existing tasks inside the lock to ensure concurrency safety
    existing_stmt = (
        select(StudyTask)
        .where(
            StudyTask.user_id == user_id,
            StudyTask.scheduled_date == target_date,
        )
        .order_by(StudyTask.display_order.asc())
    )
    db_tasks = list((await db.execute(existing_stmt)).scalars().all())

    preserved_tasks: List[StudyTask] = (
        existing_tasks if existing_tasks is not None else db_tasks
    )

    target_budget = goal.daily_study_minutes
    accumulated_minutes = sum(t.estimated_minutes for t in preserved_tasks)
    max_total_tasks = 4

    # If already at 4 tasks or time budget exhausted, no new tasks needed
    if len(preserved_tasks) >= max_total_tasks or accumulated_minutes >= target_budget:
        return []

    generated_tasks: List[StudyTask] = []
    scheduled_lesson_ids: Set[uuid.UUID] = {
        t.lesson_id for t in preserved_tasks if t.lesson_id
    }
    scheduled_topic_ids: Set[uuid.UUID] = {
        t.topic_id for t in preserved_tasks if t.topic_id
    }

    # Track allocated display orders so every task receives a unique display_order between 1 and 4
    used_orders: Set[int] = {t.display_order for t in preserved_tasks}

    def get_next_display_order() -> int:
        for candidate in range(1, max_total_tasks + 1):
            if candidate not in used_orders:
                used_orders.add(candidate)
                return candidate
        next_order = (max(used_orders) if used_orders else 0) + 1
        used_orders.add(next_order)
        return next_order

    # Get student enrolled subjects
    prof_stmt = (
        select(StudentProfile)
        .where(StudentProfile.user_id == user_id)
        .options(selectinload(StudentProfile.selected_subjects))
    )
    profile = (await db.execute(prof_stmt)).scalar_one_or_none()
    enrolled_subject_ids = (
        [s.subject_id for s in profile.selected_subjects]
        if profile and profile.selected_subjects
        else []
    )

    def can_add_task(est: int) -> bool:
        current_count = len(preserved_tasks) + len(generated_tasks)
        if current_count >= max_total_tasks:
            return False
        if current_count == 0:
            return True
        return (accumulated_minutes + est) <= target_budget

    # Priority 1: Resume unfinished lessons (IN_PROGRESS) - MAX 1 per day (M-3)
    max_resume = 1
    resume_count = 0
    in_prog_stmt = (
        select(LessonProgress)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .where(
            LessonProgress.user_id == user_id,
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
    )
    in_prog_records = (await db.execute(in_prog_stmt)).scalars().all()

    for rec in in_prog_records:
        if resume_count >= max_resume:
            break
        lsn = rec.lesson
        if not lsn or lsn.id in scheduled_lesson_ids:
            continue
        est = lsn.estimated_read_time_minutes or 15
        if can_add_task(est):
            subj_id = (
                lsn.topic.chapter.subject_id
                if lsn.topic and lsn.topic.chapter
                else None
            )
            subj_name = (
                lsn.topic.chapter.subject.name
                if lsn.topic and lsn.topic.chapter and lsn.topic.chapter.subject
                else None
            )
            task = StudyTask(
                user_id=user_id,
                goal_id=goal.id,
                scheduled_date=target_date,
                task_type=TaskType.RESUME_LESSON.value,
                title=f"Resume: {lsn.title}",
                subject_id=subj_id,
                subject_name=subj_name,
                chapter_id=lsn.topic.chapter_id if lsn.topic else None,
                topic_id=lsn.topic_id,
                lesson_id=lsn.id,
                estimated_minutes=est,
                status=TaskStatus.PENDING.value,
                is_completed=False,
                display_order=get_next_display_order(),
                reason="You started this lesson recently. Finish it to complete the concept foundation.",
            )
            generated_tasks.append(task)
            scheduled_lesson_ids.add(lsn.id)
            if lsn.topic_id:
                scheduled_topic_ids.add(lsn.topic_id)
            accumulated_minutes += est
            resume_count += 1

    # Priority 2: Due Spaced Repetition Topic Review - MAX 1 per day
    max_review = 1
    review_count = 0
    if (
        (len(preserved_tasks) + len(generated_tasks)) < max_total_tasks
        and accumulated_minutes < target_budget
    ):
        review_stmt = (
            select(ReviewItem)
            .where(
                ReviewItem.user_id == user_id,
                ReviewItem.due_date <= target_date,
            )
            .options(
                selectinload(ReviewItem.topic)
                .selectinload(Topic.chapter)
                .selectinload(Chapter.subject)
            )
            .order_by(
                ReviewItem.due_date.asc(),
                ReviewItem.repetition_count.asc(),
            )
        )
        due_review_items = (await db.execute(review_stmt)).scalars().all()
        for rev_item in due_review_items:
            if review_count >= max_review:
                break
            if rev_item.topic_id in scheduled_topic_ids:
                continue
            if can_add_task(15):
                top = rev_item.topic
                subj_id = (
                    top.chapter.subject_id
                    if top and top.chapter
                    else rev_item.subject_id
                )
                subj_name = (
                    top.chapter.subject.name
                    if top and top.chapter and top.chapter.subject
                    else None
                )
                task = StudyTask(
                    user_id=user_id,
                    goal_id=goal.id,
                    scheduled_date=target_date,
                    task_type=TaskType.REVISE_TOPIC.value,
                    title=f"Spaced Review: {top.title if top else 'Topic Review'}",
                    subject_id=subj_id,
                    subject_name=subj_name,
                    chapter_id=top.chapter_id if top else None,
                    topic_id=rev_item.topic_id,
                    estimated_minutes=15,
                    status=TaskStatus.PENDING.value,
                    is_completed=False,
                    display_order=get_next_display_order(),
                    reason=(
                        f"Due for spaced repetition review (Interval: {rev_item.interval_days}d, "
                        f"Repetitions: {rev_item.repetition_count}). Reinforce recall to consolidate memory."
                    ),
                )
                generated_tasks.append(task)
                scheduled_topic_ids.add(rev_item.topic_id)
                accumulated_minutes += 15
                review_count += 1

    # Fetch topic analytics once for both Priority 3 and 4
    topic_analytics = []
    if (
        (len(preserved_tasks) + len(generated_tasks)) < max_total_tasks
        and accumulated_minutes < target_budget
    ):
        dummy_user = User(id=user_id, email="", full_name="", hashed_password="")
        topic_analytics = await get_topic_analytics(current_user=dummy_user, db=db)

    # Priority 3: Revise struggling topics (NEEDS_REVIEW: >= 5 attempts, accuracy < 60%)
    if (
        (len(preserved_tasks) + len(generated_tasks)) < max_total_tasks
        and accumulated_minutes < target_budget
    ):
        struggling_topics = [
            t for t in topic_analytics if t.status_category == "NEEDS_REVIEW"
        ]
        struggling_topics.sort(
            key=lambda t: t.observed_accuracy_percentage or 0.0
        )

        for top in struggling_topics:
            if not can_add_task(15):
                break
            if top.topic_id in scheduled_topic_ids:
                continue
            task = StudyTask(
                user_id=user_id,
                goal_id=goal.id,
                scheduled_date=target_date,
                task_type=TaskType.REVISE_TOPIC.value,
                title=f"Revise: {top.topic_title}",
                subject_name=top.subject_name,
                topic_id=top.topic_id,
                estimated_minutes=15,
                status=TaskStatus.PENDING.value,
                is_completed=False,
                display_order=get_next_display_order(),
                reason=(
                    f"Observed accuracy is {top.observed_accuracy_percentage}% across "
                    f"{top.total_attempts} questions. Dedicated revision practice is recommended."
                ),
            )
            generated_tasks.append(task)
            scheduled_topic_ids.add(top.topic_id)
            accumulated_minutes += 15

    # Priority 4: Low-confidence topic drill (<5 attempts, INSUFFICIENT_DATA)
    if (
        (len(preserved_tasks) + len(generated_tasks)) < max_total_tasks
        and accumulated_minutes < target_budget
    ):
        low_conf_topics = [
            t
            for t in topic_analytics
            if t.status_category == "INSUFFICIENT_DATA" and t.total_attempts > 0
        ]
        for top in low_conf_topics:
            if not can_add_task(15):
                break
            if top.topic_id in scheduled_topic_ids:
                continue
            task = StudyTask(
                user_id=user_id,
                goal_id=goal.id,
                scheduled_date=target_date,
                task_type=TaskType.PRACTICE_TOPIC.value,
                title=f"Practice: {top.topic_title}",
                subject_name=top.subject_name,
                topic_id=top.topic_id,
                estimated_minutes=15,
                status=TaskStatus.PENDING.value,
                is_completed=False,
                display_order=get_next_display_order(),
                reason=(
                    f"You have answered {top.total_attempts} questions in this topic. "
                    f"Complete a 5-question drill to establish a performance baseline."
                ),
            )
            generated_tasks.append(task)
            scheduled_topic_ids.add(top.topic_id)
            accumulated_minutes += 15

    # Priority 5: Next unstarted published lesson in syllabus sequence (H-3, L-1)
    # ONLY schedule if student has enrolled subjects to prevent leaking arbitrary global curricula
    if (
        enrolled_subject_ids
        and (len(preserved_tasks) + len(generated_tasks)) < max_total_tasks
        and accumulated_minutes < target_budget
    ):
        done_stmt = select(LessonProgress.lesson_id).where(
            LessonProgress.user_id == user_id
        )
        done_lesson_ids = set((await db.execute(done_stmt)).scalars().all())

        unstarted_query = (
            select(Lesson)
            .join(Topic, Lesson.topic_id == Topic.id)
            .join(Chapter, Topic.chapter_id == Chapter.id)
            .join(Subject, Chapter.subject_id == Subject.id)
            .where(
                Lesson.status == ContentStatus.PUBLISHED.value,
                Chapter.subject_id.in_(enrolled_subject_ids),
            )
            .options(
                selectinload(Lesson.topic)
                .selectinload(Topic.chapter)
                .selectinload(Chapter.subject)
            )
            .order_by(
                Subject.display_order.asc(),
                Chapter.chapter_number.asc(),
                Topic.display_order.asc(),
                Lesson.display_order.asc(),
            )
        )
        all_lessons = (await db.execute(unstarted_query)).scalars().all()

        for lsn in all_lessons:
            if len(preserved_tasks) + len(generated_tasks) >= max_total_tasks:
                break
            if lsn.id in done_lesson_ids or lsn.id in scheduled_lesson_ids:
                continue
            est = lsn.estimated_read_time_minutes or 15
            if can_add_task(est):
                subj_id = (
                    lsn.topic.chapter.subject_id
                    if lsn.topic and lsn.topic.chapter
                    else None
                )
                subj_name = (
                    lsn.topic.chapter.subject.name
                    if lsn.topic and lsn.topic.chapter and lsn.topic.chapter.subject
                    else None
                )
                task = StudyTask(
                    user_id=user_id,
                    goal_id=goal.id,
                    scheduled_date=target_date,
                    task_type=TaskType.STUDY_LESSON.value,
                    title=f"Study: {lsn.title}",
                    subject_id=subj_id,
                    subject_name=subj_name,
                    chapter_id=lsn.topic.chapter_id if lsn.topic else None,
                    topic_id=lsn.topic_id,
                    lesson_id=lsn.id,
                    estimated_minutes=est,
                    status=TaskStatus.PENDING.value,
                    is_completed=False,
                    display_order=get_next_display_order(),
                    reason=f"Next structured lesson in your enrolled {subj_name or 'curriculum'} syllabus sequence.",
                )
                generated_tasks.append(task)
                scheduled_lesson_ids.add(lsn.id)
                accumulated_minutes += est

    # Persist tasks
    for t in generated_tasks:
        db.add(t)
    if generated_tasks:
        await db.flush()

    return generated_tasks


# ==========================================
# Endpoints
# ==========================================


@router.get(
    "/goal",
    response_model=StudyGoalResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Active Study Goal",
)
async def get_study_goal(
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> StudyGoalResponse:
    """Retrieve the student's active study goal, creating a sensible default if none exists."""
    goal = await _get_or_create_goal(current_user.id, db)
    return StudyGoalResponse.model_validate(goal)


@router.post(
    "/goal",
    response_model=StudyGoalResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or Update Active Study Goal",
)
async def update_study_goal(
    payload: StudyGoalCreateRequest,
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> StudyGoalResponse:
    """Update or create the student's active study goal and synchronize daily minutes."""
    today = get_planner_date()
    if payload.target_date and payload.target_date < today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target exam date cannot be in the past.",
        )

    stmt = select(StudyGoal).where(
        StudyGoal.user_id == current_user.id,
        StudyGoal.status == GoalStatus.ACTIVE.value,
    )
    goal = (await db.execute(stmt)).scalar_one_or_none()

    if not goal:
        goal = StudyGoal(
            user_id=current_user.id,
            title=payload.title or "Academic Preparation",
            target_date=payload.target_date,
            daily_study_minutes=payload.daily_study_minutes,
            preferred_days=payload.preferred_days
            or ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
            status=GoalStatus.ACTIVE.value,
        )
        db.add(goal)
    else:
        if payload.title:
            goal.title = payload.title
        goal.target_date = payload.target_date
        goal.daily_study_minutes = payload.daily_study_minutes
        if payload.preferred_days is not None:
            goal.preferred_days = payload.preferred_days

    # Synchronize with StudentProfile daily_study_goal_minutes
    prof_stmt = select(StudentProfile).where(
        StudentProfile.user_id == current_user.id
    )
    profile = (await db.execute(prof_stmt)).scalar_one_or_none()
    if profile:
        profile.daily_study_goal_minutes = payload.daily_study_minutes

    await db.commit()
    await db.refresh(goal)
    return StudyGoalResponse.model_validate(goal)


@router.get(
    "/daily",
    response_model=DailyStudyPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Daily Study Plan for Date",
)
async def get_daily_study_plan(
    plan_date: Optional[date] = Query(
        default=None, description="Plan date (YYYY-MM-DD), defaults to today in platform timezone (IST)"
    ),
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> DailyStudyPlanResponse:
    """Retrieve daily scheduled study tasks.

    Automatically cleanses past overdue tasks and generates today's plan if empty and today is a preferred study day.
    """
    today = get_planner_date()
    target_date = plan_date or today

    # Cleanse overdue pending and rescheduled past tasks
    await _roll_forward_past_tasks(current_user.id, today, db)

    goal = await _get_or_create_goal(current_user.id, db)
    target_minutes = goal.daily_study_minutes
    preferred_days = goal.preferred_days or ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

    # Fetch existing tasks for target_date
    task_stmt = (
        select(StudyTask)
        .where(
            StudyTask.user_id == current_user.id,
            StudyTask.scheduled_date == target_date,
        )
        .order_by(StudyTask.display_order.asc())
    )
    tasks = list((await db.execute(task_stmt)).scalars().all())

    # If empty and viewing today, automatically synthesize only if today is an active preferred study day (M-1)
    if not tasks and target_date == today:
        lock = await _get_student_date_lock(current_user.id, target_date)
        async with lock:
            # Acquire row lock across worker processes before auto-generation
            await _acquire_user_lock(current_user.id, db)
            # Re-fetch tasks after acquiring locks to guard against concurrent generation race conditions
            tasks = list((await db.execute(task_stmt)).scalars().all())
            if not tasks:
                day_abbr = target_date.strftime("%a").upper()[:3]
                if day_abbr in preferred_days:
                    try:
                        await _generate_tasks_for_date(
                            current_user.id, target_date, goal, db
                        )
                        await db.commit()
                    except IntegrityError:
                        await db.rollback()
                    except Exception:
                        await db.rollback()
                        raise
                    tasks = list((await db.execute(task_stmt)).scalars().all())
                else:
                    await db.commit()
            else:
                await db.commit()
    else:
        # Commit any state changes (e.g. rolled-forward past tasks or newly initialized goal)
        await db.commit()

    planned_minutes = sum(t.estimated_minutes for t in tasks)
    completed_minutes = sum(
        t.estimated_minutes for t in tasks if t.is_completed
    )
    is_fully_completed = bool(tasks) and all(t.is_completed for t in tasks)

    return DailyStudyPlanResponse(
        date=target_date,
        target_minutes=target_minutes,
        planned_minutes=planned_minutes,
        completed_minutes=completed_minutes,
        is_fully_completed=is_fully_completed,
        tasks=[StudyTaskResponse.model_validate(t) for t in tasks],
    )


@router.post(
    "/daily/generate",
    response_model=DailyStudyPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Explicitly Regenerate Daily Study Plan",
)
async def generate_daily_study_plan(
    plan_date: Optional[date] = Query(default=None),
    force_refresh: bool = Query(default=False),
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> DailyStudyPlanResponse:
    """Regenerate study plan for date, optionally refreshing uncompleted tasks while preserving completed tasks (H-1)."""
    target_date = plan_date or get_planner_date()
    lock = await _get_student_date_lock(current_user.id, target_date)
    async with lock:
        # Step 1: Acquire row lock on User row across worker processes before reading or deleting
        await _acquire_user_lock(current_user.id, db)

        # Step 2: Retrieve or create study goal (also with row lock if exists)
        goal = await _get_or_create_goal(current_user.id, db, for_update=True)
        target_minutes = goal.daily_study_minutes

        # Step 3: Roll forward past overdue tasks
        today = get_planner_date()
        await _roll_forward_past_tasks(current_user.id, today, db)

        # Step 4: If force_refresh is requested, delete uncompleted tasks for this date WITHOUT committing
        if force_refresh:
            del_stmt = delete(StudyTask).where(
                StudyTask.user_id == current_user.id,
                StudyTask.scheduled_date == target_date,
                StudyTask.is_completed == False,
            )
            await db.execute(del_stmt)
            await db.flush()

        # Step 5: Read existing tasks (including preserved completed tasks)
        task_stmt = (
            select(StudyTask)
            .where(
                StudyTask.user_id == current_user.id,
                StudyTask.scheduled_date == target_date,
            )
            .order_by(StudyTask.display_order.asc())
        )
        existing_tasks = list((await db.execute(task_stmt)).scalars().all())

        # Step 6: Generate if force_refresh or no existing tasks, then single atomic commit
        if force_refresh or not existing_tasks:
            try:
                await _generate_tasks_for_date(
                    current_user.id, target_date, goal, db, existing_tasks=existing_tasks
                )
                await db.commit()
            except IntegrityError:
                await db.rollback()
            except Exception:
                await db.rollback()
                raise
        else:
            await db.commit()

        # Step 7: Always re-query persisted tasks directly from DB to eliminate any duplicate
        # entries and guarantee response consistency
        persisted_tasks = list((await db.execute(task_stmt)).scalars().all())

        planned_minutes = sum(t.estimated_minutes for t in persisted_tasks)
        completed_minutes = sum(
            t.estimated_minutes for t in persisted_tasks if t.is_completed
        )
        is_fully_completed = bool(persisted_tasks) and all(t.is_completed for t in persisted_tasks)

        return DailyStudyPlanResponse(
            date=target_date,
            target_minutes=target_minutes,
            planned_minutes=planned_minutes,
            completed_minutes=completed_minutes,
            is_fully_completed=is_fully_completed,
            tasks=[StudyTaskResponse.model_validate(t) for t in persisted_tasks],
        )


@router.patch(
    "/tasks/{task_id}/complete",
    response_model=StudyTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle Study Task Completion",
)
async def toggle_task_completion(
    task_id: uuid.UUID,
    payload: TaskCompleteRequest,
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> StudyTaskResponse:
    """Mark a study task as completed or pending. IDOR-protected by current_user.id."""
    stmt = select(StudyTask).where(
        StudyTask.id == task_id,
        StudyTask.user_id == current_user.id,
    )
    task = (await db.execute(stmt)).scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study task not found.",
        )

    task.is_completed = payload.is_completed
    today = get_planner_date()
    if payload.is_completed:
        task.status = TaskStatus.COMPLETED.value
        if not task.completed_at:
            task.completed_at = datetime.now(timezone.utc)
    else:
        task.completed_at = None
        # If in the past, unchecking it marks it SKIPPED according to non-punitive missed-day policy
        if task.scheduled_date < today:
            task.status = TaskStatus.SKIPPED.value
        else:
            task.status = TaskStatus.PENDING.value

    await db.commit()
    await db.refresh(task)
    return StudyTaskResponse.model_validate(task)


@router.patch(
    "/tasks/{task_id}/reschedule",
    response_model=StudyTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Reschedule Study Task to New Date",
)
async def reschedule_task(
    task_id: uuid.UUID,
    payload: TaskRescheduleRequest,
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> StudyTaskResponse:
    """Move an uncompleted task to a future date. Rejects past dates and completed tasks.

    Serialized across worker processes via row-level User locking and student-date mutex.
    """
    today = get_planner_date()
    if payload.new_date < today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rescheduled date cannot be in the past.",
        )

    lock = await _get_student_date_lock(current_user.id, payload.new_date)
    async with lock:
        await _acquire_user_lock(current_user.id, db)

        stmt = select(StudyTask).where(
            StudyTask.id == task_id,
            StudyTask.user_id == current_user.id,
        )
        task = (await db.execute(stmt)).scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study task not found.",
            )

        if task.is_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed study tasks cannot be rescheduled.",
            )

        # Enforce maximum 4 tasks per day ceiling on the target new_date
        count_stmt = select(func.count(StudyTask.id)).where(
            StudyTask.user_id == current_user.id,
            StudyTask.scheduled_date == payload.new_date,
            StudyTask.id != task_id,
        )
        target_count = (await db.execute(count_stmt)).scalar() or 0
        if target_count >= 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target date already has the maximum limit of 4 study tasks.",
            )

        # Calculate next available display_order between 1 and 4 on target date
        orders_stmt = select(StudyTask.display_order).where(
            StudyTask.user_id == current_user.id,
            StudyTask.scheduled_date == payload.new_date,
            StudyTask.id != task_id,
        )
        existing_orders = set((await db.execute(orders_stmt)).scalars().all())
        assigned_order = None
        for candidate in range(1, 5):
            if candidate not in existing_orders:
                assigned_order = candidate
                break
        if assigned_order is None:
            assigned_order = max(existing_orders, default=0) + 1

        task.display_order = assigned_order
        task.scheduled_date = payload.new_date
        task.status = TaskStatus.RESCHEDULED.value

        try:
            await db.commit()
            await db.refresh(task)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A concurrent update affected this schedule. Please retry.",
            )

        return StudyTaskResponse.model_validate(task)


@router.get(
    "/roadmap",
    response_model=CurriculumRoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Curriculum Progress Roadmap Across Enrolled Subjects",
)
async def get_curriculum_roadmap(
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> CurriculumRoadmapResponse:
    """Calculate macro syllabus completion across subjects and chapters (H-3: strictly isolated to enrolled subjects)."""
    # Get enrolled subjects
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

    # If student has no selected subjects, return an isolated, well-defined empty roadmap (H-3)
    if not enrolled_subject_ids:
        return CurriculumRoadmapResponse(
            total_lessons_count=0,
            completed_lessons_count=0,
            overall_completion_percentage=0.0,
            subjects=[],
        )

    # Query only actively enrolled subjects
    subj_query = (
        select(Subject)
        .where(Subject.id.in_(enrolled_subject_ids))
        .order_by(Subject.display_order.asc())
    )
    subjects = (await db.execute(subj_query)).scalars().all()

    # Get student progress maps
    prog_stmt = select(LessonProgress).where(
        LessonProgress.user_id == current_user.id
    )
    prog_records = (await db.execute(prog_stmt)).scalars().all()
    completed_lesson_ids = {
        p.lesson_id
        for p in prog_records
        if p.status == LessonProgressStatus.COMPLETED.value
    }
    in_prog_lesson_ids = {
        p.lesson_id
        for p in prog_records
        if p.status == LessonProgressStatus.IN_PROGRESS.value
    }

    subject_items: List[SubjectRoadmapItem] = []
    total_curriculum_lessons = 0
    total_completed_lessons = 0

    for subj in subjects:
        # Load chapters, topics, published lessons for subject
        chap_stmt = (
            select(Chapter)
            .where(Chapter.subject_id == subj.id)
            .options(
                selectinload(Chapter.topics).selectinload(Topic.lessons)
            )
            .order_by(Chapter.chapter_number.asc())
        )
        chapters = (await db.execute(chap_stmt)).scalars().all()

        subj_total = 0
        subj_completed = 0
        subj_in_prog = 0
        chapter_items: List[ChapterRoadmapItem] = []

        for chap in chapters:
            chap_total = 0
            chap_completed = 0
            for top in chap.topics:
                for lsn in top.lessons:
                    if lsn.status == ContentStatus.PUBLISHED.value:
                        chap_total += 1
                        if lsn.id in completed_lesson_ids:
                            chap_completed += 1
                        elif lsn.id in in_prog_lesson_ids:
                            subj_in_prog += 1

            subj_total += chap_total
            subj_completed += chap_completed

            chapter_items.append(
                ChapterRoadmapItem(
                    chapter_id=chap.id,
                    chapter_number=chap.chapter_number,
                    title=chap.title,
                    total_lessons=chap_total,
                    completed_lessons=chap_completed,
                    is_completed=chap_total > 0 and chap_completed == chap_total,
                )
            )

        total_curriculum_lessons += subj_total
        total_completed_lessons += subj_completed
        pct = (
            round((subj_completed / subj_total) * 100.0, 1)
            if subj_total > 0
            else 0.0
        )

        subject_items.append(
            SubjectRoadmapItem(
                subject_id=subj.id,
                subject_name=subj.name,
                total_lessons=subj_total,
                completed_lessons=subj_completed,
                in_progress_lessons=subj_in_prog,
                completion_percentage=pct,
                chapters=chapter_items,
            )
        )

    overall_pct = (
        round((total_completed_lessons / total_curriculum_lessons) * 100.0, 1)
        if total_curriculum_lessons > 0
        else 0.0
    )

    return CurriculumRoadmapResponse(
        total_lessons_count=total_curriculum_lessons,
        completed_lessons_count=total_completed_lessons,
        overall_completion_percentage=overall_pct,
        subjects=subject_items,
    )
