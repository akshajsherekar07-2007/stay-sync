"""Application constants.

All magic numbers and fixed values are defined here.
Import from this module instead of hardcoding values.
"""

# ── Bed Status Colors ────────────────────────────────────────
BED_STATUS_VACANT = "vacant"       # 🟢 GREEN
BED_STATUS_HELD = "held"           # 🟡 YELLOW
BED_STATUS_OCCUPIED = "occupied"   # 🔴 RED

# ── Hold System Limits ───────────────────────────────────────
MAX_ACTIVE_HOLDS_PER_STUDENT = 3
HOLD_COOLDOWN_MINUTES = 30
DEFAULT_HOLD_DURATION_HOURS = 24

# ── Pagination ───────────────────────────────────────────────
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ── File Upload ──────────────────────────────────────────────
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_MIME_TYPES = frozenset({
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
})

# ── API ──────────────────────────────────────────────────────
API_VERSION = "v1"
