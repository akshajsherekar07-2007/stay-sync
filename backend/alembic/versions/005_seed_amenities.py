"""Phase 1.5 — Seed default amenities data.

Revision ID: 005
Revises: 004
Create Date: 2026-06-12

Data inserted
-------------
  18 default amenity records across 4 categories:
  basic, safety, comfort, facilities
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# ── Revision identifiers ─────────────────────────────────────────────────────

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Seed data ─────────────────────────────────────────────────────────────────

AMENITIES = [
    # (name, icon, category)
    ("WiFi", "wifi", "basic"),
    ("AC", "snowflake", "comfort"),
    ("Parking", "car", "facilities"),
    ("Laundry", "shirt", "facilities"),
    ("Gym", "dumbbell", "facilities"),
    ("Power Backup", "zap", "basic"),
    ("Water Purifier", "droplets", "basic"),
    ("CCTV", "camera", "safety"),
    ("Security Guard", "shield", "safety"),
    ("Elevator", "arrow-up-down", "facilities"),
    ("Hot Water", "thermometer", "basic"),
    ("Kitchen", "chef-hat", "facilities"),
    ("Fridge", "refrigerator", "comfort"),
    ("TV", "tv", "comfort"),
    ("Study Room", "book-open", "facilities"),
    ("Common Area", "users", "facilities"),
    ("Balcony", "sun", "comfort"),
    ("Garden", "tree-pine", "comfort"),
]


def upgrade() -> None:
    for name, icon, category in AMENITIES:
        op.execute(
            f"INSERT INTO amenities (name, icon, category) "
            f"VALUES ('{name}', '{icon}', '{category}') "
            f"ON CONFLICT (name) DO NOTHING"
        )


def downgrade() -> None:
    names = ", ".join(f"'{name}'" for name, _, _ in AMENITIES)
    op.execute(f"DELETE FROM amenities WHERE name IN ({names})")
