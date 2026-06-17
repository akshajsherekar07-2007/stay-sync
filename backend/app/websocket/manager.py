"""In-memory WebSocket connection manager.

Tracks active WebSocket connections per user and per property room.
Provides methods to broadcast events to specific users or property
subscribers.

Designed with a clean broadcast interface so that a Redis Pub/Sub
adapter can replace the in-memory storage in a future horizontal-scaling
phase without changing callers.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections in-memory.

    Channel types:
        - ``user:{user_id}``     — personal notifications
        - ``property:{prop_id}`` — bed availability updates for viewers
    """

    def __init__(self) -> None:
        # user_id (str) → set of active WebSocket connections
        self._user_connections: dict[str, set[WebSocket]] = {}
        # property_id (str) → set of WebSocket connections subscribed
        self._property_connections: dict[str, set[WebSocket]] = {}
        # websocket → user_id (reverse lookup for cleanup)
        self._ws_to_user: dict[WebSocket, str] = {}
        # websocket → set of property_ids subscribed
        self._ws_to_properties: dict[WebSocket, set[str]] = {}

    # ── Connection lifecycle ──────────────────────────────────────────────────

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Register a new WebSocket connection for a user."""
        await websocket.accept()

        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(websocket)

        self._ws_to_user[websocket] = user_id
        self._ws_to_properties[websocket] = set()

        logger.info("WebSocket connected: user=%s (total=%d)", user_id, len(self._ws_to_user))

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection and clean up all subscriptions."""
        user_id = self._ws_to_user.pop(websocket, None)

        if user_id and user_id in self._user_connections:
            self._user_connections[user_id].discard(websocket)
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]

        # Remove from all property rooms
        property_ids = self._ws_to_properties.pop(websocket, set())
        for prop_id in property_ids:
            if prop_id in self._property_connections:
                self._property_connections[prop_id].discard(websocket)
                if not self._property_connections[prop_id]:
                    del self._property_connections[prop_id]

        logger.info("WebSocket disconnected: user=%s (remaining=%d)", user_id, len(self._ws_to_user))

    # ── Room subscription ─────────────────────────────────────────────────────

    def subscribe_property(self, websocket: WebSocket, property_id: str) -> None:
        """Subscribe a connection to a property room for bed updates."""
        if property_id not in self._property_connections:
            self._property_connections[property_id] = set()
        self._property_connections[property_id].add(websocket)

        if websocket in self._ws_to_properties:
            self._ws_to_properties[websocket].add(property_id)

        user_id = self._ws_to_user.get(websocket, "unknown")
        logger.debug("User %s subscribed to property %s", user_id, property_id)

    def unsubscribe_property(self, websocket: WebSocket, property_id: str) -> None:
        """Unsubscribe a connection from a property room."""
        if property_id in self._property_connections:
            self._property_connections[property_id].discard(websocket)
            if not self._property_connections[property_id]:
                del self._property_connections[property_id]

        if websocket in self._ws_to_properties:
            self._ws_to_properties[websocket].discard(property_id)

    # ── Broadcasting ──────────────────────────────────────────────────────────

    async def send_to_user(self, user_id: str, event: dict[str, Any]) -> None:
        """Send an event to all connections of a specific user."""
        connections = self._user_connections.get(user_id, set())
        if not connections:
            return

        message = json.dumps(event)
        stale: list[WebSocket] = []

        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                stale.append(ws)

        for ws in stale:
            await self.disconnect(ws)

    async def broadcast_to_property(self, property_id: str, event: dict[str, Any]) -> None:
        """Broadcast an event to all connections watching a property."""
        connections = self._property_connections.get(property_id, set())
        if not connections:
            return

        message = json.dumps(event)
        stale: list[WebSocket] = []

        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                stale.append(ws)

        for ws in stale:
            await self.disconnect(ws)

    # ── Diagnostics ───────────────────────────────────────────────────────────

    @property
    def active_connections(self) -> int:
        """Total number of active WebSocket connections."""
        return len(self._ws_to_user)

    @property
    def active_users(self) -> int:
        """Number of distinct users with active connections."""
        return len(self._user_connections)
