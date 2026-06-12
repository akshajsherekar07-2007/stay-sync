"""Phase 1.5 — Saved properties (student wishlist) table.

Revision ID: 004
Revises: 003
Create Date: 2026-06-12

Tables created
--------------
  saved_properties — Student wishlist / bookmarked properties
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ── Revision identifiers ─────────────────────────────────────────────────────

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "saved_properties",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
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
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_index(
        "idx_saved_unique",
        "saved_properties",
        ["student_id", "property_id"],
        unique=True,
    )
    op.create_index(
        "idx_saved_student",
        "saved_properties",
        ["student_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_saved_student", table_name="saved_properties")
    op.drop_index("idx_saved_unique", table_name="saved_properties")
    op.drop_table("saved_properties")
