"""Authentication Endpoints: Registration, Login, Logout, and Current User."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    auth_rate_limiter,
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.identity import Role, StudentProfile, User, UserRole
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _format_user_response(user: User) -> UserResponse:
    """Format SQLAlchemy User model into public UserResponse."""
    role_names = [ur.role.name for ur in user.user_roles if ur.role]
    onboarding_done = False
    if user.student_profile:
        onboarding_done = user.student_profile.onboarding_completed

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        roles=role_names,
        onboarding_completed=onboarding_done,
        created_at=user.created_at,
    )


def _set_auth_cookie(response: Response, token: str) -> None:
    """Set secure HttpOnly authentication cookie."""
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        secure=settings.AUTH_COOKIE_SECURE or settings.ENVIRONMENT == "production",
        path="/",
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Student Account Registration",
)
async def register_student(
    payload: UserRegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Register a new student account with validated email and password."""
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_id = f"reg:{client_ip}"

    if auth_rate_limiter.is_rate_limited(rate_limit_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please wait before trying again.",
        )
    auth_rate_limiter.record_attempt(rate_limit_id)

    # Check for existing normalized email
    stmt = select(User).where(User.email == payload.email)
    existing_user = (await db.execute(stmt)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Hash password with bcrypt
    hashed_pwd = get_password_hash(payload.password)

    # Create new User
    user = User(
        email=payload.email,
        hashed_password=hashed_pwd,
        full_name=payload.full_name,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    # Assign STUDENT role
    role_stmt = select(Role).where(Role.name == "STUDENT")
    student_role = (await db.execute(role_stmt)).scalar_one_or_none()
    if not student_role:
        # Fallback create role if seed has not executed
        student_role = Role(name="STUDENT", description="Student Learner")
        db.add(student_role)
        await db.flush()

    user_role = UserRole(user_id=user.id, role_id=student_role.id)
    db.add(user_role)

    # Create initial StudentProfile with onboarding_completed=False
    student_profile = StudentProfile(
        user_id=user.id,
        onboarding_completed=False,
    )
    db.add(student_profile)

    await db.commit()

    # Re-query user to load eager relationships
    query = (
        select(User)
        .where(User.id == user.id)
        .options(
            selectinload(User.user_roles).selectinload(UserRole.role),
            selectinload(User.student_profile),
        )
    )
    loaded_user = (await db.execute(query)).scalar_one()

    # Generate JWT
    token_claims = {
        "sub": str(loaded_user.id),
        "email": loaded_user.email,
        "roles": ["STUDENT"],
    }
    access_token = create_access_token(token_claims)
    _set_auth_cookie(response, access_token)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=_format_user_response(loaded_user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Account Login",
)
async def login(
    payload: UserLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate with email and password to receive session token."""
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_id = f"login:{client_ip}:{payload.email}"

    if auth_rate_limiter.is_rate_limited(rate_limit_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please wait 1 minute before retrying.",
        )

    # Query user by normalized email
    query = (
        select(User)
        .where(User.email == payload.email)
        .options(
            selectinload(User.user_roles).selectinload(UserRole.role),
            selectinload(User.student_profile),
        )
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        auth_rate_limiter.record_attempt(rate_limit_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support.",
        )

    auth_rate_limiter.reset(rate_limit_id)

    role_names = [ur.role.name for ur in user.user_roles if ur.role]
    token_claims = {
        "sub": str(user.id),
        "email": user.email,
        "roles": role_names,
    }
    access_token = create_access_token(token_claims)
    _set_auth_cookie(response, access_token)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=_format_user_response(user),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User Logout",
)
async def logout(response: Response) -> dict:
    """Invalidate session by clearing the authentication cookie."""
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        path="/",
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    return {"status": "success", "message": "Logged out successfully"}


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Current Authenticated User",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Retrieve identity and roles for the authenticated user."""
    return _format_user_response(current_user)
