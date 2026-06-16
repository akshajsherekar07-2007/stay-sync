"""Celery tasks for hold request expiry and expiring-soon notifications.

Bridges the synchronous Celery worker with the async service layer by
running coroutines via ``asyncio.run()``.  Each task creates its own
``AsyncSession``, wires repositories and services, executes the business
logic, and commits the transaction — fulfilling the Phase 2 convention
that the *caller* commits.

Tasks
-----
expire_hold_task(hold_id)
    Expire a single approved hold that has passed its ``expires_at``.

scan_and_expire_holds_task()
    Bulk-scan for all expired approved holds and expire each one.

send_expiring_soon_notifications_task()
    Notify students whose holds expire within the warning threshold.
    Uses Redis SETNX deduplication (Phase 2.2.4) to ensure at most one
    notification per hold per warning window.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from celery import shared_task
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import HOLD_EXPIRY_WARNING_MINUTES
from app.db.session import _get_session_factory

logger = logging.getLogger(__name__)


# ── Async session helper ──────────────────────────────────────────────────────

def _new_async_session() -> AsyncSession:
    """Create a fresh async session for use inside a Celery task.

    Uses the same session factory as FastAPI (same engine, same pool).
    The caller is responsible for committing and closing.
    """
    factory = _get_session_factory()
    return factory()


# ── Service wiring ────────────────────────────────────────────────────────────
# Constructed per-task inside the async context to avoid cross-thread sharing.
# Imports are at function level to prevent circular imports at module load.

def _build_hold_service(session: AsyncSession):
    """Wire HoldService with all its repository and service dependencies."""
    from app.repositories.bed_repository import BedRepository
    from app.repositories.booking_repository import BookingRepository
    from app.repositories.hold_request_repository import HoldRequestRepository
    from app.repositories.property_repository import PropertyRepository
    from app.repositories.audit_log_repository import AuditLogRepository
    from app.repositories.notification_repository import NotificationRepository
    from app.repositories.waitlist_entry_repository import WaitlistEntryRepository

    from app.services.audit_service import AuditService
    from app.services.notification_service import NotificationService
    from app.services.waitlist_service import WaitlistService
    from app.services.hold_service import HoldService

    # Repositories
    hold_repo = HoldRequestRepository(session)
    bed_repo = BedRepository(session)
    booking_repo = BookingRepository(session)
    property_repo = PropertyRepository(session)
    audit_log_repo = AuditLogRepository(session)
    notification_repo = NotificationRepository(session)
    waitlist_repo = WaitlistEntryRepository(session)

    # Services
    audit_service = AuditService(audit_log_repo)
    notification_service = NotificationService(notification_repo)
    waitlist_service = WaitlistService(
        waitlist_repo=waitlist_repo,
        hold_repo=hold_repo,
        bed_repo=bed_repo,
        audit_service=audit_service,
    )
    hold_service = HoldService(
        hold_repo=hold_repo,
        bed_repo=bed_repo,
        booking_repo=booking_repo,
        property_repo=property_repo,
        waitlist_service=waitlist_service,
        notification_service=notification_service,
        audit_service=audit_service,
    )
    return hold_service, hold_repo, notification_service, property_repo, bed_repo


# ── Task 1: expire a single hold ─────────────────────────────────────────────

@shared_task(
    bind=True,
    name="hold.expire_single",
    max_retries=3,
    default_retry_delay=10,
    acks_late=True,
)
def expire_hold_task(self, hold_id: str) -> dict:
    """Expire a single approved hold by UUID.

    This is the targeted variant: a future Celery Beat schedule or
    ``apply_async(eta=...)`` will dispatch this at the hold's
    ``expires_at`` time.

    Args:
        hold_id: String UUID of the hold request to expire.

    Returns:
        A dict summarising the outcome.
    """
    try:
        return asyncio.run(_expire_hold_async(hold_id))
    except Exception as exc:
        logger.exception("expire_hold_task failed for hold %s", hold_id)
        raise self.retry(exc=exc)


async def _expire_hold_async(hold_id: str) -> dict:
    """Async implementation for expiring a single hold."""
    parsed_id = uuid.UUID(hold_id)
    session = _new_async_session()

    try:
        hold_service, *_ = _build_hold_service(session)

        updated_hold = await hold_service.expire_hold(
            parsed_id,
            ip_address="celery-worker",
            user_agent="StaySync Celery Worker",
        )

        await session.commit()

        logger.info(
            "Hold %s expired successfully  bed=%s  student=%s",
            hold_id,
            updated_hold.bed_id,
            updated_hold.student_id,
        )
        return {
            "status": "expired",
            "hold_id": hold_id,
            "bed_id": str(updated_hold.bed_id),
        }

    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# ── Task 2: bulk scan and expire ─────────────────────────────────────────────

@shared_task(
    bind=True,
    name="hold.scan_and_expire",
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def scan_and_expire_holds_task(self) -> dict:
    """Scan for all approved holds past their ``expires_at`` and expire them.

    Designed to be called periodically (e.g. every minute via Celery Beat,
    implemented in a future phase).  Each hold is expired individually to
    preserve per-hold audit trails, notifications, and waitlist promotions.

    Returns:
        A dict with counts of expired / failed / total holds processed.
    """
    try:
        return asyncio.run(_scan_and_expire_async())
    except Exception as exc:
        logger.exception("scan_and_expire_holds_task failed")
        raise self.retry(exc=exc)


async def _scan_and_expire_async() -> dict:
    """Async implementation for the bulk scan-and-expire flow."""
    session = _new_async_session()
    expired_count = 0
    failed_count = 0
    hold_ids: list[str] = []

    try:
        # 1. Discover expired holds
        _, hold_repo, *_ = _build_hold_service(session)
        now = datetime.now(tz=timezone.utc)
        expired_holds = await hold_repo.list_expired_approved(now)

        if not expired_holds:
            logger.info("scan_and_expire: no expired holds found")
            return {"status": "ok", "total": 0, "expired": 0, "failed": 0}

        hold_ids = [str(h.id) for h in expired_holds]
        logger.info("scan_and_expire: found %d expired holds", len(hold_ids))

    finally:
        await session.close()

    # 2. Expire each hold in its own session/transaction for isolation
    for hid in hold_ids:
        try:
            await _expire_hold_async(hid)
            expired_count += 1
        except Exception:
            logger.exception("scan_and_expire: failed to expire hold %s", hid)
            failed_count += 1

    result = {
        "status": "ok",
        "total": len(hold_ids),
        "expired": expired_count,
        "failed": failed_count,
    }
    logger.info("scan_and_expire complete: %s", result)
    return result


# ── Task 3: expiring-soon notifications ──────────────────────────────────────

@shared_task(
    bind=True,
    name="hold.send_expiring_soon_notifications",
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def send_expiring_soon_notifications_task(self) -> dict:
    """Notify students whose approved holds expire within the warning window.

    The warning threshold is configured via ``HOLD_EXPIRY_WARNING_MINUTES``
    (default 60 minutes).

    Deduplication (Phase 2.2.4)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~
    Because Celery Beat fires this task periodically (default every 15
    minutes) and the warning window is 60 minutes, the same hold can
    appear in multiple consecutive scans.  A Redis SETNX key per hold
    ensures at most **one** notification per hold per warning window.

    The key format is ``notif:hold_expiring_soon:{hold_id}`` with a TTL
    of ``HOLD_EXPIRY_WARNING_MINUTES * 60`` seconds.  If Redis is
    unavailable, the task **fails open** — notifications are sent without
    dedup rather than silently suppressed.

    Returns:
        A dict with counts of notified / skipped holds.
    """
    try:
        return asyncio.run(_send_expiring_soon_async())
    except Exception as exc:
        logger.exception("send_expiring_soon_notifications_task failed")
        raise self.retry(exc=exc)


async def _send_expiring_soon_async() -> dict:
    """Async implementation for expiring-soon notifications with Redis dedup."""
    settings = get_settings()
    session = _new_async_session()
    notified_count = 0
    skipped_count = 0

    # Redis client for dedup — constructed from the same URL as the app pool.
    # Lifecycle is managed here, not through the FastAPI dependency.
    redis_client: Redis | None = None
    try:
        redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        logger.warning(
            "expiring_soon: could not connect to Redis for dedup; "
            "proceeding without deduplication"
        )

    # TTL = full warning window so each hold gets at most one notification
    dedup_ttl = HOLD_EXPIRY_WARNING_MINUTES * 60

    try:
        (
            _hold_service,
            hold_repo,
            notification_service,
            property_repo,
            bed_repo,
        ) = _build_hold_service(session)

        now = datetime.now(tz=timezone.utc)
        threshold = now + timedelta(minutes=HOLD_EXPIRY_WARNING_MINUTES)

        expiring_holds = await hold_repo.list_expiring_soon(threshold)

        if not expiring_holds:
            logger.info("expiring_soon: no holds expiring within %d minutes", HOLD_EXPIRY_WARNING_MINUTES)
            return {"status": "ok", "notified": 0, "skipped": 0}

        logger.info("expiring_soon: found %d holds expiring soon", len(expiring_holds))

        for hold in expiring_holds:
            try:
                # ── Dedup check (Phase 2.2.4) ────────────────────────────
                dedup_key = f"notif:hold_expiring_soon:{hold.id}"
                is_new = True  # default: send (fail-open)

                if redis_client is not None:
                    try:
                        is_new = await redis_client.set(
                            dedup_key, "1", nx=True, ex=dedup_ttl
                        )
                    except Exception:
                        logger.warning(
                            "expiring_soon: Redis dedup failed for hold %s; "
                            "proceeding without dedup",
                            hold.id,
                        )
                        is_new = True  # fail-open

                if not is_new:
                    logger.debug(
                        "expiring_soon: skipping duplicate for hold %s", hold.id
                    )
                    skipped_count += 1
                    continue

                # ── Send notification ────────────────────────────────────
                prop = await property_repo.get(hold.property_id)
                bed = await bed_repo.get(hold.bed_id)

                property_name = prop.name if prop else "Unknown"
                bed_label = (bed.label or bed.bed_number) if bed else "Unknown"
                expires_at_str = hold.expires_at.isoformat() if hold.expires_at else ""

                await notification_service.notify_hold_expiring_soon(
                    student_id=hold.student_id,
                    bed_id=hold.bed_id,
                    property_name=property_name,
                    bed_label=bed_label,
                    expires_at=expires_at_str,
                )

                notified_count += 1

            except Exception:
                logger.exception(
                    "expiring_soon: failed to notify for hold %s", hold.id
                )

        await session.commit()

        result = {
            "status": "ok",
            "notified": notified_count,
            "skipped": skipped_count,
        }
        logger.info("expiring_soon complete: %s", result)
        return result

    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
        if redis_client is not None:
            await redis_client.aclose()
