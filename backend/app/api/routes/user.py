"""
User profile and onboarding API routes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.schemas import OnboardingRequest, UserProfileResponse
from app.services.user_service import get_user_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/onboarding", response_model=UserProfileResponse)
async def onboarding(
    data: OnboardingRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit or update onboarding profile."""
    service = get_user_service()
    return await service.onboard(db, user, data)


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve current user profile."""
    service = get_user_service()
    return await service.get_profile(db, user)
