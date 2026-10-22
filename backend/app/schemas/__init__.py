"""Pydantic Request and Response Schemas."""

from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.schemas.curriculum import (
    BoardCurriculumResponse,
    GradeStageResponse,
    SubjectResponse,
)
from app.schemas.health import HealthResponse
from app.schemas.student import (
    EnrolledSubjectResponse,
    StudentOnboardingRequest,
    StudentProfileResponse,
    StudentProfileUpdateRequest,
)
from app.schemas.ai import (
    AITutorChatRequest,
    AITutorChatResponse,
    AITutorQuizQuestion,
    SubscriptionEntitlementResponse,
    TierUpgradeRequest,
)

__all__ = [
    "HealthResponse",
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "TokenResponse",
    "BoardCurriculumResponse",
    "GradeStageResponse",
    "SubjectResponse",
    "EnrolledSubjectResponse",
    "StudentOnboardingRequest",
    "StudentProfileResponse",
    "StudentProfileUpdateRequest",
    "AITutorChatRequest",
    "AITutorChatResponse",
    "AITutorQuizQuestion",
    "SubscriptionEntitlementResponse",
    "TierUpgradeRequest",
]
