"""
Authentication API routes: signup and login.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import LoginRequest, SignupRequest, TokenResponse
from app.services.user_service import get_user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(
    data: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    service = get_user_service()
    return await service.signup(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and receive an access token."""
    service = get_user_service()
    return await service.login(db, data)
