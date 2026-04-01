"""
Central API router — aggregates all route modules.
"""

from fastapi import APIRouter

from app.api.routes import analytics, auth, matching, plan, user, websocket

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router)
api_router.include_router(user.router)
api_router.include_router(plan.router)
api_router.include_router(matching.router)
api_router.include_router(analytics.router)

# WebSocket router (mounted separately at app level, no /api prefix)
ws_router = websocket.router
