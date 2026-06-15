"""Celery application factory and configuration.

Creates a Celery instance using Redis as both the message broker and result
backend.  Configuration is sourced from the application settings singleton
(``get_settings()``) so that ``REDIS_URL`` is the single source of truth.

Usage — worker startup::

    celery -A app.core.celery:celery_app worker --loglevel=info

Usage — beat startup (future phases)::

    celery -A app.core.celery:celery_app beat --loglevel=info

The Celery instance auto-discovers tasks registered in ``app.tasks``.
"""

from __future__ import annotations

import logging

from celery import Celery

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

    # Auto-discover tasks registered in app/tasks/ sub-modules.
    # Each future task module (e.g. app/tasks/hold_tasks.py) will be
    # detected automatically — no manual imports required.
    app.autodiscover_tasks(["app.tasks"])

    logger.info(
        "Celery app configured  broker=%s  backend=%s",
        settings.REDIS_URL,
        app.conf.result_backend,
    )

    return app


# Module-level singleton used by the ``celery`` CLI and task decorators.
celery_app: Celery = create_celery_app()
