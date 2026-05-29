"""API v1 aggregated router.

All v1 endpoint routers are mounted here.
This module is imported by the application factory.
"""

from fastapi import APIRouter

api_v1_router = APIRouter(tags=["v1"])


@api_v1_router.get("/ping", tags=["Health"])
async def ping() -> dict[str, str]:
    """Simple connectivity check for the v1 API."""
    return {"message": "pong", "api_version": "v1"}


# ── Phase 1 routers (will be added in subsequent tasks) ──────
# from app.api.v1 import auth, users, properties, floors, rooms, beds

# ── Phase 2 routers ──────────────────────────────────────────
# from app.api.v1 import holds, waitlists, notifications

# ── Phase 3 routers ──────────────────────────────────────────
# from app.api.v1 import analytics
