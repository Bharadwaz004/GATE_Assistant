"""
Study partner matching service using Sentence Transformers.
Converts user profiles to embeddings and computes cosine similarity.
"""

import logging
from typing import List, Optional
from uuid import UUID

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import MatchingScore, User, UserEmbedding, UserProfile

logger = logging.getLogger(__name__)
settings = get_settings()

def _text_to_vector(text: str, all_texts: List[str]) -> List[float]:
    """Generate TF-IDF vector for text given a corpus."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    corpus = list(dict.fromkeys(all_texts + [text]))  # deduplicated
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(corpus)
    idx = corpus.index(text)
    return matrix[idx].toarray().flatten().tolist()


class MatchingService:
    """
    Matches study partners based on profile similarity.

    Pipeline:
    1. Convert user profiles to natural language descriptions
    2. Generate embeddings using sentence-transformers
    3. Compute cosine similarity between all user pairs
    4. Return top-N matches for a given user
    """

    @staticmethod
    def profile_to_text(profile: UserProfile) -> str:
        """
        Convert a user profile into a descriptive text string
        suitable for embedding generation.
        """
        subjects = profile.subjects if isinstance(profile.subjects, list) else []
        subjects_str = ", ".join(subjects) if subjects else "General"

        text_parts = [
            f"GATE {profile.branch} aspirant",
            f"preparing via {profile.prep_type}",
            f"studying {subjects_str}",
            f"exam date {profile.target_exam_date}",
        ]

        if profile.prep_type == "coaching":
            if profile.coaching_start_time and profile.coaching_end_time:
                text_parts.append(
                    f"coaching from {profile.coaching_start_time} to {profile.coaching_end_time}"
                )
        else:
            if profile.daily_available_hours:
                text_parts.append(
                    f"{profile.daily_available_hours} hours daily study"
                )

        return ". ".join(text_parts)

    @staticmethod
    def generate_embedding(text: str, corpus: List[str] = None) -> List[float]:
        """Generate TF-IDF vector from profile text."""
        return _text_to_vector(text, corpus or [text])

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a = np.array(vec_a)
        b = np.array(vec_b)
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    async def update_user_embedding(
        self,
        db: AsyncSession,
        user_id: UUID,
        profile: UserProfile,
    ) -> UserEmbedding:
        """Create or update embedding for a user profile."""
        profile_text = self.profile_to_text(profile)
        vector = self.generate_embedding(profile_text, [profile_text])

        # Check for existing embedding
        result = await db.execute(
            select(UserEmbedding).where(UserEmbedding.user_id == user_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.embedding_vector = vector
            existing.profile_text = profile_text
            return existing
        else:
            embedding = UserEmbedding(
                user_id=user_id,
                embedding_vector=vector,
                profile_text=profile_text,
            )
            db.add(embedding)
            return embedding

    async def find_matches(
        self,
        db: AsyncSession,
        user_id: UUID,
        top_n: int = 10,
    ) -> List[dict]:
        """
        Find top-N study partner matches for a user.

        Steps:
        1. Get the user's embedding
        2. Fetch all other user embeddings
        3. Compute cosine similarities
        4. Return sorted top-N matches with profile details
        """
        # Get current user's embedding
        result = await db.execute(
            select(UserEmbedding).where(UserEmbedding.user_id == user_id)
        )
        user_embedding = result.scalar_one_or_none()

        if not user_embedding:
            return []

        # Get all other embeddings
        result = await db.execute(
            select(UserEmbedding).where(UserEmbedding.user_id != user_id)
        )
        other_embeddings = result.scalars().all()

        if not other_embeddings:
            return []

        # Recompute similarities using shared TF-IDF corpus for consistent dimensions
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity as sk_cosine

        all_texts = [user_embedding.profile_text] + [o.profile_text for o in other_embeddings]
        vectorizer = TfidfVectorizer()
        matrix = vectorizer.fit_transform(all_texts)

        user_vec = matrix[0]
        other_vecs = matrix[1:]
        scores = sk_cosine(user_vec, other_vecs).flatten()

        matches = []
        for i, other in enumerate(other_embeddings):
            matches.append({
                "user_id": str(other.user_id),
                "similarity_score": round(float(scores[i]), 4),
            })

        # Sort by similarity (descending) and take top N
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_matches = matches[:top_n]

        # Enrich with profile data
        enriched = []
        for match in top_matches:
            matched_uid = match["user_id"]

            # Fetch user + profile
            user_result = await db.execute(
                select(User).where(User.id == matched_uid)
            )
            matched_user = user_result.scalar_one_or_none()

            profile_result = await db.execute(
                select(UserProfile).where(UserProfile.user_id == matched_uid)
            )
            matched_profile = profile_result.scalar_one_or_none()

            if matched_user and matched_profile:
                # Get current user's profile for common subjects
                curr_profile_result = await db.execute(
                    select(UserProfile).where(UserProfile.user_id == user_id)
                )
                curr_profile = curr_profile_result.scalar_one_or_none()

                curr_subjects = set(
                    curr_profile.subjects if curr_profile and isinstance(curr_profile.subjects, list) else []
                )
                matched_subjects = set(
                    matched_profile.subjects if isinstance(matched_profile.subjects, list) else []
                )

                enriched.append({
                    "user_id": matched_uid,
                    "full_name": matched_user.full_name,
                    "branch": matched_profile.branch,
                    "prep_type": matched_profile.prep_type,
                    "subjects": matched_profile.subjects or [],
                    "similarity_score": match["similarity_score"],
                    "common_subjects": list(curr_subjects & matched_subjects),
                })

            # Store/update matching score
            await self._store_score(db, user_id, matched_uid, match["similarity_score"])

        return enriched

    async def _store_score(
        self,
        db: AsyncSession,
        user_id: UUID,
        matched_user_id: str,
        score: float,
    ) -> None:
        """Persist a matching score to the database."""
        result = await db.execute(
            select(MatchingScore).where(
                MatchingScore.user_id == user_id,
                MatchingScore.matched_user_id == matched_user_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.similarity_score = score
        else:
            db.add(MatchingScore(
                user_id=user_id,
                matched_user_id=matched_user_id,
                similarity_score=score,
            ))


# ── Singleton ────────────────────────────────────────────────
_matching_service: Optional[MatchingService] = None


def get_matching_service() -> MatchingService:
    global _matching_service
    if _matching_service is None:
        _matching_service = MatchingService()
    return _matching_service
