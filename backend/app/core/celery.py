"""Celery application factory and configuration.

Creates a Celery instance using Redis as both the message broker and result
backend.  Configuration is sourced from the application settings singleton
(``get_settings()``) so that ``REDIS_URL`` is the single source of truth.

Usage — worker startup::

    celery -A app.core.celery:celery_app worker --loglevel=info --pool=solo

Usage — beat startup::

    celery -A app.core.celery:celery_app beat --loglevel=info

Run both processes simultaneously for full periodic-task support.

The Celery instance auto-discovers tasks registered in ``app.tasks``.
Beat schedules are defined in ``_build_beat_schedule()`` and applied inside
``create_celery_app()``.
"""

from __future__ import annotations

import logging

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _build_result_backend_url(redis_url: str) -> str:
    """Derive a result-backend URL on Redis DB 1 to isolate from the cache DB.

    The application's async Redis pool uses DB 0 (the default).  Celery
    results are stored in DB 1 to avoid key-namespace collisions.
    """
    # Strip a trailing db number if present (e.g. "redis://localhost:6379/0")
    base = redis_url.rsplit("/", 1)[0]
    return f"{base}/1"


def _seconds_to_crontab(interval_seconds: int) -> crontab:
    """Convert an interval in whole minutes to a :class:`crontab` expression.

    Args:
        interval_seconds: Interval in seconds.  Must be a positive multiple of
            60 — Beat schedules resolve to whole cron minutes.

    Returns:
        A :class:`~celery.schedules.crontab` that fires every N minutes.

    Raises:
        ValueError: If ``interval_seconds`` is not a positive multiple of 60.
    """
    if interval_seconds <= 0 or interval_seconds % 60 != 0:
        raise ValueError(
            f"interval_seconds must be a positive multiple of 60, got {interval_seconds}"
        )
    minutes = interval_seconds // 60
    if minutes == 1:
        # crontab(minute="*") fires every minute
        return crontab(minute="*")
    # crontab(minute="*/N") fires every N minutes
    return crontab(minute=f"*/{minutes}")


def _build_beat_schedule(settings) -> dict:
    """Build the ``beat_schedule`` dict from application settings.

    Keeping schedule construction in a dedicated helper makes
    ``create_celery_app()`` readable and the schedule trivially testable
    in isolation.

    Returns:
        A dict suitable for assignment to ``app.conf.beat_schedule``.
    """
    return {
        # ── Bulk hold-expiry scan ─────────────────────────────
        # Finds all approved holds whose expires_at is in the past and
        # transitions each one to EXPIRED (releasing the bed and promoting
        # waitlist candidates).
        "hold-scan-and-expire": {
            "task": "hold.scan_and_expire",
            "schedule": _seconds_to_crontab(
                settings.CELERY_BEAT_EXPIRE_SCAN_INTERVAL_SECONDS
            ),
        },
        # ── Expiring-soon notification scan ──────────────────
        # Finds approved holds expiring within HOLD_EXPIRY_WARNING_MINUTES
        # (60 min) and sends in-app advance-warning notifications.
        # Dedup via Redis SETNX prevents duplicate notifications (Phase 2.2.4).
        "hold-send-expiring-soon-notifications": {
            "task": "hold.send_expiring_soon_notifications",
            "schedule": _seconds_to_crontab(
                settings.CELERY_BEAT_EXPIRING_SOON_INTERVAL_SECONDS
            ),
        },
        # ── Expired Token Cleanup (Phase 2) ──────────────────
        # Hard-deletes expired refresh tokens from database daily (86400s).
        "maintenance-cleanup-expired-tokens": {
            "task": "maintenance.cleanup_expired_tokens",
            "schedule": _seconds_to_crontab(86400),
        },
        # ── Stale Listings Detection (Phase 2) ───────────────
        # Deactivates listings with no updates for 30+ days daily (86400s).
        "maintenance-detect-stale-listings": {
            "task": "maintenance.detect_stale_listings",
            "schedule": _seconds_to_crontab(86400),
        },
    }


def create_celery_app() -> Celery:
    """Build and configure the Celery application instance.

    Returns:
        A fully configured :class:`~celery.Celery` instance.
    """
    settings = get_settings()

    app = Celery("staysync")

    app.conf.update(
        # ── Broker (Redis) ───────────────────────────────────
        broker_url=settings.REDIS_URL,
        result_backend=_build_result_backend_url(settings.REDIS_URL),

        # ── Serialization ────────────────────────────────────
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],

        # ── Time / timezone ──────────────────────────────────
        timezone="UTC",
        enable_utc=True,

        # ── Result tracking ──────────────────────────────────
        task_track_started=True,
        result_expires=settings.CELERY_RESULT_EXPIRES_SECONDS,

        # ── Reliability ──────────────────────────────────────
        task_acks_late=True,
        worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
        task_reject_on_worker_lost=True,

        # ── Default retry policy ─────────────────────────────
        task_default_retry_delay=30,
        task_max_retries=3,

        # ── Broker connection reliability ────────────────────
        broker_connection_retry_on_startup=True,
    )

    # ── Task discovery ────────────────────────────────────────────────────────
    # conf.imports triggers eager import of each listed module so that
    # @shared_task decorators execute and register tasks on this app.
    app.conf.imports = (
        "app.tasks.hold_tasks",
    )

    app.autodiscover_tasks(["app.tasks"])

    # ── Beat schedule (Phase 2.2.3) ───────────────────────────────────────────
    # Defines which tasks are executed periodically and how often.
    # Beat is a separate process — start it alongside the worker:
    #   celery -A app.core.celery:celery_app beat --loglevel=info
    app.conf.beat_schedule = _build_beat_schedule(settings)

    # Beat persists last-run timestamps in a local shelve file.
    # The filename is fixed so it is always created in the working directory
    # (wherever the Beat process starts) and easy to locate/delete.
    app.conf.beat_schedule_filename = "celerybeat-schedule"

    logger.info(
        "Celery app configured  broker=%s  backend=%s  beat_schedules=%s",
        settings.REDIS_URL,
        app.conf.result_backend,
        list(app.conf.beat_schedule.keys()),
    )

    return app


# Module-level singleton used by the ``celery`` CLI and task decorators.
celery_app: Celery = create_celery_app()

# Import task modules here to trigger registration of tasks on celery_app.
# This ensures hold.* tasks are in celery_app.tasks immediately after
# ``from app.core.celery import celery_app`` — no manual import required.
import app.tasks.hold_tasks  # noqa: F401
