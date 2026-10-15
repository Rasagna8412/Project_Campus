"""API v1 Router Aggregator."""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, curricula, health, practice, student

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(curricula.router, prefix="/curricula", tags=["Curricula"])
api_router.include_router(student.router, prefix="/student", tags=["Student"])
api_router.include_router(practice.router, prefix="/practice", tags=["Practice & Assessment"])
