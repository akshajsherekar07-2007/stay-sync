"""Application-level enumerations for StaySync.

Enums are stored as VARCHAR in the database and validated at the
application layer via Pydantic.  All enum values use lowercase strings
to match the database CHECK constraints defined in DATABASE_SCHEMA.md §2.

Phase 1 enums: UserRole, PropertyType, GenderPreference, SharingType,
BedStatus, PropertyStatus, ImageEntityType.

Phase 2/3 enums (HoldStatus, WaitlistStatus, BookingStatus, etc.) will
be added when those phases are implemented.
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


class PropertyType(str, Enum):
    """Type of accommodation property.

    Values must match ``ck_properties_type`` CHECK constraint.
    """

    PG = "pg"
    HOSTEL = "hostel"
    FLAT = "flat"
    APARTMENT = "apartment"


class GenderPreference(str, Enum):
    """Gender preference for a property.

    Values must match ``ck_properties_gender`` CHECK constraint.
    """

    MALE = "male"
    FEMALE = "female"
    COED = "coed"


class SharingType(str, Enum):
    """Room sharing configuration.

    Values must match ``ck_rooms_sharing_type`` CHECK constraint.
    """

    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    QUAD = "quad"


class BedStatus(str, Enum):
    """Current occupancy status of a bed.

    Values must match ``ck_beds_status`` CHECK constraint.
    """

    VACANT = "vacant"
    HELD = "held"
    OCCUPIED = "occupied"


class PropertyStatus(str, Enum):
    """Lifecycle status of a property listing.

    Values must match ``ck_properties_status`` CHECK constraint.
    """

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class ImageEntityType(str, Enum):
    """The entity type that an image belongs to.

    Used in the ``property_images`` polymorphic association.
    """

    PROPERTY = "property"
    FLOOR = "floor"
    ROOM = "room"
    BED = "bed"
