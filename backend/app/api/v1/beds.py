"""Bed API endpoints.

Endpoints
---------
POST   /rooms/{room_id}/beds → Create bed (Owner)
GET    /rooms/{room_id}/beds → List beds (Public)
PATCH  /beds/{id}            → Update bed (Owner)
DELETE /beds/{id}            → Soft delete bed (Owner)
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_owner
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.bed_repository import BedRepository
from app.repositories.property_repository import PropertyRepository
from app.repositories.room_repository import RoomRepository
from app.schemas.bed import BedCreate, BedRead, BedUpdate
from app.schemas.common import MessageResponse, SuccessResponse, build_meta
from app.services.bed_service import BedService

router = APIRouter()


def _make_bed_service(db: AsyncSession) -> BedService:
    return BedService(
        bed_repo=BedRepository(db),
        room_repo=RoomRepository(db),
        property_repo=PropertyRepository(db),
    )


# ── POST /rooms/{room_id}/beds ───────────────────────────────────────────────


@router.post(
    "/rooms/{room_id}/beds",
    response_model=SuccessResponse[BedRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create bed",
    description="Create a new bed within a room.",
)
async def create_bed(
    request: Request,
    room_id: uuid.UUID,
    data: BedCreate,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[BedRead]:
    service = _make_bed_service(db)
    bed = await service.create_bed(room_id, current_user.id, data, db)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=BedRead.model_validate(bed),
        meta=build_meta(request_id),
    )


# ── GET /rooms/{room_id}/beds ────────────────────────────────────────────────


@router.get(
    "/rooms/{room_id}/beds",
    response_model=SuccessResponse[list[BedRead]],
    status_code=status.HTTP_200_OK,
    summary="List beds",
    description="List all beds for a room.",
)
async def list_beds(
    request: Request,
    room_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[list[BedRead]]:
    service = _make_bed_service(db)
    beds = await service.list_beds(room_id)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=[BedRead.model_validate(b) for b in beds],
        meta=build_meta(request_id),
    )


# ── PATCH /beds/{bed_id} ─────────────────────────────────────────────────────


@router.patch(
    "/beds/{bed_id}",
    response_model=SuccessResponse[BedRead],
    status_code=status.HTTP_200_OK,
    summary="Update bed",
    description="Partially update a bed.",
)
async def update_bed(
    request: Request,
    bed_id: uuid.UUID,
    data: BedUpdate,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[BedRead]:
    service = _make_bed_service(db)
    bed = await service.update_bed(bed_id, current_user.id, data, db)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=BedRead.model_validate(bed),
        meta=build_meta(request_id),
    )


# ── DELETE /beds/{bed_id} ────────────────────────────────────────────────────


@router.delete(
    "/beds/{bed_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete bed",
    description="Soft-delete a bed.",
)
async def delete_bed(
    request: Request,
    bed_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = _make_bed_service(db)
    await service.delete_bed(bed_id, current_user.id, db)
    request_id: str = getattr(request.state, "request_id", "")
    return MessageResponse(
        message="Bed deleted successfully.",
        meta=build_meta(request_id),
    )
