"""WebSocket endpoint for real-time event streaming.

Handles the WebSocket lifecycle:
  1. Authenticate via JWT query parameter.
  2. Register connection with ConnectionManager.
  3. Listen for subscribe/unsubscribe messages.
  4. Clean up on disconnect.

Mounted at ``/api/v1/ws`` by the v1 router.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.auth import WebSocketAuthError, authenticate_websocket
from app.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_manager(websocket: WebSocket) -> ConnectionManager:
    """Retrieve the ConnectionManager from the application state."""
    return websocket.app.state.ws_manager


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = None) -> None:
    """Main WebSocket endpoint.

    Query Parameters:
        token: JWT access token for authentication.

    Client → Server messages (JSON):
        ``{"action": "subscribe", "channel": "property:<uuid>"}``
        ``{"action": "unsubscribe", "channel": "property:<uuid>"}``
        ``{"action": "ping"}``

    Server → Client messages (JSON):
        ``{"type": "<event_type>", "data": {...}, "timestamp": "..."}``
    """
    manager = _get_manager(websocket)

    # 1. Authenticate
    try:
        auth_info = authenticate_websocket(token)
    except WebSocketAuthError as exc:
        await websocket.close(code=exc.code, reason=str(exc))
        return

    user_id = auth_info["user_id"]

    # 2. Register connection
    await manager.connect(websocket, user_id)

    try:
        # 3. Listen for client messages
        while True:
            raw = await websocket.receive_text()

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"type": "error", "data": {"message": "Invalid JSON"}})
                )
                continue

            action = message.get("action")
            channel = message.get("channel", "")

            if action == "ping":
                await websocket.send_text(
                    json.dumps({"type": "pong", "data": {}})
                )

            elif action == "subscribe" and channel.startswith("property:"):
                property_id = channel.removeprefix("property:")
                manager.subscribe_property(websocket, property_id)
                await websocket.send_text(
                    json.dumps({
                        "type": "subscribed",
                        "data": {"channel": channel},
                    })
                )

            elif action == "unsubscribe" and channel.startswith("property:"):
                property_id = channel.removeprefix("property:")
                manager.unsubscribe_property(websocket, property_id)
                await websocket.send_text(
                    json.dumps({
                        "type": "unsubscribed",
                        "data": {"channel": channel},
                    })
                )

            else:
                await websocket.send_text(
                    json.dumps({
                        "type": "error",
                        "data": {"message": f"Unknown action: {action}"},
                    })
                )

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected: user=%s", user_id)
    except Exception as exc:
        logger.exception("WebSocket error for user=%s: %s", user_id, exc)
    finally:
        await manager.disconnect(websocket)
