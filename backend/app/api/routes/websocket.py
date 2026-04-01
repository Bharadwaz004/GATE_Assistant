"""
WebSocket endpoint for real-time client updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.utils.auth import decode_token
from app.utils.websocket import ws_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket connection endpoint.
    Requires JWT token as query parameter for authentication.

    Client usage:
        const ws = new WebSocket(`ws://localhost:8000/ws?token=${accessToken}`);
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            // Handle: plan_generated, task_updated, streak_updated, new_match
        };
    """
    # Validate token
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
    except Exception:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    # Connect
    await ws_manager.connect(websocket, user_id)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Real-time updates active",
            "user_id": user_id,
        })

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_json()

            # Handle ping/pong for keepalive
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
    except Exception:
        ws_manager.disconnect(websocket, user_id)
