"""Celery tasks for expired token cleanup and stale listing detection.

Bridges synchronous Celery worker processes with the async database/service
layers using ``asyncio.run()``. Follows the established hold_tasks pattern
with isolated sessions, caller commits, and fail-safe error wrapping.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import NotificationType, PropertyStatus
from app.db.session import _get_session_factory
from app.models.property import Property
from app.models.user import User

logger = logging.getLogger(__name__)


# ── Session & Wiring Helpers ──────────────────────────────────────────────────

def _new_async_session() -> AsyncSession:
    """Create a fresh async session for database queries."""
    factory = _get_session_factory()
    return factory()


def _build_maintenance_services(session: AsyncSession):
    """Wire up all required repositories and services for maintenance tasks."""
    from app.repositories.refresh_token_repository import RefreshTokenRepository
    from app.repositories.property_repository import PropertyRepository
    from app.repositories.audit_log_repository import AuditLogRepository
    from app.repositories.notification_repository import NotificationRepository

    from app.services.audit_service import AuditService
    from app.services.notification_service import NotificationService

    # Repositories
    refresh_repo = RefreshTokenRepository(session)
    property_repo = PropertyRepository(session)
    audit_repo = AuditLogRepository(session)
    notif_repo = NotificationRepository(session)

    # Services
    audit_service = AuditService(audit_repo)
    notification_service = NotificationService(notif_repo)

    return refresh_repo, property_repo, audit_service, notification_service


# ── Task 1: Expired Token Cleanup ─────────────────────────────────────────────

@shared_task(
    bind=True,
    name="maintenance.cleanup_expired_tokens",
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def cleanup_expired_tokens_task(self) -> dict:
    """Hard-delete all expired refresh tokens from the database.

    Returns:
        dict: Summary payload showing number of cleaned tokens.
    """
    try:
        return asyncio.run(_cleanup_expired_tokens_async())
    except Exception as exc:
        logger.exception("cleanup_expired_tokens_task failed")
        raise self.retry(exc=exc)


async def _cleanup_expired_tokens_async() -> dict:
    """Async implementation for token cleanup task."""
    session = _new_async_session()
    try:
        refresh_repo, *_ = _build_maintenance_services(session)
        deleted_count = await refresh_repo.delete_expired()
        await session.commit()

        logger.info("Token cleanup complete. Deleted %d expired tokens.", deleted_count)
        return {
            "status": "ok",
            "deleted_count": deleted_count,
        }
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# ── Task 2: Stale Listing Detection ───────────────────────────────────────────

@shared_task(
    bind=True,
    name="maintenance.detect_stale_listings",
    max_retries=2,
    default_retry_delay=60,
    acks_late=True,
)
def detect_stale_listings_task(self) -> dict:
    """Scan active property listings and deactivate stale ones.

    Returns:
        dict: Summary payload showing counts of processed listings.
    """
    try:
        return asyncio.run(_detect_stale_listings_async())
    except Exception as exc:
        logger.exception("detect_stale_listings_task failed")
        raise self.retry(exc=exc)


async def _detect_stale_listings_async() -> dict:
    """Async implementation for stale listing deactivation."""
    session = _new_async_session()
    settings = get_settings()
    threshold_days = settings.PROPERTY_STALE_THRESHOLD_DAYS

    processed_count = 0
    failed_count = 0

    try:
        (
            _,
            property_repo,
            audit_service,
            notification_service,
        ) = _build_maintenance_services(session)

        # 1. Fetch properties that are Active and have not been refreshed/updated
        # for more than threshold_days.
        now = datetime.now(tz=timezone.utc)
        limit_date = now - timedelta(days=threshold_days)

        # We query properties where status = 'active' and last_refreshed_at < limit_date
        # (or updated_at < limit_date if last_refreshed_at is NULL).
        stmt = (
            select(Property)
            .where(Property.status == PropertyStatus.ACTIVE.value)
            .where(Property.deleted_at.is_(None))
            .where(
                (
                    (Property.last_refreshed_at.isnot(None))
                    & (Property.last_refreshed_at < limit_date)
                )
                | (
                    (Property.last_refreshed_at.is_(None))
                    & (Property.updated_at < limit_date)
                )
            )
        )

        res = await session.execute(stmt)
        stale_properties = list(res.scalars().all())

        if not stale_properties:
            logger.info("detect_stale_listings: no stale listings found.")
            return {
                "status": "ok",
                "stale_count": 0,
                "deactivated_count": 0,
                "failed_count": 0,
            }

        logger.info("detect_stale_listings: found %d stale listings.", len(stale_properties))

        for prop in stale_properties:
            try:
                # Store old status state for audit trail snapshot
                old_status = prop.status

                # Deactivate property
                prop.status = PropertyStatus.INACTIVE.value
                session.add(prop)

                # Log audit action
                await audit_service.log_action(
                    action="property_marked_stale",
                    entity_type="property",
                    entity_id=prop.id,
                    user_id=None,  # system-initiated
                    old_data={"status": old_status, "last_refreshed_at": prop.last_refreshed_at.isoformat() if prop.last_refreshed_at else None},
                    new_data={"status": prop.status},
                    ip_address="celery-worker",
                    user_agent="StaySync Celery Worker",
                )

                # Create database in-app notification for the owner
                await notification_service._notification_repo.create(
                    user_id=prop.owner_id,
                    type=NotificationType.SYSTEM_ANNOUNCEMENT,
                    title="Listing Deactivated",
                    message=(
                        f"Your property listing '{prop.name}' has been marked as inactive "
                        f"because it hasn't been updated or refreshed for {threshold_days} days."
                    ),
                    data={"property_id": str(prop.id)},
                )

                processed_count += 1
            except Exception:
                logger.exception("Failed to process stale listing deactivation for property %s", prop.id)
                failed_count += 1

        # Save all state changes and logs
        await session.commit()

        logger.info(
            "detect_stale_listings complete: deactivated=%d failed=%d",
            processed_count,
            failed_count,
        )
        return {
            "status": "ok",
            "stale_count": len(stale_properties),
            "deactivated_count": processed_count,
            "failed_count": failed_count,
        }

    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
