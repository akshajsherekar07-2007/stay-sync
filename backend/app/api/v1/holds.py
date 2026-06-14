"""Hold API endpoints.

All routes are mounted at /api/v1/holds by the v1 router.

Endpoints
---------
POST   /holds                          → Request a new hold (Student)
GET    /holds/me                       → List my holds (Student)
GET    /holds/property/{prop_id}       → List holds for my property (Owner)
GET    /holds/{id}                     → Get hold details (Shared)
POST   /holds/{id}/approve             → Approve pending hold (Owner)
POST   /holds/{id}/reject              → Reject pending hold (Owner)
POST   /holds/{id}/cancel              → Cancel my hold (Student)
POST   /holds/{id}/override            → Override hold for diff student (Owner)
"""

from __future__ import annotations

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import HoldStatus, UserRole
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
from app.repositories.waitlist_entry_repository import WaitlistEntryRepository
from app.schemas.common import (
    PaginatedResponse,
    PaginationInfo,
    SuccessResponse,
    build_meta,
)
from app.schemas.hold_request import HoldRequestCreate, HoldRequestRead, HoldRequestUpdate
from app.services.audit_service import AuditService
from app.services.hold_service import HoldService
from app.services.notification_service import NotificationService
from app.services.waitlist_service import WaitlistService

router = APIRouter()


def _make_hold_service(db: AsyncSession) -> tuple[HoldService, WaitlistService]:
    audit_service = AuditService(AuditLogRepository(db))
    notification_service = NotificationService(NotificationRepository(db))
    
    waitlist_service = WaitlistService(
        waitlist_repo=WaitlistEntryRepository(db),
        bed_repo=BedRepository(db),
        hold_repo=HoldRequestRepository(db),
        notification_service=notification_service,
        audit_service=audit_service,
    )

    hold_service = HoldService(
        hold_repo=HoldRequestRepository(db),
        bed_repo=BedRepository(db),
        booking_repo=BookingRepository(db),
        property_repo=PropertyRepository(db),
        waitlist_service=waitlist_service,
        notification_service=notification_service,
        audit_service=audit_service,
    )
    
    return hold_service, waitlist_service


@router.post(
    "",
    summary="Request a new hold",
    responses={
        201: {"description": "Hold created"},
        202: {"description": "Added to waitlist instead"},
    }
)
async def request_hold(
    request: Request,
    data: HoldRequestCreate,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service, waitlist_service = _make_hold_service(db)
    
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    hold = await service.request_hold(
        bed_id=data.bed_id,
        student_id=current_user.id,
        hold_duration_hours=data.hold_duration_hours,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    await db.commit()
    
    request_id: str = getattr(request.state, "request_id", "")
    meta = build_meta(request_id)
    
    if hold is None:
        # Fallback to waitlist (Decision #2)
        # Fetch queue position
        position = await waitlist_service.get_queue_position(data.bed_id, current_user.id)
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": "waitlisted",
                "message": "The bed is currently held. You have been added to the waitlist.",
                "data": {"position": position},
                "meta": meta,
            }
        )

    # 201 Created
    response = SuccessResponse(data=HoldRequestRead.model_validate(hold), meta=meta)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=response.model_dump(mode="json"),
    )


