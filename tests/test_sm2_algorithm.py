"""Unit tests for the pure SuperMemo SM-2 algorithm implementation."""

from datetime import date, timedelta
import pytest

from app.core.sm2 import (
    calculate_sm2,
    determine_review_status,
    get_ist_date,
    MAX_INTERVAL_DAYS,
    MIN_EASE_FACTOR,
)


def test_get_ist_date():
    """Verify IST calendar date extraction."""
    today_ist = get_ist_date()
    assert isinstance(today_ist, date)


# ==============================================================================
# 1. SPECIFICATION TEST VECTORS (Section 4.4 of Milestone 7 Spec)
# ==============================================================================


def test_vector_1_initial_review_good():
    """Review 1: First exposure review with q=4 ('Good')."""
    base_date = date(2026, 10, 20)
    res = calculate_sm2(
        repetition_count=0,
        ease_factor=2.50,
        interval_days=0,
        quality_score=4,
        review_date=base_date,
    )
    assert res.repetition_count == 1
    assert res.ease_factor == 2.50  # delta = 0.1 - 1*(0.08 + 0.02) = 0.0
    assert res.interval_days == 1
    assert res.due_date == base_date + timedelta(days=1)
    assert res.status == "LEARNING"
    assert res.is_successful is True


def test_vector_2_second_review_easy():
    """Review 2: Second review with q=5 ('Easy')."""
    base_date = date(2026, 10, 21)
    res = calculate_sm2(
        repetition_count=1,
        ease_factor=2.50,
        interval_days=1,
        quality_score=5,
        review_date=base_date,
    )
    assert res.repetition_count == 2
    assert res.ease_factor == 2.60  # delta = +0.10
    assert res.interval_days == 6
    assert res.due_date == base_date + timedelta(days=6)
    assert res.status == "REVIEW"
    assert res.is_successful is True


def test_vector_3_third_review_good():
    """Review 3: Third review with q=4 ('Good')."""
    base_date = date(2026, 10, 27)
    res = calculate_sm2(
        repetition_count=2,
        ease_factor=2.60,
        interval_days=6,
        quality_score=4,
        review_date=base_date,
    )
    assert res.repetition_count == 3
    assert res.ease_factor == 2.60
    assert res.interval_days == 16  # round(6 * 2.60) = 15.6 -> 16
    assert res.due_date == base_date + timedelta(days=16)
    assert res.status == "REVIEW"
    assert res.is_successful is True


def test_vector_4_fourth_review_easy():
    """Review 4: Fourth review with q=5 ('Easy')."""
    base_date = date(2026, 11, 12)
    res = calculate_sm2(
        repetition_count=3,
        ease_factor=2.60,
        interval_days=16,
        quality_score=5,
        review_date=base_date,
    )
    assert res.repetition_count == 4
    assert res.ease_factor == 2.70
    assert res.interval_days == 43  # round(16 * 2.70) = 43.2 -> 43
    assert res.due_date == base_date + timedelta(days=43)
    assert res.status == "REVIEW"
    assert res.is_successful is True


def test_vector_5_fifth_review_enters_mastery():
    """Review 5: Fifth review entering MASTERED status."""
    base_date = date(2026, 12, 25)
    res = calculate_sm2(
        repetition_count=4,
        ease_factor=2.70,
        interval_days=43,
        quality_score=4,
        review_date=base_date,
    )
    assert res.repetition_count == 5
    assert res.ease_factor == 2.70
    assert res.interval_days == 116  # round(43 * 2.70) = 116.1 -> 116
    assert res.due_date == base_date + timedelta(days=116)
    assert res.status == "MASTERED"  # n >= 5, I >= 21, EF >= 2.50
    assert res.is_successful is True


def test_vector_6_lapse_from_mastery():
    """Review 6: Lapse from MASTERED with q=1 ('Wrong')."""
    base_date = date(2027, 4, 20)
    res = calculate_sm2(
        repetition_count=5,
        ease_factor=2.70,
        interval_days=116,
        quality_score=1,
        review_date=base_date,
    )
    # diff = 4, delta = 0.1 - 4 * (0.08 + 4*0.02) = 0.1 - 0.64 = -0.54
    assert res.repetition_count == 0
    assert res.ease_factor == 2.16  # 2.70 - 0.54
    assert res.interval_days == 1
    assert res.due_date == base_date + timedelta(days=1)
    assert res.status == "LEARNING"  # Reverts immediately to LEARNING
    assert res.is_successful is False


def test_vector_7_repeated_failures_clamped_to_min_ef():
    """Review 7: Multiple consecutive failures clamped to MIN_EASE_FACTOR = 1.30."""
    res = calculate_sm2(
        repetition_count=0,
        ease_factor=1.40,
        interval_days=1,
        quality_score=0,  # delta = 0.1 - 5 * (0.08 + 5*0.02) = 0.1 - 0.90 = -0.80
    )
    assert res.repetition_count == 0
    assert res.ease_factor == MIN_EASE_FACTOR  # clamped to 1.30
    assert res.interval_days == 1
    assert res.status == "LEARNING"
    assert res.is_successful is False


