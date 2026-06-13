"""Phase 2.1.1 — Add FK constraints to beds for Phase 2 tables.

Revision ID: 008
Revises: 007
Create Date: 2026-06-14

Changes
-------
  Adds deferred FK constraints to the existing ``beds`` columns
  ``current_hold_id`` and ``current_booking_id`` that were created in
  001_initial_schema without FKs (the target tables did not exist yet).

  • fk_beds_current_hold    → hold_requests(id)  ON DELETE SET NULL
  • fk_beds_current_booking → bookings(id)        ON DELETE SET NULL

Rollback
--------
downgrade() drops both FK constraints, restoring the Phase 1 state.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# ── Revision identifiers ─────────────────────────────────────────────────────

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── Upgrade ───────────────────────────────────────────────────────────────────

def upgrade() -> None:
    op.create_foreign_key(
        "fk_beds_current_hold",
        "beds",
        "hold_requests",
        ["current_hold_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_foreign_key(
        "fk_beds_current_booking",
        "beds",
        "bookings",
        ["current_booking_id"],
        ["id"],
        ondelete="SET NULL",
    )


# ── Downgrade ─────────────────────────────────────────────────────────────────

def downgrade() -> None:
    op.drop_constraint("fk_beds_current_booking", "beds", type_="foreignkey")
    op.drop_constraint("fk_beds_current_hold", "beds", type_="foreignkey")
