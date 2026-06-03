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
"""

# Preserve import order — parent tables first
from app.models.user import User
from app.models.profile import Profile
from app.models.property import Property
from app.models.floor import Floor
from app.models.room import Room
from app.models.bed import Bed
from app.models.refresh_token import RefreshToken

__all__ = [
    "User",
    "Profile",
    "Property",
    "Floor",
    "Room",
    "Bed",
    "RefreshToken",
]
