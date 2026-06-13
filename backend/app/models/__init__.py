"""SQLAlchemy ORM models package.

Importing this package registers all model classes with the shared
``Base.metadata``.  Alembic's ``env.py`` imports ``Base`` from here so that
autogenerate can detect all mapped tables.

Phase 1.2 models (in dependency order)
---------------------------------------
User         → users
Profile      → profiles          (depends on users)
Property     → properties        (depends on users)
Floor        → floors            (depends on properties)
Room         → rooms             (depends on floors, properties)
Bed          → beds              (depends on rooms, properties)

Phase 1.4 models
-----------------
RefreshToken → refresh_tokens    (depends on users)

Phase 1.5 models
-----------------
Amenity         → amenities
PropertyAmenity → property_amenities  (depends on properties, amenities)
PropertyImage   → property_images     (depends on properties)
SavedProperty   → saved_properties    (depends on users, properties)

Phase 2.1 models
-----------------
HoldRequest    → hold_requests      (depends on beds, users, properties)
WaitlistEntry  → waitlist_entries    (depends on beds, users, properties)
Booking        → bookings           (depends on beds, users, properties, hold_requests)
Notification   → notifications      (depends on users)
AuditLog       → audit_logs         (depends on users)
"""

# Preserve import order — parent tables first
from app.models.user import User
from app.models.profile import Profile
from app.models.property import Property
from app.models.floor import Floor
from app.models.room import Room
from app.models.bed import Bed
from app.models.refresh_token import RefreshToken
from app.models.amenity import Amenity
from app.models.property_amenity import PropertyAmenity
from app.models.property_image import PropertyImage
from app.models.saved_property import SavedProperty
from app.models.hold_request import HoldRequest
from app.models.waitlist_entry import WaitlistEntry
from app.models.booking import Booking
from app.models.notification import Notification
from app.models.audit_log import AuditLog

__all__ = [
    "User",
    "Profile",
    "Property",
    "Floor",
    "Room",
    "Bed",
    "RefreshToken",
    "Amenity",
    "PropertyAmenity",
    "PropertyImage",
    "SavedProperty",
    "HoldRequest",
    "WaitlistEntry",
    "Booking",
    "Notification",
    "AuditLog",
]

