"""Waitlist API endpoints.

All routes are mounted at /api/v1/waitlists by the v1 router.

Endpoints
---------
POST   /waitlists                      → Join waitlist (Student)
GET    /waitlists/me                   → List my waitlist entries (Student)
GET    /waitlists/bed/{bed_id}         → View active queue for bed (Owner)
GET    /waitlists/bed/{bed_id}/position→ Get my queue position (Student)
POST   /waitlists/{id}/cancel          → Cancel my entry (Student)
"""

from __future__ import annotations

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user, require_owner, require_student
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.bed_repository import BedRepository
from app.repositories.hold_request_repository import HoldRequestRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.waitlist_entry_repository import WaitlistEntryRepository
from app.schemas.common import (
    PaginatedResponse,
    PaginationInfo,
    SuccessResponse,
    build_meta,
)
from app.schemas.waitlist_entry import WaitlistEntryCreate, WaitlistEntryRead
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.waitlist_service import WaitlistService

router = APIRouter()


def _make_waitlist_service(db: AsyncSession) -> WaitlistService:
    return WaitlistService(
        waitlist_repo=WaitlistEntryRepository(db),
        bed_repo=BedRepository(db),
        hold_repo=HoldRequestRepository(db),
        notification_service=NotificationService(NotificationRepository(db)),
        audit_service=AuditService(AuditLogRepository(db)),
    )


@router.post(
    "",
    response_model=SuccessResponse[WaitlistEntryRead],
    status_code=status.HTTP_201_CREATED,
    summary="Join waitlist",
)
async def join_waitlist(
    request: Request,
    data: WaitlistEntryCreate,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[WaitlistEntryRead]:
    service = _make_waitlist_service(db)
    
    # We need property_id, which we fetch from the bed repo inside the service or here.
    # The service expects property_id. Wait, `add_to_waitlist` takes `property_id`.
    # Let's let the service look it up if we don't have it, but waitlist_service
    # signature: async def add_to_waitlist(..., property_id: uuid.UUID) -> WaitlistEntry
    # Let's just fetch bed here to get property_id, or we could let the hold_service
    # logic handle it. Wait, the `add_to_waitlist` signature in WaitlistService is:
    # `add_to_waitlist(self, bed_id: uuid.UUID, student_id: uuid.UUID, property_id: uuid.UUID)`
    
    bed_repo = BedRepository(db)
    bed = await bed_repo.get(data.bed_id)
    if bed is None:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(message="Bed not found.", code="BED_NOT_FOUND")

    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    entry = await service.add_to_waitlist(
        bed_id=data.bed_id,
        student_id=current_user.id,
        property_id=bed.property_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    await db.commit()
    
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=WaitlistEntryRead.model_validate(entry),
        meta=build_meta(request_id),
    )


@router.get(
    "/me",
    response_model=PaginatedResponse[WaitlistEntryRead],
    summary="List my waitlist entries",
)
async def list_my_entries(
    request: Request,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[WaitlistEntryRead]:
    service = _make_waitlist_service(db)
    items, total = await service.list_student_entries(
        current_user.id, page=page, page_size=page_size
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    request_id: str = getattr(request.state, "request_id", "")
    
    return PaginatedResponse(
        data=[WaitlistEntryRead.model_validate(item) for item in items],
        pagination=PaginationInfo(
            total_items=total,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
            has_next=page < total_pages,
            has_previous=page > 1,
        ),
        meta=build_meta(request_id),
    )


@router.get(
    "/bed/{bed_id}",
    response_model=SuccessResponse[list[WaitlistEntryRead]],
    summary="View active queue for bed",
)
async def list_bed_queue(
    request: Request,
    bed_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[list[WaitlistEntryRead]]:
    service = _make_waitlist_service(db)
    # The service `list_bed_queue` verifies ownership implicitly or we should explicitly verify
    # Let's check `list_bed_queue` signature: async def list_bed_queue(self, bed_id: uuid.UUID)
    # It does not take owner_id. So we must verify ownership.
    bed_repo = BedRepository(db)
    bed = await bed_repo.get(bed_id)
    from app.core.exceptions import NotFoundException, ForbiddenException
    if bed is None:
        raise NotFoundException(message="Bed not found.", code="BED_NOT_FOUND")
        
    from app.repositories.property_repository import PropertyRepository
    prop_repo = PropertyRepository(db)
    prop = await prop_repo.get(bed.property_id)
    if prop is None or prop.owner_id != current_user.id:
        raise ForbiddenException(message="You do not own this property.", code="NOT_PROPERTY_OWNER")

    items = await service.list_bed_queue(bed_id)
    
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=[WaitlistEntryRead.model_validate(item) for item in items],
        meta=build_meta(request_id),
    )


@router.get(
    "/bed/{bed_id}/position",
    response_model=SuccessResponse[dict[str, int]],
    summary="Get my queue position",
)
async def get_queue_position(
    request: Request,
    bed_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[dict[str, int]]:
    service = _make_waitlist_service(db)
    position = await service.get_queue_position(bed_id, current_user.id)
    
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data={"position": position},
        meta=build_meta(request_id),
    )


@router.post(
    "/{entry_id}/cancel",
    response_model=SuccessResponse[WaitlistEntryRead],
    summary="Cancel my entry",
)
async def cancel_entry(
    request: Request,
    entry_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[WaitlistEntryRead]:
    service = _make_waitlist_service(db)
    
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    entry = await service.cancel_entry(
        entry_id,
        student_id=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    await db.commit()
    
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=WaitlistEntryRead.model_validate(entry),
        meta=build_meta(request_id),
    )
