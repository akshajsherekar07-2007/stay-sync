"""Phase 2.1.1 — Notifications and audit logs.

Revision ID: 007
Revises: 006
Create Date: 2026-06-14

Tables created
--------------
  notifications  — In-app notification records (no updated_at, no deleted_at)
  audit_logs     — Append-only audit trail (no updated_at, no deleted_at)

Key design notes
-----------------
  • Neither table has updated_at or deleted_at — they are not soft-deletable.
  • notifications.data defaults to '{}'::jsonb.
  • audit_logs is strictly append-only — no triggers needed.
  • notifications gets no updated_at trigger (immutable after creation,
    except for the is_read flag which is toggled at the application layer).

Rollback
--------
downgrade() drops all indexes and tables in reverse order.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ── Revision identifiers ─────────────────────────────────────────────────────

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── Upgrade ───────────────────────────────────────────────────────────────────

def upgrade() -> None:
    # ── notifications ─────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "type",
            sa.String(50),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column(
            "data",
            postgresql.JSONB,
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "is_read",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        # ── CHECK constraints ─────────────────────────────────────────────────
        sa.CheckConstraint(
            "type IN ("
            "'hold_requested', 'hold_approved', 'hold_rejected', "
            "'hold_expired', 'hold_overridden', 'hold_expiring_soon', "
            "'waitlist_promoted', 'booking_confirmed', "
            "'property_verified', 'system_announcement'"
            ")",
            name="ck_notifications_type",
        ),
    )

    # ── notifications indexes ─────────────────────────────────────────────────
    op.create_index("idx_notifications_user", "notifications", ["user_id"])
    op.create_index(
        "idx_notifications_unread",
        "notifications",
        ["user_id"],
        postgresql_where=sa.text("is_read = false"),
    )
    op.create_index("idx_notifications_type", "notifications", ["type"])
    op.create_index(
        "idx_notifications_created",
        "notifications",
        [sa.text("created_at DESC")],
    )

    # ── audit_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column(
            "entity_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("old_data", postgresql.JSONB, nullable=True),
        sa.Column("new_data", postgresql.JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # ── audit_logs indexes ────────────────────────────────────────────────────
    op.create_index(
        "idx_audit_entity",
        "audit_logs",
        ["entity_type", "entity_id"],
    )
    op.create_index("idx_audit_user", "audit_logs", ["user_id"])
    op.create_index("idx_audit_action", "audit_logs", ["action"])
    op.create_index(
        "idx_audit_created",
        "audit_logs",
        [sa.text("created_at DESC")],
    )


# ── Downgrade ─────────────────────────────────────────────────────────────────

def downgrade() -> None:
    # ── audit_logs ────────────────────────────────────────────────────────────
    op.drop_index("idx_audit_created", table_name="audit_logs")
    op.drop_index("idx_audit_action", table_name="audit_logs")
    op.drop_index("idx_audit_user", table_name="audit_logs")
    op.drop_index("idx_audit_entity", table_name="audit_logs")
    op.drop_table("audit_logs")

    # ── notifications ─────────────────────────────────────────────────────────
    op.drop_index("idx_notifications_created", table_name="notifications")
    op.drop_index("idx_notifications_type", table_name="notifications")
    op.drop_index("idx_notifications_unread", table_name="notifications")
    op.drop_index("idx_notifications_user", table_name="notifications")
    op.drop_table("notifications")
