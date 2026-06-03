"""Application-level enumerations for StaySync.

Enums are stored as VARCHAR in the database and validated at the
application layer via Pydantic.  All enum values use lowercase strings
to match the database CHECK constraints defined in DATABASE_SCHEMA.md §2.

Only enums needed for Phase 1 are defined here.  Phase 2/3 enums
(HoldStatus, WaitlistStatus, BookingStatus, etc.) will be added when
those phases are implemented.
"""

from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    """Roles assigned to platform users.

    Values must match the CHECK constraint on ``users.role``:
    ``CHECK (role IN ('student', 'owner', 'admin'))``.
    """

    STUDENT = "student"
    OWNER = "owner"
    ADMIN = "admin"
