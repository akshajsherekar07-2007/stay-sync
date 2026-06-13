"""Phase 2.1.1 — Hold system: hold_requests, waitlist_entries, bookings.

Revision ID: 006
Revises: 005
Create Date: 2026-06-14

Tables created
--------------
  hold_requests     — Student hold requests on beds
  waitlist_entries  — Queue for students waiting for held/occupied beds
  bookings          — Confirmed occupancy records

Key design notes
-----------------
  • hold_duration_hours CHECK-constrained to [1, 72] (default 24).
  • Partial unique indexes enforce single active hold per bed and
    single active hold per student-bed pair at the database level.
  • All UUID PKs use gen_random_uuid() — matching project convention.
  • Updated-at triggers reuse the update_updated_at_column() function
    created in 001_initial_schema.

Rollback
--------
downgrade() drops all triggers, indexes, and tables in reverse order.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ── Revision identifiers ─────────────────────────────────────────────────────

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _create_updated_at_trigger(table_name: str) -> None:
    """Attach the set_updated_at trigger to a table."""
    op.execute(f"""
        CREATE TRIGGER set_updated_at_{table_name}
        BEFORE UPDATE ON {table_name}
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column()
    """)


def _drop_updated_at_trigger(table_name: str) -> None:
    """Remove the set_updated_at trigger from a table."""
    op.execute(
        f"DROP TRIGGER IF EXISTS set_updated_at_{table_name} ON {table_name}"
    )


# ── Upgrade ───────────────────────────────────────────────────────────────────

def upgrade() -> None:
    # ── hold_requests ─────────────────────────────────────────────────────────
    op.create_table(
        "hold_requests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "bed_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("beds.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "hold_duration_hours",
            sa.Integer,
            nullable=False,
            server_default=sa.text("24"),
        ),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "resolved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolution_note", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # ── CHECK constraints ─────────────────────────────────────────────────
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'expired', 'overridden', 'cancelled')",
            name="ck_hold_requests_status",
        ),
        sa.CheckConstraint(
            "hold_duration_hours BETWEEN 1 AND 72",
            name="ck_hold_requests_duration",
        ),
    )

    # ── hold_requests indexes ─────────────────────────────────────────────────
    op.create_index("idx_holds_bed_id", "hold_requests", ["bed_id"])
    op.create_index("idx_holds_student_id", "hold_requests", ["student_id"])
    op.create_index("idx_holds_property_id", "hold_requests", ["property_id"])
    op.create_index("idx_holds_resolved_by", "hold_requests", ["resolved_by"])
    op.create_index("idx_holds_status", "hold_requests", ["status"])
    op.create_index(
        "idx_holds_expires",
        "hold_requests",
        ["expires_at"],
        postgresql_where=sa.text("status IN ('pending', 'approved')"),
    )
    # Only one active (pending/approved) hold per bed at a time
    op.create_index(
        "idx_holds_active_bed",
        "hold_requests",
        ["bed_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('pending', 'approved') AND deleted_at IS NULL"
        ),
    )
    # A student cannot have two active holds on the same bed
    op.create_index(
        "idx_holds_active_student_bed",
        "hold_requests",
        ["student_id", "bed_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('pending', 'approved') AND deleted_at IS NULL"
        ),
    )

    _create_updated_at_trigger("hold_requests")

    # ── waitlist_entries ──────────────────────────────────────────────────────
    op.create_table(
        "waitlist_entries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "bed_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("beds.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # ── CHECK constraints ─────────────────────────────────────────────────
        sa.CheckConstraint(
            "status IN ('active', 'promoted', 'expired', 'cancelled')",
            name="ck_waitlist_entries_status",
        ),
    )

    # ── waitlist_entries indexes ──────────────────────────────────────────────
    op.create_index(
        "idx_waitlist_bed",
        "waitlist_entries",
        ["bed_id"],
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index("idx_waitlist_student", "waitlist_entries", ["student_id"])
    op.create_index("idx_waitlist_property", "waitlist_entries", ["property_id"])
    op.create_index(
        "idx_waitlist_position",
        "waitlist_entries",
        ["bed_id", "position"],
        postgresql_where=sa.text("status = 'active'"),
    )
    # A student cannot be in the active queue twice for the same bed
    op.create_index(
        "idx_waitlist_unique_student_bed",
        "waitlist_entries",
        ["student_id", "bed_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active' AND deleted_at IS NULL"),
    )

    _create_updated_at_trigger("waitlist_entries")

    # ── bookings ──────────────────────────────────────────────────────────────
    op.create_table(
        "bookings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "bed_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("beds.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "hold_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("hold_requests.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'confirmed'"),
        ),
        sa.Column("check_in_date", sa.Date, nullable=True),
        sa.Column("check_out_date", sa.Date, nullable=True),
        sa.Column(
            "confirmed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("vacated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # ── CHECK constraints ─────────────────────────────────────────────────
        sa.CheckConstraint(
            "status IN ('confirmed', 'vacated', 'cancelled')",
            name="ck_bookings_status",
        ),
    )

    # ── bookings indexes ──────────────────────────────────────────────────────
    op.create_index("idx_bookings_bed", "bookings", ["bed_id"])
    op.create_index("idx_bookings_student", "bookings", ["student_id"])
    op.create_index("idx_bookings_property", "bookings", ["property_id"])
    op.create_index("idx_bookings_hold_request", "bookings", ["hold_request_id"])
    op.create_index("idx_bookings_status", "bookings", ["status"])
    # Only one active booking per bed
    op.create_index(
        "idx_bookings_active_bed",
        "bookings",
        ["bed_id"],
        unique=True,
        postgresql_where=sa.text("status = 'confirmed' AND deleted_at IS NULL"),
    )
    # Only one active booking per student per bed
    op.create_index(
        "idx_bookings_active_student_bed",
        "bookings",
        ["student_id", "bed_id"],
        unique=True,
        postgresql_where=sa.text("status = 'confirmed' AND deleted_at IS NULL"),
    )

    _create_updated_at_trigger("bookings")


# ── Downgrade ─────────────────────────────────────────────────────────────────

def downgrade() -> None:
    # ── bookings ──────────────────────────────────────────────────────────────
    _drop_updated_at_trigger("bookings")
    op.drop_index("idx_bookings_active_student_bed", table_name="bookings")
    op.drop_index("idx_bookings_active_bed", table_name="bookings")
    op.drop_index("idx_bookings_status", table_name="bookings")
    op.drop_index("idx_bookings_hold_request", table_name="bookings")
    op.drop_index("idx_bookings_property", table_name="bookings")
    op.drop_index("idx_bookings_student", table_name="bookings")
    op.drop_index("idx_bookings_bed", table_name="bookings")
    op.drop_table("bookings")

    # ── waitlist_entries ──────────────────────────────────────────────────────
    _drop_updated_at_trigger("waitlist_entries")
    op.drop_index("idx_waitlist_unique_student_bed", table_name="waitlist_entries")
    op.drop_index("idx_waitlist_position", table_name="waitlist_entries")
    op.drop_index("idx_waitlist_property", table_name="waitlist_entries")
    op.drop_index("idx_waitlist_student", table_name="waitlist_entries")
    op.drop_index("idx_waitlist_bed", table_name="waitlist_entries")
    op.drop_table("waitlist_entries")

    # ── hold_requests ─────────────────────────────────────────────────────────
    _drop_updated_at_trigger("hold_requests")
    op.drop_index("idx_holds_active_student_bed", table_name="hold_requests")
    op.drop_index("idx_holds_active_bed", table_name="hold_requests")
    op.drop_index("idx_holds_expires", table_name="hold_requests")
    op.drop_index("idx_holds_status", table_name="hold_requests")
    op.drop_index("idx_holds_resolved_by", table_name="hold_requests")
    op.drop_index("idx_holds_property_id", table_name="hold_requests")
    op.drop_index("idx_holds_student_id", table_name="hold_requests")
    op.drop_index("idx_holds_bed_id", table_name="hold_requests")
    op.drop_table("hold_requests")
