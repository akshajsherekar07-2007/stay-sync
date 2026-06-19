"""Property API endpoints.

All routes are mounted at /api/v1/properties by the v1 router.

Endpoints
---------
POST   /properties                              → Create property (Owner)
GET    /properties                              → List properties (Public, filtered)
GET    /properties/{id}                         → Property detail (Public)
PATCH  /properties/{id}                         → Update property (Owner)
DELETE /properties/{id}                         → Soft delete property (Owner)
POST   /properties/{id}/status                  → Change status (Owner)
POST   /properties/{id}/refresh                 → Refresh listing (Owner)
POST   /properties/{id}/amenities               → Attach amenities (Owner)
DELETE /properties/{id}/amenities/{amenity_id}   → Detach amenity (Owner)
GET    /properties/{id}/images                  → List images (Public)
POST   /properties/{id}/images                  → Upload image (Owner)
PATCH  /properties/{id}/images/{image_id}       → Update image meta (Owner)
DELETE /properties/{id}/images/{image_id}       → Delete image (Owner)
POST   /properties/{id}/images/reorder          → Reorder images (Owner)
POST   /properties/{id}/save                    → Save to wishlist (Student)
DELETE /properties/{id}/save                    → Remove from wishlist (Student)
"""

from __future__ import annotations

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import (
    get_current_user,
    get_current_user_optional,
    require_owner,
    require_student,
)
from app.dependencies.database import get_db
from app.integrations.supabase_storage import SupabaseStorage
from app.models.user import User
from app.repositories.amenity_repository import AmenityRepository
from app.repositories.image_repository import ImageRepository
from app.repositories.property_repository import PropertyRepository
from app.repositories.saved_property_repository import SavedPropertyRepository
from app.schemas.amenity import AmenityAttach, AmenityRead
from app.schemas.common import (
    MessageResponse,
    PaginatedResponse,
    PaginationInfo,
    SuccessResponse,
    build_meta,
)
from app.schemas.image import ImageRead, ImageReorder, ImageUpdate
from app.schemas.property import (
    PropertyCreate,
    PropertyFilter,
    PropertyListItem,
    PropertyRead,
    PropertyStatusUpdate,
    PropertyUpdate,
)
from app.services.image_service import ImageService
from app.services.property_service import PropertyService

router = APIRouter()


# ── Service factories ─────────────────────────────────────────────────────────


def _make_property_service(db: AsyncSession) -> PropertyService:
    return PropertyService(
        property_repo=PropertyRepository(db),
        amenity_repo=AmenityRepository(db),
        saved_repo=SavedPropertyRepository(db),
    )


def _make_image_service(db: AsyncSession) -> ImageService:
    return ImageService(
        image_repo=ImageRepository(db),
        property_repo=PropertyRepository(db),
        storage=SupabaseStorage(),
    )


# ── POST /properties ─────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=SuccessResponse[PropertyRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create a property",
    description="Create a new property listing. Defaults to draft status.",
)
async def create_property(
    request: Request,
    data: PropertyCreate,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[PropertyRead]:
    service = _make_property_service(db)
    prop = await service.create_property(current_user.id, data, db)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=PropertyRead.model_validate(prop),
        meta=build_meta(request_id),
    )


# ── GET /properties ──────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=PaginatedResponse[PropertyListItem],
    status_code=status.HTTP_200_OK,
    summary="List properties",
    description="Paginated property listing with optional filters.",
)
async def list_properties(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    city: str | None = Query(default=None),
    state: str | None = Query(default=None),
    property_type: str | None = Query(default=None),
    gender_preference: str | None = Query(default=None),
    price_min: float | None = Query(default=None, ge=0),
    price_max: float | None = Query(default=None, ge=0),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, max_length=255),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse[PropertyListItem]:
    from app.core.enums import GenderPreference, PropertyStatus, PropertyType
    from decimal import Decimal

    filters = PropertyFilter(
        city=city,
        state=state,
        property_type=PropertyType(property_type) if property_type else None,
        gender_preference=GenderPreference(gender_preference) if gender_preference else None,
        price_min=Decimal(str(price_min)) if price_min is not None else None,
        price_max=Decimal(str(price_max)) if price_max is not None else None,
        status=PropertyStatus(status_filter) if status_filter else None,
        search=search,
        page=page,
        page_size=page_size,
    )

    service = _make_property_service(db)
    items, total = await service.list_properties(filters)

    total_pages = math.ceil(total / page_size) if total > 0 else 0
    request_id: str = getattr(request.state, "request_id", "")

    return PaginatedResponse(
        data=[PropertyListItem.model_validate(item) for item in items],
        pagination=PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
        meta=build_meta(request_id),
    )


