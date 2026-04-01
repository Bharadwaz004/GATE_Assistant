"""
WebSocket connection manager for real-time updates.
Pushes plan generation status, task updates, and streak changes to clients.
"""

import json
import logging
from typing import Dict, Set
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections per user.
    Supports broadcasting to all connections of a specific user.
    """

    def __init__(self):
        # user_id -> set of active WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept a new WebSocket connection for a user."""
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(websocket)
        logger.info(f"WS connected: user={user_id} (total={len(self._connections[user_id])})")

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """Remove a disconnected WebSocket."""
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]
        logger.info(f"WS disconnected: user={user_id}")

    async def send_to_user(self, user_id: str, message: dict) -> None:
        """Send a JSON message to all connections of a specific user."""
        connections = self._connections.get(user_id, set())
        dead = set()

        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)

        # Clean up dead connections
        for ws in dead:
            self.disconnect(ws, user_id)

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected users."""
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, message)

    @property
    def active_connections_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


# ── Singleton ────────────────────────────────────────────────
ws_manager = ConnectionManager()


# ── Event Helpers ────────────────────────────────────────────
async def notify_plan_generated(user_id: str, plan_id: str) -> None:
    """Notify user that their plan has been generated."""
    await ws_manager.send_to_user(user_id, {
        "type": "plan_generated",
        "plan_id": plan_id,
        "message": "Your study plan is ready!",
    })


async def notify_task_updated(user_id: str, task_id: str, status: str) -> None:
    """Notify user of a task status change."""
    await ws_manager.send_to_user(user_id, {
        "type": "task_updated",
        "task_id": task_id,
        "status": status,
    })


async def notify_streak_update(user_id: str, current: int, longest: int) -> None:
    """Notify user of a streak change."""
    await ws_manager.send_to_user(user_id, {
        "type": "streak_updated",
        "current_streak": current,
        "longest_streak": longest,
    })


async def notify_new_match(user_id: str, matched_name: str, score: float) -> None:
    """Notify user of a new study partner match."""
    await ws_manager.send_to_user(user_id, {
        "type": "new_match",
        "matched_name": matched_name,
        "similarity_score": score,
        "message": f"New study partner match: {matched_name}!",
    })
