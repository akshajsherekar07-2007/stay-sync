"""Alembic migrations environment — async configuration.

This file configures the Alembic migration context for StaySync's
async SQLAlchemy setup.  Key responsibilities:

1. Reads DATABASE_URL from Settings (environment variable) — never hardcoded.
2. Imports all ORM models so that ``Base.metadata`` is fully populated.
3. Supports both ``offline`` mode (generates SQL scripts) and ``online``
   mode (runs migrations against the live database using an async engine).
4. Uses ``run_sync`` to run synchronous Alembic operations inside the
   async engine context.

References
----------
- SQLAlchemy 2.0 async migration docs:
  https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── Import application components ─────────────────────────────────────────────
# Settings must be imported before Base so DATABASE_URL is available.
from app.core.config import get_settings

# Import Base — this registers all mapped tables in Base.metadata.
# Import models module to trigger all model class definitions.
from app.db.base import Base
import app.models  # noqa: F401 — side-effect import to populate Base.metadata

# ── Alembic Config ────────────────────────────────────────────────────────────
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with the value from the environment variable.
# This is the ONLY place DATABASE_URL is referenced — no hardcoded strings.
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Provide the metadata object for autogenerate support.
target_metadata = Base.metadata


# ── Offline mode ─────────────────────────────────────────────────────────────

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — generates SQL without a live DB.

    This configures the context with just a URL and not an Engine.
    Calls to context.execute() emit the given SQL string to the output.
    Useful for generating migration SQL to be reviewed before execution.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        # Render the batch migration support (required for SQLite; harmless on PG)
        render_as_batch=False,
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Online mode ───────────────────────────────────────────────────────────────

def do_run_migrations(connection: Connection) -> None:
    """Configure the migration context and run all pending migrations.

    Called inside an async context via ``run_sync``.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        # Include schemas — set to None to use the default schema only
        include_schemas=False,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations inside a sync context.

    SQLAlchemy's async engine does not support Alembic's synchronous
    migration runner directly, so we use ``run_sync`` to bridge the gap.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No connection pooling in migration scripts
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration mode."""
    asyncio.run(run_async_migrations())


# ── Entry point ───────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
