"""WebSocket event type definitions and broadcast helpers.

Defines the event constants and a lightweight factory for constructing
broadcast-ready event payloads.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


# ── Event type constants ──────────────────────────────────────────────────────

class WSEventType:
    """WebSocket event type string constants."""

    # Notification events (user-targeted)
    NOTIFICATION_CREATED = "notification_created"

    # Hold lifecycle events
    HOLD_CREATED = "hold_created"
    HOLD_APPROVED = "hold_approved"
    HOLD_REJECTED = "hold_rejected"
    HOLD_CANCELLED = "hold_cancelled"
    HOLD_EXPIRED = "hold_expired"

    # Waitlist events
    WAITLIST_PROMOTED = "waitlist_promoted"

    # Property / bed events (property-room-targeted)
    BED_STATUS_CHANGED = "bed_status_changed"


# ── Event factory ─────────────────────────────────────────────────────────────

def build_event(event_type: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Construct a WebSocket event payload.

    Args:
        event_type: One of the ``WSEventType`` constants.
        data:       Event-specific payload data.

    Returns:
        A JSON-serializable dict with ``type``, ``data``, and ``timestamp``.
    """
    return {
        "type": event_type,
        "data": data or {},
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }
