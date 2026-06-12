"""Room API endpoints.

Endpoints
---------
POST   /floors/{floor_id}/rooms → Create room (Owner)
GET    /floors/{floor_id}/rooms → List rooms (Public)
PATCH  /rooms/{id}              → Update room (Owner)
DELETE /rooms/{id}              → Soft delete room (Owner)
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_owner
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.floor_repository import FloorRepository
from app.repositories.property_repository import PropertyRepository
from app.repositories.room_repository import RoomRepository
from app.schemas.common import MessageResponse, SuccessResponse, build_meta
from app.schemas.room import RoomCreate, RoomRead, RoomUpdate
from app.services.room_service import RoomService

router = APIRouter()


def _make_room_service(db: AsyncSession) -> RoomService:
    return RoomService(
        room_repo=RoomRepository(db),
        floor_repo=FloorRepository(db),
        property_repo=PropertyRepository(db),
    )


# ── POST /floors/{floor_id}/rooms ────────────────────────────────────────────


@router.post(
    "/floors/{floor_id}/rooms",
    response_model=SuccessResponse[RoomRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create room",
    description="Create a new room within a floor.",
)
async def create_room(
    request: Request,
    floor_id: uuid.UUID,
    data: RoomCreate,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[RoomRead]:
    service = _make_room_service(db)
    room = await service.create_room(floor_id, current_user.id, data, db)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=RoomRead.model_validate(room),
        meta=build_meta(request_id),
    )


# ── GET /floors/{floor_id}/rooms ─────────────────────────────────────────────


@router.get(
    "/floors/{floor_id}/rooms",
    response_model=SuccessResponse[list[RoomRead]],
    status_code=status.HTTP_200_OK,
    summary="List rooms",
    description="List all rooms for a floor.",
)
async def list_rooms(
    request: Request,
    floor_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[list[RoomRead]]:
    service = _make_room_service(db)
    rooms = await service.list_rooms(floor_id)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=[RoomRead.model_validate(r) for r in rooms],
        meta=build_meta(request_id),
    )


# ── PATCH /rooms/{room_id} ───────────────────────────────────────────────────


@router.patch(
    "/rooms/{room_id}",
    response_model=SuccessResponse[RoomRead],
    status_code=status.HTTP_200_OK,
    summary="Update room",
    description="Partially update a room.",
)
async def update_room(
    request: Request,
    room_id: uuid.UUID,
    data: RoomUpdate,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[RoomRead]:
    service = _make_room_service(db)
    room = await service.update_room(room_id, current_user.id, data, db)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=RoomRead.model_validate(room),
        meta=build_meta(request_id),
    )


# ── DELETE /rooms/{room_id} ──────────────────────────────────────────────────


@router.delete(
    "/rooms/{room_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete room",
    description="Soft-delete a room and its child beds.",
)
async def delete_room(
    request: Request,
    room_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = _make_room_service(db)
    await service.delete_room(room_id, current_user.id, db)
    request_id: str = getattr(request.state, "request_id", "")
    return MessageResponse(
        message="Room deleted successfully.",
        meta=build_meta(request_id),
    )
