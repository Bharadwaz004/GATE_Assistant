"""
Study partner matching API routes.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.schemas import MatchedUser, MatchingResponse
from app.services.matching_service import get_matching_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/match", tags=["Matching"])


@router.get("", response_model=MatchingResponse)
async def get_matches(
    top_n: int = Query(default=10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Find study partners matched by profile similarity.
    Uses sentence-transformer embeddings and cosine similarity.
    """
    service = get_matching_service()
    matches = await service.find_matches(db, user.id, top_n=top_n)

    matched_users = [
        MatchedUser(
            user_id=m["user_id"],
            full_name=m["full_name"],
            branch=m["branch"],
            prep_type=m["prep_type"],
            subjects=m["subjects"],
            similarity_score=m["similarity_score"],
            common_subjects=m["common_subjects"],
        )
        for m in matches
    ]

    return MatchingResponse(
        matches=matched_users,
        total_found=len(matched_users),
    )
