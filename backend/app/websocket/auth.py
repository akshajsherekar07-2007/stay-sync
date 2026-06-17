"""WebSocket authentication helper.

Validates JWT tokens passed as a query parameter during the WebSocket
handshake. Reuses the existing ``decode_access_token`` from the security
module — no new auth mechanism introduced.
"""

from __future__ import annotations

import logging

from app.core.security import decode_access_token

logger = logging.getLogger(__name__)


class WebSocketAuthError(Exception):
    """Raised when WebSocket authentication fails."""

    def __init__(self, message: str, code: int = 4001) -> None:
        super().__init__(message)
        self.code = code


def authenticate_websocket(token: str | None) -> dict[str, str]:
    """Validate a JWT token for WebSocket connections.

    Args:
        token: The raw JWT string from the ``?token=`` query parameter.

    Returns:
        A dict with ``user_id`` and ``role`` extracted from the JWT.

    Raises:
        WebSocketAuthError: If the token is missing, invalid, or expired.
    """
    if not token:
        raise WebSocketAuthError("Missing authentication token", code=4001)

    try:
        payload = decode_access_token(token)
    except Exception as exc:
        logger.warning("WebSocket auth failed: %s", exc)
        raise WebSocketAuthError("Invalid or expired token", code=4001) from exc

    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id:
        raise WebSocketAuthError("Invalid token payload", code=4001)

    return {"user_id": user_id, "role": role or "unknown"}
