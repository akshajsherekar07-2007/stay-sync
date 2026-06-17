"""WebSocket handlers package (Phase 2).

Exports:
    ConnectionManager — in-memory WebSocket connection tracker.
    authenticate_websocket — JWT validation for WS handshakes.
    WSEventType, build_event — event type constants and payload factory.
"""

from app.websocket.manager import ConnectionManager
from app.websocket.auth import authenticate_websocket, WebSocketAuthError
from app.websocket.events import WSEventType, build_event

__all__ = [
    "ConnectionManager",
    "authenticate_websocket",
    "WebSocketAuthError",
    "WSEventType",
    "build_event",
]