def test_vector_8_maximum_interval_capped_at_180():
    """Review 8: Interval reaching maximum cap of 180 days."""
    res = calculate_sm2(
        repetition_count=8,
        ease_factor=2.80,
        interval_days=150,
        quality_score=5,  # 150 * 2.90 = 435 -> clamped to 180
    )
    assert res.repetition_count == 9
    assert res.ease_factor == 2.90
    assert res.interval_days == MAX_INTERVAL_DAYS
    assert res.status == "MASTERED"
    assert res.is_successful is True


# ==============================================================================
# 2. MASTERY BOUNDARY TEST VECTORS (Technical Addendum Section 1.3)
# ==============================================================================


def test_mastery_boundary_tc_m1():
    """TC-M1: (4, 2.50, 16) with q=4 -> (5, 2.50, 40) enters MASTERED."""
    res = calculate_sm2(
        repetition_count=4,
        ease_factor=2.50,
        interval_days=16,
        quality_score=4,
    )
    assert res.repetition_count == 5
    assert res.ease_factor == 2.50
    assert res.interval_days == 40
    assert res.status == "MASTERED"


def test_mastery_boundary_tc_m2():
    """TC-M2: (5, 2.50, 40) with q=5 -> (6, 2.60, 104) remains MASTERED."""
    res = calculate_sm2(
        repetition_count=5,
        ease_factor=2.50,
        interval_days=40,
        quality_score=5,
    )
    assert res.repetition_count == 6
    assert res.ease_factor == 2.60
    assert res.interval_days == 104  # 40 * 2.60 = 104.0
    assert res.status == "MASTERED"


def test_mastery_boundary_tc_m3_ef_below_threshold():
    """TC-M3: (4, 2.30, 16) with q=4 -> (5, 2.30, 37) remains REVIEW because EF < 2.50."""
    res = calculate_sm2(
        repetition_count=4,
        ease_factor=2.30,
        interval_days=16,
        quality_score=4,
    )
    assert res.repetition_count == 5
    assert res.ease_factor == 2.30
    assert res.interval_days == 37  # round(16 * 2.30) = 36.8 -> 37
    assert res.status == "REVIEW"  # NOT Mastered because EF < 2.50


def test_mastery_boundary_tc_m4_lapse_from_mastery():
    """TC-M4: (6, 2.60, 104) with q=2 -> (0, 2.28, 1) reverts to LEARNING."""
    res = calculate_sm2(
        repetition_count=6,
        ease_factor=2.60,
        interval_days=104,
        quality_score=2,  # diff = 3, delta = 0.1 - 3 * (0.08 + 0.06) = 0.1 - 0.42 = -0.32
    )
    assert res.repetition_count == 0
    assert res.ease_factor == 2.28
    assert res.interval_days == 1
    assert res.status == "LEARNING"
    assert res.is_successful is False


def test_mastery_boundary_tc_m5_max_interval_clamp():
    """TC-M5: (8, 2.70, 150) with q=5 -> (9, 2.80, 180) clamped to 180 and MASTERED."""
    res = calculate_sm2(
        repetition_count=8,
        ease_factor=2.70,
        interval_days=150,
        quality_score=5,
    )
    assert res.repetition_count == 9
    assert res.ease_factor == 2.80
    assert res.interval_days == 180
    assert res.status == "MASTERED"


# ==============================================================================
# 3. INPUT VALIDATION AND ERROR HANDLING
# ==============================================================================


@pytest.mark.parametrize("invalid_q", [-1, 6, 10, -100, 2.5, "4", None, True, False])
def test_invalid_quality_score_raises_value_error(invalid_q):
    """Verify that any quality score not in {0, 1, 2, 3, 4, 5} raises ValueError."""
    with pytest.raises(ValueError):
        calculate_sm2(
            repetition_count=0,
            ease_factor=2.50,
            interval_days=0,
            quality_score=invalid_q,
        )


def test_negative_repetition_raises_value_error():
    with pytest.raises(ValueError):
        calculate_sm2(
            repetition_count=-1,
            ease_factor=2.50,
            interval_days=0,
            quality_score=4,
        )


def test_negative_interval_raises_value_error():
    with pytest.raises(ValueError):
        calculate_sm2(
            repetition_count=0,
            ease_factor=2.50,
            interval_days=-1,
            quality_score=4,
        )


def test_determine_review_status_edge_cases():
    """Verify explicit status determination logic."""
    assert determine_review_status(0, 0, 2.50) == "LEARNING"
    assert determine_review_status(1, 1, 2.50) == "LEARNING"
    assert determine_review_status(2, 6, 2.50) == "REVIEW"
    assert determine_review_status(4, 20, 2.80) == "REVIEW"
    # Fails repetition count condition
    assert determine_review_status(4, 25, 2.80) == "REVIEW"
    # Fails interval days condition
    assert determine_review_status(5, 20, 2.80) == "REVIEW"
    # Fails ease factor condition
    assert determine_review_status(5, 25, 2.49) == "REVIEW"
    # Meets all 3 conditions
    assert determine_review_status(5, 21, 2.50) == "MASTERED"
    assert determine_review_status(10, 180, 3.20) == "MASTERED"
