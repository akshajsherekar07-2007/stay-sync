"""Background task package — Celery task auto-discovery root.

All task modules placed in this package (e.g. ``hold_tasks.py``,
``notification_tasks.py``) are auto-discovered by Celery via
``app.autodiscover_tasks(["app.tasks"])``.

No business tasks are registered yet — this file wires the Celery app
reference so that ``@celery_app.task`` or ``@shared_task`` can be
imported by future task modules.

Example — adding a task in Phase 2.2.2::

    # app/tasks/hold_tasks.py
    from celery import shared_task

    @shared_task(bind=True, max_retries=3)
    def expire_hold(self, hold_id: str) -> None:
        ...
"""

from __future__ import annotations

# Re-export the celery app so task modules can do:
#   from app.tasks import celery_app
from app.core.celery import celery_app

# Explicit task imports for Celery registration
from app.tasks.hold_tasks import (
    expire_hold_task,
    scan_and_expire_holds_task,
    send_expiring_soon_notifications_task,
)
from app.tasks.maintenance_tasks import (
    cleanup_expired_tokens_task,
    detect_stale_listings_task,
)

__all__ = [
    "celery_app",
    "expire_hold_task",
    "scan_and_expire_holds_task",
    "send_expiring_soon_notifications_task",
    "cleanup_expired_tokens_task",
    "detect_stale_listings_task",
]