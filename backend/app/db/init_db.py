"""Database initialisation utilities.

Provides ``init_db()`` to be called from the application lifespan hook.
In Phase 1 this simply verifies the connection is reachable.

Note: Schema creation/migration is handled exclusively by Alembic.
      Never call ``Base.metadata.create_all()`` in production code.
"""

from __future__ import annotations

import logging

from sqlalchemy import text

from app.db.session import get_engine

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Verify the database connection on application startup.

    Runs a lightweight ``SELECT 1`` to confirm the engine can reach
    the Supabase PostgreSQL instance.  Raises on connection failure so
    the application fails fast rather than accepting requests with a
    broken database.
    """
    engine = get_engine()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection established successfully")
    except Exception as exc:
        logger.error("❌ Database connection failed: %s", exc)
        raise
