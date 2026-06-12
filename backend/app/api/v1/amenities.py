"""Amenity API endpoints.

Endpoints
---------
GET /amenities → List all amenities from master catalog (Public)
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.repositories.amenity_repository import AmenityRepository
from app.schemas.amenity import AmenityRead
from app.schemas.common import SuccessResponse, build_meta

router = APIRouter()


@router.get(
    "",
    response_model=SuccessResponse[list[AmenityRead]],
    status_code=status.HTTP_200_OK,
    summary="List amenities",
    description="Fetch all available amenities from the master catalog.",
)
async def list_amenities(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[list[AmenityRead]]:
    repo = AmenityRepository(db)
    amenities = await repo.list_all()
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=[AmenityRead.model_validate(a) for a in amenities],
        meta=build_meta(request_id),
    )
