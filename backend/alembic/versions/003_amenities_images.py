"""Phase 1.5 — Amenities, property_amenities, and property_images tables.

Revision ID: 003
Revises: 002
Create Date: 2026-06-12

Tables created
--------------
  amenities           — Master amenity catalog (no updated_at/deleted_at)
  property_amenities  — Property ↔ Amenity junction table
  property_images     — Image references for properties, floors, rooms, beds
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ── Revision identifiers ─────────────────────────────────────────────────────

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── amenities ─────────────────────────────────────────────────────────────
    op.create_table(
        "amenities",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(100),
            nullable=False,
        ),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Unique constraint on name
    op.create_index(
        "idx_amenities_name",
        "amenities",
        ["name"],
        unique=True,
    )

    # ── property_amenities ────────────────────────────────────────────────────
    op.create_table(
        "property_amenities",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "amenity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("amenities.id", ondelete="CASCADE"),
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
        "idx_property_amenities_unique",
        "property_amenities",
        ["property_id", "amenity_id"],
        unique=True,
    )
    op.create_index(
        "idx_property_amenities_property",
        "property_amenities",
        ["property_id"],
    )

    # ── property_images ───────────────────────────────────────────────────────
    op.create_table(
        "property_images",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "entity_type",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "entity_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("alt_text", sa.String(255), nullable=True),
        sa.Column(
            "sort_order",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "is_primary",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
        sa.Column("mime_type", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "entity_type IN ('property', 'floor', 'room', 'bed')",
            name="ck_images_entity_type",
        ),
    )

    op.create_index(
        "idx_images_entity",
        "property_images",
        ["entity_type", "entity_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_images_property",
        "property_images",
        ["property_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    # ── property_images ───────────────────────────────────────────────────────
    op.drop_index("idx_images_property", table_name="property_images")
    op.drop_index("idx_images_entity", table_name="property_images")
    op.drop_table("property_images")

    # ── property_amenities ────────────────────────────────────────────────────
    op.drop_index("idx_property_amenities_property", table_name="property_amenities")
    op.drop_index("idx_property_amenities_unique", table_name="property_amenities")
    op.drop_table("property_amenities")

    # ── amenities ─────────────────────────────────────────────────────────────
    op.drop_index("idx_amenities_name", table_name="amenities")
    op.drop_table("amenities")
