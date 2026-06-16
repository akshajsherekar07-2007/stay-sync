"""Tests for Celery maintenance tasks.

Mocks the database session and service constructors to verify the task
execution flows, transaction management, and fail-open logic.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.tasks.maintenance_tasks import (
    cleanup_expired_tokens_task,
    detect_stale_listings_task,
)


def test_cleanup_expired_tokens_task_success() -> None:
    """Verify cleanup_expired_tokens_task calls repository and commits."""
    mock_session = AsyncMock()
    mock_refresh_repo = AsyncMock()
    mock_refresh_repo.delete_expired.return_value = 12

    # Patch new session creator and wire helper
    with patch(
        "app.tasks.maintenance_tasks._new_async_session",
        return_value=mock_session,
    ), patch(
        "app.tasks.maintenance_tasks._build_maintenance_services",
        return_value=(mock_refresh_repo, MagicMock(), MagicMock(), MagicMock()),
    ):
        result = cleanup_expired_tokens_task()

    assert result == {"status": "ok", "deleted_count": 12}
    mock_refresh_repo.delete_expired.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()
    mock_session.rollback.assert_not_called()


def test_cleanup_expired_tokens_task_rollback_on_error() -> None:
    """Verify cleanup_expired_tokens_task rolls back and raises on error."""
    mock_session = AsyncMock()
    mock_refresh_repo = AsyncMock()
    mock_refresh_repo.delete_expired.side_effect = RuntimeError("DB Connection Lost")

    # Patch new session creator and wire helper
    with patch(
        "app.tasks.maintenance_tasks._new_async_session",
        return_value=mock_session,
    ), patch(
        "app.tasks.maintenance_tasks._build_maintenance_services",
        return_value=(mock_refresh_repo, MagicMock(), MagicMock(), MagicMock()),
    ):
        with pytest.raises(Exception) as excinfo:
            cleanup_expired_tokens_task()

    assert "DB Connection Lost" in str(excinfo.value)
    mock_session.commit.assert_not_called()
    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()


def test_detect_stale_listings_task_no_listings() -> None:
    """Verify detect_stale_listings_task returns empty result if no properties found."""
    mock_session = AsyncMock()
    mock_session.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))

    # Patch new session creator
    with patch(
        "app.tasks.maintenance_tasks._new_async_session",
        return_value=mock_session,
    ):
        result = detect_stale_listings_task()

    assert result == {
        "status": "ok",
        "stale_count": 0,
        "deactivated_count": 0,
        "failed_count": 0,
    }
    mock_session.commit.assert_not_called()
    mock_session.close.assert_called_once()


def test_detect_stale_listings_task_success() -> None:
    """Verify detect_stale_listings_task deactivates stale properties and triggers notifications."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    
    # Setup stale property mock
    mock_prop = MagicMock()
    mock_prop.id = "prop-uuid"
    mock_prop.owner_id = "owner-uuid"
    mock_prop.name = "Test Stale PG"
    mock_prop.status = "active"
    mock_prop.last_refreshed_at = None
    
    # Mock database query to yield this property
    query_mock_properties = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_prop]))))
    mock_session.execute.return_value = query_mock_properties
 
    # Setup mocks for services
    mock_property_repo = MagicMock()
    mock_audit_service = AsyncMock()
    mock_notification_service = AsyncMock()
    mock_notification_repo = AsyncMock()
    mock_notification_service._notification_repo = mock_notification_repo
 
    with patch(
        "app.tasks.maintenance_tasks._new_async_session",
        return_value=mock_session,
    ), patch(
        "app.tasks.maintenance_tasks._build_maintenance_services",
        return_value=(MagicMock(), mock_property_repo, mock_audit_service, mock_notification_service),
    ):
        result = detect_stale_listings_task()

    assert result == {
        "status": "ok",
        "stale_count": 1,
        "deactivated_count": 1,
        "failed_count": 0,
    }
    
    # Verify property was updated to inactive
    assert mock_prop.status == "inactive"
    mock_session.add.assert_called_with(mock_prop)
    
    # Verify audit log was appended
    mock_audit_service.log_action.assert_called_once_with(
        action="property_marked_stale",
        entity_type="property",
        entity_id="prop-uuid",
        user_id=None,
        old_data={"status": "active", "last_refreshed_at": None},
        new_data={"status": "inactive"},
        ip_address="celery-worker",
        user_agent="StaySync Celery Worker",
    )

    # Verify notification created
    mock_notification_repo.create.assert_called_once()
    
    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()
