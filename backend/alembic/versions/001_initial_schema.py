"""Phase 1.2 — Initial schema: users, profiles, properties, floors, rooms, beds.

Revision ID: 001_initial_schema
Revises: None (first migration)
Create Date: 2026-05-31

Tables created
--------------
Phase 1.2 scope (per DATABASE_SCHEMA.md):
  users               — Core authentication + identity
  profiles            — Extended user profile (1:1 → users)
  properties          — Accommodation listings (N:1 → users)
  floors              — Floor hierarchy (N:1 → properties)
  rooms               — Room hierarchy (N:1 → floors, properties)
  beds                — Atomic inventory unit (N:1 → rooms, properties)

DB objects also created
------------------------
  • update_updated_at_column() trigger function (applied to all tables)
  • sync_property_bed_counts() trigger function (applied to beds)
  • PostGIS GIST index on properties if PostGIS extension is available

Rollback
--------
downgrade() drops all triggers, trigger functions, indexes, and tables
in reverse dependency order.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ── Revision identifiers ─────────────────────────────────────────────────────

revision: str = "001"
down_revision: Union[str, None] = None
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
    # ── Trigger function: auto-update updated_at ──────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "is_email_verified",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_phone_verified",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "last_login_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
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
        sa.CheckConstraint(
            "role IN ('student', 'owner', 'admin')",
            name="ck_users_role",
        ),
    )

    # Partial unique indexes — only enforce uniqueness for non-deleted rows
    op.create_index(
        "idx_users_email",
        "users",
        ["email"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_users_phone",
        "users",
        ["phone"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND phone IS NOT NULL"),
    )
    op.create_index("idx_users_role", "users", ["role"])

    _create_updated_at_trigger("users")

    # ── profiles ──────────────────────────────────────────────────────────────
    op.create_table(
        "profiles",
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
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("college_name", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("date_of_birth", sa.Date, nullable=True),
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
    )

    op.create_index(
        "idx_profiles_user_id",
        "profiles",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("idx_profiles_city", "profiles", ["city"])

    _create_updated_at_trigger("profiles")

    # ── properties ────────────────────────────────────────────────────────────
    op.create_table(
        "properties",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("property_type", sa.String(20), nullable=False),
        sa.Column(
            "gender_preference",
            sa.String(10),
            nullable=False,
            server_default=sa.text("'coed'"),
        ),
        sa.Column("address_line1", sa.String(255), nullable=False),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("pincode", sa.String(10), nullable=False),
        sa.Column(
            "country",
            sa.String(100),
            nullable=False,
            server_default=sa.text("'India'"),
        ),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("google_place_id", sa.String(255), nullable=True),
        sa.Column("place_name", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(20), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("min_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("max_price", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "total_beds",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "available_beds",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'draft'"),
        ),
        sa.Column(
            "is_verified",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("last_refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rules", sa.Text, nullable=True),
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
        sa.CheckConstraint(
            "property_type IN ('pg', 'hostel', 'flat', 'apartment')",
            name="ck_properties_type",
        ),
        sa.CheckConstraint(
            "gender_preference IN ('male', 'female', 'coed')",
            name="ck_properties_gender",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'pending_review', 'active', 'inactive', 'suspended')",
            name="ck_properties_status",
        ),
    )

    op.create_index("idx_properties_owner_id", "properties", ["owner_id"])
    op.create_index("idx_properties_city", "properties", ["city"])
    op.create_index(
        "idx_properties_status",
        "properties",
        ["status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("idx_properties_type", "properties", ["property_type"])
    op.create_index("idx_properties_gender", "properties", ["gender_preference"])
    op.create_index("idx_properties_price", "properties", ["min_price", "max_price"])
    op.create_index(
        "idx_properties_available",
        "properties",
        ["available_beds"],
        postgresql_where=sa.text("deleted_at IS NULL AND status = 'active'"),
    )

    # PostGIS spatial index — created only if PostGIS extension exists.
    # Falls back gracefully if the extension is not available on this instance.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'postgis'
            ) THEN
                EXECUTE '
                    CREATE INDEX idx_properties_location
                    ON properties
                    USING GIST (ST_MakePoint(longitude::float8, latitude::float8))
                    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                ';
            END IF;
        END;
        $$
    """)

    _create_updated_at_trigger("properties")

    # ── Trigger function: sync bed counts on properties ───────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION sync_property_bed_counts()
        RETURNS TRIGGER AS $$
        DECLARE
            prop_id UUID;
        BEGIN
            prop_id := COALESCE(NEW.property_id, OLD.property_id);

            UPDATE properties
            SET
                total_beds = (
                    SELECT COUNT(*)
                    FROM beds
                    WHERE property_id = prop_id
                      AND deleted_at IS NULL
                ),
                available_beds = (
                    SELECT COUNT(*)
                    FROM beds
                    WHERE property_id = prop_id
                      AND deleted_at IS NULL
                      AND status = 'vacant'
                ),
                updated_at = NOW()
            WHERE id = prop_id;

            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql
    """)

    # ── floors ────────────────────────────────────────────────────────────────
    op.create_table(
        "floors",
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
        sa.Column("floor_number", sa.Integer, nullable=False),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "sort_order",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
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
    )

    op.create_index(
        "idx_floors_property_id",
        "floors",
        ["property_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_floors_property_number",
        "floors",
        ["property_id", "floor_number"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    _create_updated_at_trigger("floors")

    # ── rooms ─────────────────────────────────────────────────────────────────
    op.create_table(
        "rooms",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "floor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("floors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("room_number", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("sharing_type", sa.String(10), nullable=False),
        sa.Column("price_per_bed", sa.Numeric(10, 2), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "has_attached_bath",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "has_ac",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "has_balcony",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "sort_order",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
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
        sa.CheckConstraint(
            "sharing_type IN ('single', 'double', 'triple', 'quad')",
            name="ck_rooms_sharing_type",
        ),
    )

    op.create_index(
        "idx_rooms_floor_id",
        "rooms",
        ["floor_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_rooms_property_id",
        "rooms",
        ["property_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_rooms_floor_number",
        "rooms",
        ["floor_id", "room_number"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("idx_rooms_sharing_type", "rooms", ["sharing_type"])
    op.create_index("idx_rooms_price", "rooms", ["price_per_bed"])

    _create_updated_at_trigger("rooms")

    # ── beds ──────────────────────────────────────────────────────────────────
    op.create_table(
        "beds",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "room_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("bed_number", sa.String(10), nullable=False),
        sa.Column("label", sa.String(50), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'vacant'"),
        ),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        # Phase 2 FK target columns — FK constraints added in migration 008
        sa.Column(
            "current_hold_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="FK to hold_requests.id — constraint added in Phase 2 migration",
        ),
        sa.Column(
            "current_booking_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="FK to bookings.id — constraint added in Phase 2 migration",
        ),
        sa.Column(
            "version",
            sa.Integer,
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "sort_order",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
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
        sa.CheckConstraint(
            "status IN ('vacant', 'held', 'occupied')",
            name="ck_beds_status",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_beds_version_positive",
        ),
    )

    op.create_index(
        "idx_beds_room_id",
        "beds",
        ["room_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_beds_property_id",
        "beds",
        ["property_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_beds_status",
        "beds",
        ["status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_beds_room_number",
        "beds",
        ["room_id", "bed_number"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    _create_updated_at_trigger("beds")

    # Attach the bed-count sync trigger to beds table
    op.execute("""
        CREATE TRIGGER sync_bed_counts_on_beds
        AFTER INSERT OR UPDATE OR DELETE ON beds
        FOR EACH ROW
        EXECUTE FUNCTION sync_property_bed_counts()
    """)


# ── Downgrade ─────────────────────────────────────────────────────────────────

def downgrade() -> None:
    # ── beds ──────────────────────────────────────────────────────────────────
    op.execute("DROP TRIGGER IF EXISTS sync_bed_counts_on_beds ON beds")
    _drop_updated_at_trigger("beds")
    op.drop_index("idx_beds_room_number", table_name="beds")
    op.drop_index("idx_beds_status", table_name="beds")
    op.drop_index("idx_beds_property_id", table_name="beds")
    op.drop_index("idx_beds_room_id", table_name="beds")
    op.drop_table("beds")

    # ── rooms ─────────────────────────────────────────────────────────────────
    _drop_updated_at_trigger("rooms")
    op.drop_index("idx_rooms_price", table_name="rooms")
    op.drop_index("idx_rooms_sharing_type", table_name="rooms")
    op.drop_index("idx_rooms_floor_number", table_name="rooms")
    op.drop_index("idx_rooms_property_id", table_name="rooms")
    op.drop_index("idx_rooms_floor_id", table_name="rooms")
    op.drop_table("rooms")

    # ── floors ────────────────────────────────────────────────────────────────
    _drop_updated_at_trigger("floors")
    op.drop_index("idx_floors_property_number", table_name="floors")
    op.drop_index("idx_floors_property_id", table_name="floors")
    op.drop_table("floors")

    # ── Trigger functions ─────────────────────────────────────────────────────
    op.execute("DROP FUNCTION IF EXISTS sync_property_bed_counts() CASCADE")

    # ── properties ────────────────────────────────────────────────────────────
    _drop_updated_at_trigger("properties")
    # Drop PostGIS index if it exists
    op.execute("DROP INDEX IF EXISTS idx_properties_location")
    op.drop_index("idx_properties_available", table_name="properties")
    op.drop_index("idx_properties_price", table_name="properties")
    op.drop_index("idx_properties_gender", table_name="properties")
    op.drop_index("idx_properties_type", table_name="properties")
    op.drop_index("idx_properties_status", table_name="properties")
    op.drop_index("idx_properties_city", table_name="properties")
    op.drop_index("idx_properties_owner_id", table_name="properties")
    op.drop_table("properties")

    # ── profiles ──────────────────────────────────────────────────────────────
    _drop_updated_at_trigger("profiles")
    op.drop_index("idx_profiles_city", table_name="profiles")
    op.drop_index("idx_profiles_user_id", table_name="profiles")
    op.drop_table("profiles")

    # ── users ─────────────────────────────────────────────────────────────────
    _drop_updated_at_trigger("users")
    op.drop_index("idx_users_role", table_name="users")
    op.drop_index("idx_users_phone", table_name="users")
    op.drop_index("idx_users_email", table_name="users")
    op.drop_table("users")

    # ── Shared trigger function ───────────────────────────────────────────────
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE")
