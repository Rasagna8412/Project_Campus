"""Campus AI Tutor and Subscription Entitlement Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.ai import AITutorInteraction, StudentSubscription
from app.models.identity import User
from app.schemas.ai import (
    AITutorChatRequest,
    AITutorChatResponse,
    SubscriptionEntitlementResponse,
    TierUpgradeRequest,
)
from app.services.ai_tutor import ai_tutor_service

router = APIRouter()


@router.post(
    "/chat",
    response_model=AITutorChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask Campus AI Tutor",
)
async def ask_ai_tutor(
    request: AITutorChatRequest,
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> AITutorChatResponse:
    """Submit an academic query to the Campus AI Tutor with lesson grounding and guardrails."""
    return await ai_tutor_service.execute_query(
        db=db,
        user_id=current_user.id,
        request=request,
    )


@router.get(
    "/entitlements",
    response_model=SubscriptionEntitlementResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Subscription Entitlements and AI Quota",
)
async def get_student_entitlements(
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionEntitlementResponse:
    """Retrieve current subscription tier, daily tutor quota, and usage."""
    return await ai_tutor_service.get_entitlements(
        db=db,
        user_id=current_user.id,
    )


@router.post(
    "/upgrade-preview",
    response_model=SubscriptionEntitlementResponse,
    status_code=status.HTTP_200_OK,
    summary="Preview or Toggle Subscription Tier (Dev/Demo Mode)",
)
async def upgrade_subscription_tier(
    payload: TierUpgradeRequest,
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionEntitlementResponse:
    """Switch subscription tier (e.g. FREE to PRO) in development/demo mode."""
    target = payload.target_tier.upper()
    if target not in ("FREE", "PRO"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid tiers are FREE or PRO",
        )

    sub = await ai_tutor_service.get_or_create_subscription(db, current_user.id)
    sub.tier = target
    if target == "PRO":
        sub.daily_tutor_quota = 500
    else:
        sub.daily_tutor_quota = 20

    await db.commit()
    await db.refresh(sub)

    return await ai_tutor_service.get_entitlements(db, current_user.id)


@router.get(
    "/history",
    status_code=status.HTTP_200_OK,
    summary="Get Recent AI Tutor Interactions",
)
async def get_tutor_history(
    limit: int = 10,
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """Fetch recent AI tutor interaction history for the current authenticated student."""
    stmt = (
        select(AITutorInteraction)
        .where(AITutorInteraction.user_id == current_user.id)
        .order_by(AITutorInteraction.created_at.desc())
        .limit(min(limit, 50))
    )
    res = await db.execute(stmt)
    records = res.scalars().all()

    return [
        {
            "id": str(r.id),
            "lesson_id": str(r.lesson_id) if r.lesson_id else None,
            "mode": r.mode,
            "user_query": r.user_query,
            "tutor_response": r.tutor_response,
            "grounding_sources": r.grounding_sources.split(", ") if r.grounding_sources else [],
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]
