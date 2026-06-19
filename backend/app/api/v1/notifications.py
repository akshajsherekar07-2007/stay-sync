"""Notification API endpoints.

All routes are mounted at /api/v1/notifications by the v1 router.

Endpoints
---------
GET    /notifications                 → List my notifications
GET    /notifications/unread-count    → Get unread badge count
POST   /notifications/{id}/read       → Mark single as read
POST   /notifications/read-all        → Mark all as read
"""

from __future__ import annotations

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas.common import (
    MessageResponse,
    PaginatedResponse,
    PaginationInfo,
    SuccessResponse,
    build_meta,
)
from app.schemas.notification import NotificationRead
from app.services.notification_service import NotificationService

router = APIRouter()


def _make_notification_service(db: AsyncSession) -> NotificationService:
    return NotificationService(notification_repo=NotificationRepository(db))


@router.get(
    "",
    response_model=PaginatedResponse[NotificationRead],
    summary="List my notifications",
)
async def list_notifications(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    unread_only: bool = Query(False, description="Filter to only unread notifications"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[NotificationRead]:
    service = _make_notification_service(db)
    items, total = await service.list_notifications(
        current_user.id,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    request_id: str = getattr(request.state, "request_id", "")
    
    return PaginatedResponse(
        data=[NotificationRead.model_validate(item) for item in items],
        pagination=PaginationInfo(
            total_items=total,
            total_pages=total_pages,
            page=page,
            page_size=page_size,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
        meta=build_meta(request_id),
    )


@router.get(
    "/unread-count",
    response_model=SuccessResponse[dict[str, int]],
    summary="Get unread badge count",
)
async def get_unread_count(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[dict[str, int]]:
    service = _make_notification_service(db)
    count = await service.count_unread(current_user.id)
    
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data={"unread_count": count},
        meta=build_meta(request_id),
    )


@router.post(
    "/{notification_id}/read",
    response_model=SuccessResponse[NotificationRead],
    summary="Mark single notification as read",
)
async def mark_as_read(
    request: Request,
    notification_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[NotificationRead]:
    service = _make_notification_service(db)
    
    notification = await service._notification_repo.get(notification_id)
    if not notification:
        raise NotFoundException(
            message="Notification not found.",
            code="NOTIFICATION_NOT_FOUND",
        )
        
    if notification.user_id != current_user.id:
        raise ForbiddenException(
            message="You do not own this notification.",
            code="NOT_NOTIFICATION_OWNER",
        )
        
    if not notification.is_read:
        notification = await service.mark_as_read(notification_id)
    
    # Phase 2 services use flush-only, so we commit here.
    await db.commit()
    
    request_id: str = getattr(request.state, "request_id", "")
    return SuccessResponse(
        data=NotificationRead.model_validate(notification),
        meta=build_meta(request_id),
    )


@router.post(
    "/read-all",
    response_model=MessageResponse,
    summary="Mark all notifications as read",
)
async def mark_all_as_read(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = _make_notification_service(db)
    count = await service.mark_all_as_read(current_user.id)
    
    # Phase 2 services use flush-only, so we commit here.
    await db.commit()
    
    request_id: str = getattr(request.state, "request_id", "")
    return MessageResponse(
        message=f"Marked {count} notifications as read.",
        meta=build_meta(request_id),
    )


@router.delete(
    "/clear-all",
    response_model=MessageResponse,
    summary="Clear all notifications",
)
async def clear_all_notifications(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = _make_notification_service(db)
    count = await service.clear_all_notifications(current_user.id)
    
    await db.commit()
    
    request_id: str = getattr(request.state, "request_id", "")
    return MessageResponse(
        message=f"Cleared {count} notifications.",
        meta=build_meta(request_id),
    )
