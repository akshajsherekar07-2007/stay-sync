"""API v1 aggregated router.

All v1 endpoint routers are mounted here.
This module is imported by the application factory.
"""

from fastapi import APIRouter

from app.api.v1 import amenities, auth, beds, floors, properties, rooms, users

api_v1_router = APIRouter(tags=["v1"])


@api_v1_router.get("/ping", tags=["Health"])
async def ping() -> dict[str, str]:
    """Simple connectivity check for the v1 API."""
    return {"message": "pong", "api_version": "v1"}


# ── Phase 1.4 routers ─────────────────────────────────────────────────────────
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])

# ── Phase 1.5 routers ─────────────────────────────────────────────────────────
api_v1_router.include_router(
    properties.router, prefix="/properties", tags=["Properties"]
)
api_v1_router.include_router(floors.router, tags=["Floors"])
api_v1_router.include_router(rooms.router, tags=["Rooms"])
api_v1_router.include_router(beds.router, tags=["Beds"])
api_v1_router.include_router(
    amenities.router, prefix="/amenities", tags=["Amenities"]
)

# ── Phase 2 routers ──────────────────────────────────────────────────────────
# from app.api.v1 import holds, waitlists, notifications

# ── Phase 3 routers ──────────────────────────────────────────────────────────
# from app.api.v1 import analytics
