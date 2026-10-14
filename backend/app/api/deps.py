"""FastAPI Authentication and Authorization Dependencies."""

import uuid
from typing import AsyncGenerator, Callable, Optional
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.identity import Role, StudentProfile, User, UserRole

# Optional bearer scheme allows fallback to HttpOnly cookie
bearer_security = HTTPBearer(auto_error=False)


def get_token_from_request(
    request: Request,
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(bearer_security),
) -> Optional[str]:
    """Extract JWT token from Authorization header or HttpOnly cookie."""
    if auth_header and auth_header.credentials:
        return auth_header.credentials

    # Fallback to session cookie
    cookie_token = request.cookies.get(settings.AUTH_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    return None


async def get_current_user(
    token: Optional[str] = Depends(get_token_from_request),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate JWT token and resolve authenticated User entity."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = decode_access_token(token)
        user_id_str: Optional[str] = payload.get("sub")
        if not user_id_str:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    # Query user with eagerly loaded roles and profile
    query = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.user_roles).selectinload(UserRole.role),
            selectinload(User.student_profile),
        )
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def require_role(required_role: str) -> Callable:
    """Dependency factory enforcing role-based access control."""

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_names = [ur.role.name for ur in current_user.user_roles if ur.role]
        if required_role not in user_role_names and "ADMIN" not in user_role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role} privilege",
            )
        return current_user

    return role_checker


async def get_current_student(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StudentProfile:
    """Ensure authenticated user is a student and return their isolated StudentProfile."""
    user_role_names = [ur.role.name for ur in current_user.user_roles if ur.role]
    if "STUDENT" not in user_role_names and "ADMIN" not in user_role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to student accounts",
        )

    # Fetch fresh student profile with enrolled subjects
    query = (
        select(StudentProfile)
        .where(StudentProfile.user_id == current_user.id)
        .options(
            selectinload(StudentProfile.selected_subjects),
            selectinload(StudentProfile.target_curriculum),
            selectinload(StudentProfile.grade_stage),
        )
    )
    res = await db.execute(query)
    profile = res.scalar_one_or_none()

    if not profile:
        # Create empty profile if not yet created
        profile = StudentProfile(
            user_id=current_user.id,
            onboarding_completed=False,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return profile
