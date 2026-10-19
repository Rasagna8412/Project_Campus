"""SuperMemo SM-2 Spaced Repetition Scheduling Algorithm.

Pure mathematical implementation of the SuperMemo SM-2 algorithm customized for
academic curricula, Indian Standard Time (IST) calendar dates, and platform mastery criteria.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import math
from typing import Optional

# Standard platform timezone: Indian Standard Time (IST: UTC+5:30)
PLANNER_TZ = timezone(timedelta(hours=5, minutes=30))

MIN_EASE_FACTOR = 1.30
INITIAL_EASE_FACTOR = 2.50
MAX_INTERVAL_DAYS = 180


def get_ist_date(now_dt: Optional[datetime] = None) -> date:
    """Return the current calendar date in Indian Standard Time (IST: UTC+5:30)."""
    if now_dt is None:
        now_dt = datetime.now(PLANNER_TZ)
    elif now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=PLANNER_TZ)
    else:
        now_dt = now_dt.astimezone(PLANNER_TZ)
    return now_dt.date()


@dataclass(frozen=True)
class SM2CalculationResult:
    """Immutable result of an SM-2 scheduling computation."""

    repetition_count: int
    ease_factor: float
    interval_days: int
    due_date: date
    status: str
    is_successful: bool


def determine_review_status(
    repetition_count: int, interval_days: int, ease_factor: float
) -> str:
    """Determine learning lifecycle status based on SM-2 metrics.

    Status criteria:
    - 'MASTERED': repetition_count >= 5 AND interval_days >= 21 AND ease_factor >= 2.50
    - 'REVIEW': repetition_count >= 2
    - 'LEARNING': repetition_count < 2
    """
    if repetition_count >= 5 and interval_days >= 21 and ease_factor >= 2.50:
        return "MASTERED"
    elif repetition_count >= 2:
        return "REVIEW"
    return "LEARNING"


def calculate_sm2(
    repetition_count: int,
    ease_factor: float,
    interval_days: int,
    quality_score: int,
    review_date: Optional[date] = None,
) -> SM2CalculationResult:
    """Calculate the next SM-2 interval, ease factor, repetition count, and due date.

    Args:
        repetition_count: Current number of consecutive successful reviews (n >= 0).
        ease_factor: Current Ease Factor (EF >= 1.30).
        interval_days: Current scheduled interval in days (I >= 0).
        quality_score: Student recall score between 0 and 5 inclusive.
            5 - Perfect recall (effortless)
            4 - Good recall (brief hesitation)
            3 - Passable recall (serious difficulty)
            2 - Incorrect (near miss)
            1 - Incorrect (familiar)
            0 - Complete blackout
        review_date: Calendar date of review (defaults to current date in IST).

    Returns:
        SM2CalculationResult containing the updated scheduling metrics.

    Raises:
        ValueError: If quality_score is not an integer in [0, 5], or inputs are out of valid bounds.
    """
    if not isinstance(quality_score, int) or isinstance(quality_score, bool):
        raise ValueError("Quality score must be an integer between 0 and 5.")
    if quality_score < 0 or quality_score > 5:
        raise ValueError("Quality score must be an integer between 0 and 5.")
    if repetition_count < 0:
        raise ValueError("Repetition count cannot be negative.")
    if interval_days < 0:
        raise ValueError("Interval days cannot be negative.")

    base_date = review_date if review_date is not None else get_ist_date()
    current_ef = max(MIN_EASE_FACTOR, float(ease_factor))
    is_successful = quality_score >= 3

    # Step 1: Update Ease Factor on every review:
    # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    diff = 5 - quality_score
    delta_ef = 0.1 - diff * (0.08 + diff * 0.02)
    new_ef = round(current_ef + delta_ef, 4)
    new_ef = max(MIN_EASE_FACTOR, new_ef)

    # Step 2: Update Repetition Count and Interval
    if is_successful:
        new_repetition = repetition_count + 1
        if new_repetition == 1:
            next_interval = 1
        elif new_repetition == 2:
            next_interval = 6
        else:
            # Deterministic rounding: floor(x + 0.5)
            computed_interval = math.floor((interval_days * new_ef) + 0.5)
            next_interval = min(MAX_INTERVAL_DAYS, max(1, computed_interval))
    else:
        new_repetition = 0
        next_interval = 1

    # Step 3: Determine Lifecycle Status
    status = determine_review_status(new_repetition, next_interval, new_ef)

    # Step 4: Calculate Target Due Date in IST
    due_date = base_date + timedelta(days=next_interval)

    return SM2CalculationResult(
        repetition_count=new_repetition,
        ease_factor=new_ef,
        interval_days=next_interval,
        due_date=due_date,
        status=status,
        is_successful=is_successful,
    )
