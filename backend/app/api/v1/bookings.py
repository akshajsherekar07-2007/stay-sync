"""Booking API endpoints.

All routes are mounted at /api/v1/bookings by the v1 router.

Endpoints
---------
POST   /bookings/from-hold/{hold_id}  → Convert hold to booking (Owner)
POST   /bookings/direct               → Create direct booking (Owner)
GET    /bookings/me                   → List my bookings (Student)
GET    /bookings/property/{prop_id}   → List bookings for my property (Owner)
GET    /bookings/{id}                 → Get booking details (Shared)
POST   /bookings/{id}/vacate          → Mark booking vacated (Owner)
POST   /bookings/{id}/cancel          → Cancel booking (Owner)
"""

from __future__ import annotations

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import BookingStatus, UserRole
from app.core.exceptions import ForbiddenException
from app.dependencies.auth import get_current_user, require_owner, require_student
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.bed_repository import BedRepository
from app.repositories.booking_repository import BookingRepository
from app.repositories.hold_request_repository import HoldRequestRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.property_repository import PropertyRepository
from app.repositories.user_repository import UserRepository
from app.repositories.waitlist_entry_repository import WaitlistEntryRepository
from app.schemas.booking import BookingCreate, BookingRead
from app.schemas.common import (
    PaginatedResponse,
    PaginationInfo,
    SuccessResponse,
    build_meta,
)
from app.services.audit_service import AuditService
from app.services.booking_service import BookingService
from app.services.notification_service import NotificationService
from app.services.waitlist_service import WaitlistService

router = APIRouter()


def _make_booking_service(db: AsyncSession) -> BookingService:
    audit_service = AuditService(AuditLogRepository(db))
    notification_service = NotificationService(NotificationRepository(db))
    
    waitlist_service = WaitlistService(
        waitlist_repo=WaitlistEntryRepository(db),
        bed_repo=BedRepository(db),
        hold_repo=HoldRequestRepository(db),
        audit_service=audit_service,
    )

    return BookingService(
        booking_repo=BookingRepository(db),
        hold_repo=HoldRequestRepository(db),
        bed_repo=BedRepository(db),
        property_repo=PropertyRepository(db),
        waitlist_service=waitlist_service,
        notification_service=notification_service,
        audit_service=audit_service,
        user_repo=UserRepository(db),
    )


@router.post(
    "/from-hold/{hold_id}",
    response_model=SuccessResponse[BookingRead],
    status_code=status.HTTP_201_CREATED,
    summary="Convert hold to booking",
)
async def create_from_hold(
    request: Request,
    hold_id: uuid.UUID,
    data: BookingCreate,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[BookingRead]:
    service = _make_booking_service(db)
    
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    booking = await service.create_from_hold(
        hold_id=hold_id,
        owner_id=current_user.id,
        check_in_date=data.check_in_date,
        check_out_date=data.check_out_date,
        notes=data.notes,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    await db.commit()
    
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=BookingRead.model_validate(booking),
        meta=build_meta(request_id),
    )


@router.post(
    "/direct",
    response_model=SuccessResponse[BookingRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create direct booking",
)
async def create_direct(
    request: Request,
    data: BookingCreate,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
    student_id: uuid.UUID = Query(..., description="Target student for the booking"),
) -> SuccessResponse[BookingRead]:
    service = _make_booking_service(db)
    
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    booking = await service.create_direct(
        bed_id=data.bed_id,
        student_id=student_id,
        owner_id=current_user.id,
        check_in_date=data.check_in_date,
        check_out_date=data.check_out_date,
        notes=data.notes,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    await db.commit()
    
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=BookingRead.model_validate(booking),
        meta=build_meta(request_id),
    )


@router.get(
    "/me",
    response_model=PaginatedResponse[BookingRead],
    summary="List my bookings",
)
async def list_my_bookings(
    request: Request,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: BookingStatus | None = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[BookingRead]:
    service = _make_booking_service(db)
    items, total = await service.list_student_bookings(
        current_user.id, status=status_filter, page=page, page_size=page_size
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    request_id: str = getattr(request.state, "request_id", "")
    
    return PaginatedResponse(
        data=[BookingRead.model_validate(item) for item in items],
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


@router.get(
    "/property/{property_id}",
    response_model=PaginatedResponse[BookingRead],
    summary="List bookings for my property",
)
async def list_property_bookings(
    request: Request,
    property_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: BookingStatus | None = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[BookingRead]:
    service = _make_booking_service(db)
    items, total = await service.list_property_bookings(
        property_id, current_user.id, status=status_filter, page=page, page_size=page_size
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    request_id: str = getattr(request.state, "request_id", "")
    
    return PaginatedResponse(
        data=[BookingRead.model_validate(item) for item in items],
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


@router.get(
    "/{booking_id}",
    response_model=SuccessResponse[BookingRead],
    summary="Get booking details",
)
async def get_booking(
    request: Request,
    booking_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[BookingRead]:
    service = _make_booking_service(db)
    booking = await service.get_booking(booking_id)

    # Authorization Check
    if current_user.role == UserRole.STUDENT.value:
        if booking.student_id != current_user.id:
            raise ForbiddenException(message="You can only view your own bookings.", code="NOT_BOOKING_OWNER")
    elif current_user.role == UserRole.OWNER.value:
        prop_repo = PropertyRepository(db)
        prop = await prop_repo.get(booking.property_id)
        if prop is None or prop.owner_id != current_user.id:
            raise ForbiddenException(message="You can only view bookings for your properties.", code="NOT_PROPERTY_OWNER")

    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=BookingRead.model_validate(booking),
        meta=build_meta(request_id),
    )


@router.post(
    "/{booking_id}/vacate",
    response_model=SuccessResponse[BookingRead],
    summary="Mark booking vacated",
)
async def vacate_booking(
    request: Request,
    booking_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[BookingRead]:
    service = _make_booking_service(db)
    
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    booking = await service.vacate(
        booking_id=booking_id,
        owner_id=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    await db.commit()
    
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=BookingRead.model_validate(booking),
        meta=build_meta(request_id),
    )


@router.post(
    "/{booking_id}/cancel",
    response_model=SuccessResponse[BookingRead],
    summary="Cancel booking",
)
async def cancel_booking(
    request: Request,
    booking_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[BookingRead]:
    service = _make_booking_service(db)
    
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    booking = await service.cancel(
        booking_id=booking_id,
        owner_id=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    await db.commit()
    
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=BookingRead.model_validate(booking),
        meta=build_meta(request_id),
    )
