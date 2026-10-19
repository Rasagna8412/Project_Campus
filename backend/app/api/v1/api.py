"""API v1 Router Aggregator."""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    analytics,
    analytics_trends,
    auth,
    curricula,
    health,
    planner,
    practice,
    progress,
    review,
    student,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(curricula.router, prefix="/curricula", tags=["Curricula"])
api_router.include_router(student.router, prefix="/student", tags=["Student"])
api_router.include_router(progress.router, prefix="/student/progress", tags=["Student Lesson Progress"])
api_router.include_router(analytics.router, prefix="/student/analytics", tags=["Student Learning Analytics"])
api_router.include_router(analytics_trends.router, prefix="/student/analytics", tags=["Student Analytics Trends & Diagnostics"])
api_router.include_router(practice.router, prefix="/practice", tags=["Practice & Assessment"])
api_router.include_router(planner.router, prefix="/planner", tags=["Study Planner & Learning Roadmap"])
api_router.include_router(review.router, prefix="/review", tags=["Spaced Repetition & Revision Queue"])
