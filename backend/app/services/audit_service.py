"""Audit Service — business logic for audit logging.

Provides an abstraction layer over the AuditLogRepository for logging critical system events
and retrieving audit trails.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi.encoders import jsonable_encoder

from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository

logger = logging.getLogger(__name__)


class AuditService:
    """Service for handling audit logging and history retrieval."""

    def __init__(self, audit_log_repo: AuditLogRepository) -> None:
        self._audit_log_repo = audit_log_repo

    async def log_action(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        old_data: Any | None = None,
        new_data: Any | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Record an audit log entry synchronously.

        Serializes `old_data` and `new_data` into JSON-safe dictionaries before saving.

        Args:
            action: Action performed (e.g., 'hold_approved', 'property_created').
            entity_type: Type of entity affected (e.g., 'hold_request', 'property').
            entity_id: UUID of the affected entity.
            user_id: Actor user UUID (None for system-initiated).
            old_data: Data snapshot before the change (will be json-encoded).
            new_data: Data snapshot after the change (will be json-encoded).
            ip_address: Client IP address.
            user_agent: Client user-agent string.

        Returns:
            The created AuditLog instance.
        """
        try:
            encoded_old = jsonable_encoder(old_data) if old_data is not None else None
            encoded_new = jsonable_encoder(new_data) if new_data is not None else None

            log_entry = await self._audit_log_repo.create(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                old_data=encoded_old,
                new_data=encoded_new,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return log_entry
        except Exception as e:
            # We log the error but we might still want to raise it to roll back the transaction
            # depending on whether audit logs are critical (they usually are).
            logger.exception("Failed to create audit log for %s on %s %s", action, entity_type, entity_id)
            raise

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Fetch the audit trail for a specific entity.

        Args:
            entity_type: The type of entity (e.g., 'hold_request').
            entity_id: The UUID of the entity.
            page: 1-indexed page number.
            page_size: Number of items per page.

        Returns:
            A tuple containing a list of AuditLog entries and the total count.
        """
        return await self._audit_log_repo.list_by_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            page=page,
            page_size=page_size,
        )