# ── GET /properties/{id} ─────────────────────────────────────────────────────


@router.get(
    "/{property_id}",
    response_model=SuccessResponse[PropertyRead],
    status_code=status.HTTP_200_OK,
    summary="Get property detail",
    description="Fetch a property with full hierarchy (floors, rooms, beds, amenities, images).",
)
async def get_property(
    request: Request,
    property_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[PropertyRead]:
    service = _make_property_service(db)
    prop = await service.get_property_detail(property_id)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=PropertyRead.model_validate(prop),
        meta=build_meta(request_id),
    )


# ── PATCH /properties/{id} ───────────────────────────────────────────────────


@router.patch(
    "/{property_id}",
    response_model=SuccessResponse[PropertyRead],
    status_code=status.HTTP_200_OK,
    summary="Update property",
    description="Partially update a property. Only the owner can update.",
)
async def update_property(
    request: Request,
    property_id: uuid.UUID,
    data: PropertyUpdate,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[PropertyRead]:
    service = _make_property_service(db)
    prop = await service.update_property(property_id, current_user.id, data, db)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=PropertyRead.model_validate(prop),
        meta=build_meta(request_id),
    )


# ── DELETE /properties/{id} ──────────────────────────────────────────────────


@router.delete(
    "/{property_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete property",
    description="Soft-delete a property. Only the owner can delete.",
)
async def delete_property(
    request: Request,
    property_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = _make_property_service(db)
    await service.delete_property(property_id, current_user.id, db)
    request_id: str = getattr(request.state, "request_id", "")
    return MessageResponse(
        message="Property deleted successfully.",
        meta=build_meta(request_id),
    )


# ── POST /properties/{id}/status ─────────────────────────────────────────────


@router.post(
    "/{property_id}/status",
    response_model=SuccessResponse[PropertyRead],
    status_code=status.HTTP_200_OK,
    summary="Change property status",
    description="Update the property status (e.g., draft → active).",
)
async def update_property_status(
    request: Request,
    property_id: uuid.UUID,
    data: PropertyStatusUpdate,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[PropertyRead]:
    service = _make_property_service(db)
    prop = await service.update_status(property_id, current_user.id, data, db)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=PropertyRead.model_validate(prop),
        meta=build_meta(request_id),
    )


# ── POST /properties/{id}/refresh ────────────────────────────────────────────


@router.post(
    "/{property_id}/refresh",
    response_model=SuccessResponse[PropertyRead],
    status_code=status.HTTP_200_OK,
    summary="Refresh property listing",
    description="Update the last_refreshed_at timestamp to indicate listing is current.",
)
async def refresh_property(
    request: Request,
    property_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[PropertyRead]:
    service = _make_property_service(db)
    prop = await service.refresh_property(property_id, current_user.id, db)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=PropertyRead.model_validate(prop),
        meta=build_meta(request_id),
    )


# ── POST /properties/{id}/amenities ──────────────────────────────────────────


@router.post(
    "/{property_id}/amenities",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Attach amenities",
    description="Attach one or more amenities to a property.",
)
async def attach_amenities(
    request: Request,
    property_id: uuid.UUID,
    data: AmenityAttach,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = _make_property_service(db)
    await service.attach_amenities(property_id, current_user.id, data, db)
    request_id: str = getattr(request.state, "request_id", "")
    return MessageResponse(
        message="Amenities attached successfully.",
        meta=build_meta(request_id),
    )


# ── DELETE /properties/{id}/amenities/{amenity_id} ───────────────────────────


@router.delete(
    "/{property_id}/amenities/{amenity_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Detach amenity",
    description="Remove an amenity from a property.",
)
async def detach_amenity(
    request: Request,
    property_id: uuid.UUID,
    amenity_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = _make_property_service(db)
    await service.detach_amenity(property_id, amenity_id, current_user.id, db)
    request_id: str = getattr(request.state, "request_id", "")
    return MessageResponse(
        message="Amenity detached successfully.",
        meta=build_meta(request_id),
    )


# ── GET /properties/{id}/images ──────────────────────────────────────────────


@router.get(
    "/{property_id}/images",
    response_model=SuccessResponse[list[ImageRead]],
    status_code=status.HTTP_200_OK,
    summary="List property images",
    description="Fetch all images for a property.",
)
async def list_images(
    request: Request,
    property_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[list[ImageRead]]:
    service = _make_image_service(db)
    images = await service.list_images(property_id)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=[ImageRead.model_validate(img) for img in images],
        meta=build_meta(request_id),
    )


# ── POST /properties/{id}/images ─────────────────────────────────────────────


@router.post(
    "/{property_id}/images",
    response_model=SuccessResponse[ImageRead],
    status_code=status.HTTP_201_CREATED,
    summary="Upload image",
    description="Upload an image for a property (max 50MB, jpg/png/webp).",
)
async def upload_image(
    request: Request,
    property_id: uuid.UUID,
    file: UploadFile = File(...),
    entity_type: str = Query(default="property"),
    entity_id: uuid.UUID | None = Query(default=None),
    current_user: Annotated[User, Depends(require_owner)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> SuccessResponse[ImageRead]:
    service = _make_image_service(db)
    file_bytes = await file.read()

    # Default entity_id to property_id if not specified
    resolved_entity_id = entity_id if entity_id else property_id

    image = await service.upload_image(
        property_id=property_id,
        owner_id=current_user.id,
        entity_type=entity_type,
        entity_id=resolved_entity_id,
        file_bytes=file_bytes,
        filename=file.filename or "image.jpg",
        content_type=file.content_type or "image/jpeg",
        db=db,
    )
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=ImageRead.model_validate(image),
        meta=build_meta(request_id),
    )


# ── PATCH /properties/{id}/images/{image_id} ─────────────────────────────────


@router.patch(
    "/{property_id}/images/{image_id}",
    response_model=SuccessResponse[ImageRead],
    status_code=status.HTTP_200_OK,
    summary="Update image metadata",
    description="Update alt_text or set as primary image.",
)
async def update_image(
    request: Request,
    property_id: uuid.UUID,
    image_id: uuid.UUID,
    data: ImageUpdate,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[ImageRead]:
    service = _make_image_service(db)
    image = await service.update_image(image_id, property_id, current_user.id, data, db)
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=ImageRead.model_validate(image),
        meta=build_meta(request_id),
    )


# ── DELETE /properties/{id}/images/{image_id} ────────────────────────────────


@router.delete(
    "/{property_id}/images/{image_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete image",
    description="Soft-delete an image and remove from storage.",
)
async def delete_image(
    request: Request,
    property_id: uuid.UUID,
    image_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = _make_image_service(db)
    await service.delete_image(image_id, property_id, current_user.id, db)
    request_id: str = getattr(request.state, "request_id", "")
    return MessageResponse(
        message="Image deleted successfully.",
        meta=build_meta(request_id),
    )


# ── POST /properties/{id}/images/reorder ─────────────────────────────────────


@router.post(
    "/{property_id}/images/reorder",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reorder images",
    description="Batch update sort_order for property images.",
)
async def reorder_images(
    request: Request,
    property_id: uuid.UUID,
    data: ImageReorder,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = _make_image_service(db)
    await service.reorder_images(property_id, current_user.id, data, db)
    request_id: str = getattr(request.state, "request_id", "")
    return MessageResponse(
        message="Images reordered successfully.",
        meta=build_meta(request_id),
    )


# ── POST /properties/{id}/save ───────────────────────────────────────────────


@router.post(
    "/{property_id}/save",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save to wishlist",
    description="Save a property to the student's wishlist.",
)
async def save_property(
    request: Request,
    property_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = _make_property_service(db)
    await service.save_property(current_user.id, property_id, db)
    request_id: str = getattr(request.state, "request_id", "")
    return MessageResponse(
        message="Property saved to wishlist.",
        meta=build_meta(request_id),
    )


# ── DELETE /properties/{id}/save ─────────────────────────────────────────────


@router.delete(
    "/{property_id}/save",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove from wishlist",
    description="Remove a property from the student's wishlist.",
)
async def unsave_property(
    request: Request,
    property_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = _make_property_service(db)
    await service.unsave_property(current_user.id, property_id, db)
    request_id: str = getattr(request.state, "request_id", "")
    return MessageResponse(
        message="Property removed from wishlist.",
        meta=build_meta(request_id),
    )