@router.get(
    "/me",
    response_model=PaginatedResponse[HoldRequestRead],
    summary="List my holds",
)
async def list_my_holds(
    request: Request,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: HoldStatus | None = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[HoldRequestRead]:
    service, _ = _make_hold_service(db)
    items, total = await service.list_student_holds(
        current_user.id, status=status_filter, page=page, page_size=page_size
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    request_id: str = getattr(request.state, "request_id", "")
    
    return PaginatedResponse(
        data=[HoldRequestRead.model_validate(item) for item in items],
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
    "/property/{property_id}",
    response_model=PaginatedResponse[HoldRequestRead],
    summary="List holds for my property",
)
async def list_property_holds(
    request: Request,
    property_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: HoldStatus | None = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[HoldRequestRead]:
    service, _ = _make_hold_service(db)
    items, total = await service.list_property_holds(
        property_id, current_user.id, status=status_filter, page=page, page_size=page_size
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    request_id: str = getattr(request.state, "request_id", "")
    
    return PaginatedResponse(
        data=[HoldRequestRead.model_validate(item) for item in items],
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
    "/{hold_id}",
    response_model=SuccessResponse[HoldRequestRead],
    summary="Get hold details",
)
async def get_hold(
    request: Request,
    hold_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[HoldRequestRead]:
    service, _ = _make_hold_service(db)
    hold = await service.get_hold(hold_id)

    # Authorization Check
    if current_user.role == UserRole.STUDENT.value:
        if hold.student_id != current_user.id:
            raise ForbiddenException(message="You can only view your own holds.", code="NOT_HOLD_OWNER")
    elif current_user.role == UserRole.OWNER.value:
        prop_repo = PropertyRepository(db)
        prop = await prop_repo.get(hold.property_id)
        if prop is None or prop.owner_id != current_user.id:
            raise ForbiddenException(message="You can only view holds for your properties.", code="NOT_PROPERTY_OWNER")

    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=HoldRequestRead.model_validate(hold),
        meta=build_meta(request_id),
    )


@router.post(
    "/{hold_id}/approve",
    response_model=SuccessResponse[HoldRequestRead],
    summary="Approve pending hold",
)
async def approve_hold(
    request: Request,
    hold_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[HoldRequestRead]:
    service, _ = _make_hold_service(db)
    
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    hold = await service.approve_hold(
        hold_id=hold_id,
        owner_id=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    await db.commit()
    
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=HoldRequestRead.model_validate(hold),
        meta=build_meta(request_id),
    )


@router.post(
    "/{hold_id}/reject",
    response_model=SuccessResponse[HoldRequestRead],
    summary="Reject pending hold",
)
async def reject_hold(
    request: Request,
    hold_id: uuid.UUID,
    data: HoldRequestUpdate,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[HoldRequestRead]:
    service, _ = _make_hold_service(db)
    
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    hold = await service.reject_hold(
        hold_id=hold_id,
        owner_id=current_user.id,
        resolution_note=data.resolution_note,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    await db.commit()
    
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=HoldRequestRead.model_validate(hold),
        meta=build_meta(request_id),
    )


@router.post(
    "/{hold_id}/cancel",
    response_model=SuccessResponse[HoldRequestRead],
    summary="Cancel my hold",
)
async def cancel_hold(
    request: Request,
    hold_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[HoldRequestRead]:
    service, _ = _make_hold_service(db)
    
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    hold = await service.cancel_hold(
        hold_id=hold_id,
        student_id=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    await db.commit()
    
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=HoldRequestRead.model_validate(hold),
        meta=build_meta(request_id),
    )


@router.post(
    "/{hold_id}/override",
    summary="Override hold for a different student",
)
async def override_hold(
    request: Request,
    hold_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
    target_student_id: uuid.UUID = Query(..., description="Student to book for"),
    check_in_date: str | None = Query(None, description="YYYY-MM-DD"),
    check_out_date: str | None = Query(None, description="YYYY-MM-DD"),
    notes: str | None = Query(None, description="Booking notes"),
):
    from datetime import date
    
    service, _ = _make_hold_service(db)
    
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    ci_date = date.fromisoformat(check_in_date) if check_in_date else None
    co_date = date.fromisoformat(check_out_date) if check_out_date else None

    hold, booking = await service.override_hold(
        hold_id=hold_id,
        owner_id=current_user.id,
        target_student_id=target_student_id,
        check_in_date=ci_date,
        check_out_date=co_date,
        notes=notes,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    await db.commit()
    
    from app.schemas.booking import BookingRead
    
    request_id: str = getattr(request.state, "request_id", "")
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "data": {
                "hold": HoldRequestRead.model_validate(hold).model_dump(mode="json"),
                "booking": BookingRead.model_validate(booking).model_dump(mode="json"),
            },
            "meta": build_meta(request_id),
        }
    )
