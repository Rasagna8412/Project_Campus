"""Student Profile Management, Onboarding, and Account Erasure Endpoints."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.identity import StudentProfile, StudentProfileSubject, User
from app.models.taxonomy import BoardCurriculum, GradeStage, Subject
from app.schemas.student import (
    EnrolledSubjectResponse,
    StudentOnboardingRequest,
    StudentProfileResponse,
    StudentProfileUpdateRequest,
)

router = APIRouter()


async def _format_profile_response(
    profile: StudentProfile, user: User, db: AsyncSession
) -> StudentProfileResponse:
    """Load relationships and format StudentProfileResponse."""
    # Eager load subjects
    query = (
        select(StudentProfileSubject)
        .where(StudentProfileSubject.profile_id == profile.id)
        .options(selectinload(StudentProfileSubject.subject))
    )
    res = await db.execute(query)
    enrolled_records = res.scalars().all()

    enrolled_subjects = [
        EnrolledSubjectResponse(
            id=rec.subject.id,
            code=rec.subject.code,
            name=rec.subject.name,
            display_order=rec.subject.display_order,
        )
        for rec in enrolled_records
        if rec.subject
    ]

    return StudentProfileResponse(
        id=profile.id,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        target_curriculum_id=profile.target_curriculum_id,
        target_curriculum_name=(
            profile.target_curriculum.name if profile.target_curriculum else None
        ),
        target_curriculum_code=(
            profile.target_curriculum.code if profile.target_curriculum else None
        ),
        grade_stage_id=profile.grade_stage_id,
        grade_stage_name=(
            profile.grade_stage.name if profile.grade_stage else None
        ),
        grade_stage_code=(
            profile.grade_stage.code if profile.grade_stage else None
        ),
        target_exam_year=profile.target_exam_year,
        daily_study_goal_minutes=profile.daily_study_goal_minutes,
        preferred_language=profile.preferred_language,
        onboarding_completed=profile.onboarding_completed,
        selected_subjects=enrolled_subjects,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get(
    "/profile",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated Student Profile",
)
async def get_student_profile(
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> StudentProfileResponse:
    """Retrieve the authenticated student's isolated profile."""
    # Fetch profile for current user
    stmt = (
        select(StudentProfile)
        .where(StudentProfile.user_id == current_user.id)
        .options(
            selectinload(StudentProfile.target_curriculum),
            selectinload(StudentProfile.grade_stage),
        )
    )
    profile = (await db.execute(stmt)).scalar_one_or_none()

    if not profile:
        profile = StudentProfile(
            user_id=current_user.id,
            onboarding_completed=False,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return await _format_profile_response(profile, current_user, db)


@router.put(
    "/onboarding",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Save or Complete Student Onboarding",
)
async def submit_student_onboarding(
    payload: StudentOnboardingRequest,
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> StudentProfileResponse:
    """Save curriculum selections, enrolled subjects, and study preferences."""
    # 1. Validate Target Curriculum
    curr_stmt = select(BoardCurriculum).where(
        BoardCurriculum.id == payload.target_curriculum_id,
        BoardCurriculum.is_active == True,
    )
    board = (await db.execute(curr_stmt)).scalar_one_or_none()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected curriculum board is invalid or inactive",
        )

    # 2. Validate Grade Stage belongs to selected Curriculum
    grade_stmt = select(GradeStage).where(
        GradeStage.id == payload.grade_stage_id,
        GradeStage.board_id == board.id,
    )
    grade = (await db.execute(grade_stmt)).scalar_one_or_none()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected grade level does not belong to the chosen curriculum",
        )

    # 3. Validate Subjects belong to selected Grade Stage
    sub_stmt = select(Subject).where(
        Subject.id.in_(payload.selected_subject_ids),
        Subject.grade_stage_id == grade.id,
    )
    found_subjects = (await db.execute(sub_stmt)).scalars().all()
    if len(found_subjects) != len(payload.selected_subject_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more selected subjects are invalid for the chosen grade level",
        )

    # 4. Fetch or create StudentProfile
    prof_stmt = (
        select(StudentProfile)
        .where(StudentProfile.user_id == current_user.id)
        .options(
            selectinload(StudentProfile.target_curriculum),
            selectinload(StudentProfile.grade_stage),
        )
    )
    profile = (await db.execute(prof_stmt)).scalar_one_or_none()
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.add(profile)
        await db.flush()

    # Update fields
    profile.target_curriculum_id = board.id
    profile.grade_stage_id = grade.id
    profile.target_exam_year = payload.target_exam_year
    profile.daily_study_goal_minutes = payload.daily_study_goal_minutes
    profile.preferred_language = payload.preferred_language
    profile.onboarding_completed = payload.complete

    # 5. Replace enrolled subjects atomically
    await db.execute(
        delete(StudentProfileSubject).where(
            StudentProfileSubject.profile_id == profile.id
        )
    )
    for subject in found_subjects:
        db.add(
            StudentProfileSubject(profile_id=profile.id, subject_id=subject.id)
        )

    await db.commit()
    await db.refresh(profile)

    return await _format_profile_response(profile, current_user, db)


@router.put(
    "/profile",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Student Profile Preferences",
)
async def update_student_profile(
    payload: StudentProfileUpdateRequest,
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> StudentProfileResponse:
    """Update study goals and language preferences."""
    stmt = select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    profile = (await db.execute(stmt)).scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    if payload.daily_study_goal_minutes is not None:
        profile.daily_study_goal_minutes = payload.daily_study_goal_minutes
    if payload.target_exam_year is not None:
        profile.target_exam_year = payload.target_exam_year
    if payload.preferred_language is not None:
        profile.preferred_language = payload.preferred_language

    await db.commit()
    await db.refresh(profile)

    return await _format_profile_response(profile, current_user, db)


@router.delete(
    "/account",
    status_code=status.HTTP_200_OK,
    summary="Delete Student Account (DPDP Act Compliance)",
)
async def delete_student_account(
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Permanently erase the authenticated student's account and profile."""
    # Cascading foreign keys will remove profile and user_roles
    await db.delete(current_user)
    await db.commit()
    return {
        "status": "success",
        "message": "Student account and all associated personal records permanently deleted.",
    }
