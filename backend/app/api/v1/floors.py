"""Floor API endpoints.

Endpoints
---------
POST   /properties/{property_id}/floors → Create floor (Owner)
PATCH  /floors/{id}                     → Update floor (Owner)
DELETE /floors/{id}                     → Soft delete floor (Owner)
GET    /properties/{property_id}/floors → List floors (Public)
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
from app.schemas.common import MessageResponse, SuccessResponse, build_meta
from app.schemas.floor import FloorCreate, FloorRead, FloorUpdate
from app.services.floor_service import FloorService

router = APIRouter()


def _make_floor_service(db: AsyncSession) -> FloorService:
    return FloorService(
        floor_repo=FloorRepository(db),
        property_repo=PropertyRepository(db),
    )


# ── POST /properties/{property_id}/floors ────────────────────────────────────


@router.post(
    "/properties/{property_id}/floors",
    response_model=SuccessResponse[FloorRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create floor",
    description="Create a new floor within a property.",
)
async def create_floor(
    request: Request,
    property_id: uuid.UUID,
    data: FloorCreate,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[FloorRead]:
    service = _make_floor_service(db)
    floor = await service.create_floor(property_id, current_user.id, data, db)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=FloorRead.model_validate(floor),
        meta=build_meta(request_id),
    )


# ── GET /properties/{property_id}/floors ─────────────────────────────────────


@router.get(
    "/properties/{property_id}/floors",
    response_model=SuccessResponse[list[FloorRead]],
    status_code=status.HTTP_200_OK,
    summary="List floors",
    description="List all floors for a property.",
)
async def list_floors(
    request: Request,
    property_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[list[FloorRead]]:
    service = _make_floor_service(db)
    floors = await service.list_floors(property_id)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=[FloorRead.model_validate(f) for f in floors],
        meta=build_meta(request_id),
    )


# ── PATCH /floors/{floor_id} ─────────────────────────────────────────────────


@router.patch(
    "/floors/{floor_id}",
    response_model=SuccessResponse[FloorRead],
    status_code=status.HTTP_200_OK,
    summary="Update floor",
    description="Partially update a floor.",
)
async def update_floor(
    request: Request,
    floor_id: uuid.UUID,
    data: FloorUpdate,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[FloorRead]:
    service = _make_floor_service(db)
    floor = await service.update_floor(floor_id, current_user.id, data, db)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=FloorRead.model_validate(floor),
        meta=build_meta(request_id),
    )


# ── DELETE /floors/{floor_id} ────────────────────────────────────────────────


@router.delete(
    "/floors/{floor_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete floor",
    description="Soft-delete a floor and its child rooms/beds.",
)
async def delete_floor(
    request: Request,
    floor_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = _make_floor_service(db)
    await service.delete_floor(floor_id, current_user.id, db)
    request_id: str = getattr(request.state, "request_id", "")
    return MessageResponse(
        message="Floor deleted successfully.",
        meta=build_meta(request_id),
    )
