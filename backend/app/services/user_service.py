"""
User service: handles authentication, onboarding, and profile management.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, UserProfile
from app.schemas import (
    LoginRequest,
    OnboardingRequest,
    SignupRequest,
    TokenResponse,
    UserProfileResponse,
)
from app.services.matching_service import get_matching_service
from app.utils.auth import create_access_token, hash_password, verify_password

logger = logging.getLogger(__name__)


class UserService:
    """Business logic for user-related operations."""

    async def signup(
        self, db: AsyncSession, data: SignupRequest
    ) -> TokenResponse:
        """Register a new user and return an access token."""
        # Check if email exists
        result = await db.execute(
            select(User).where(User.email == data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        # Create user
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        db.add(user)
        await db.flush()

        token = create_access_token(str(user.id))

        return TokenResponse(
            access_token=token,
            user_id=str(user.id),
            is_onboarded=False,
        )

    async def login(
        self, db: AsyncSession, data: LoginRequest
    ) -> TokenResponse:
        """Authenticate a user and return an access token."""
        result = await db.execute(
            select(User).where(User.email == data.email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        token = create_access_token(str(user.id))

        return TokenResponse(
            access_token=token,
            user_id=str(user.id),
            is_onboarded=user.is_onboarded,
        )

    async def onboard(
        self, db: AsyncSession, user: User, data: OnboardingRequest
    ) -> UserProfileResponse:
        """Save onboarding data and generate user embedding."""
        # Check for existing profile
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        existing = result.scalar_one_or_none()

        # Prepare study slots data
        slots_data = None
        if data.available_study_slots:
            slots_data = [s.model_dump() for s in data.available_study_slots]

        if existing:
            # Update existing profile
            existing.branch = data.branch
            existing.prep_type = data.prep_type
            existing.target_exam_date = data.target_exam_date
            existing.subjects = data.subjects
            existing.coaching_start_time = data.coaching_start_time
            existing.coaching_end_time = data.coaching_end_time
            existing.available_study_slots = slots_data
            existing.daily_available_hours = data.daily_available_hours
            profile = existing
        else:
            profile = UserProfile(
                user_id=user.id,
                branch=data.branch,
                prep_type=data.prep_type,
                target_exam_date=data.target_exam_date,
                subjects=data.subjects,
                coaching_start_time=data.coaching_start_time,
                coaching_end_time=data.coaching_end_time,
                available_study_slots=slots_data,
                daily_available_hours=data.daily_available_hours,
            )
            db.add(profile)

        user.is_onboarded = True
        await db.flush()

        # Generate embedding for matching (async, non-blocking)
        try:
            matching = get_matching_service()
            await matching.update_user_embedding(db, user.id, profile)
        except Exception as e:
            logger.warning(f"Embedding generation failed (non-critical): {e}")

        return UserProfileResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_onboarded=True,
            branch=profile.branch,
            prep_type=profile.prep_type,
            target_exam_date=profile.target_exam_date,
            subjects=profile.subjects,
            daily_available_hours=profile.daily_available_hours,
            coaching_start_time=profile.coaching_start_time,
            coaching_end_time=profile.coaching_end_time,
        )

    async def get_profile(
        self, db: AsyncSession, user: User
    ) -> UserProfileResponse:
        """Retrieve the full user profile."""
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()

        return UserProfileResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_onboarded=user.is_onboarded,
            branch=profile.branch if profile else None,
            prep_type=profile.prep_type if profile else None,
            target_exam_date=profile.target_exam_date if profile else None,
            subjects=profile.subjects if profile else None,
            daily_available_hours=profile.daily_available_hours if profile else None,
            coaching_start_time=profile.coaching_start_time if profile else None,
            coaching_end_time=profile.coaching_end_time if profile else None,
        )


def get_user_service() -> UserService:
    return UserService()
