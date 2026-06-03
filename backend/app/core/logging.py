"""Structured logging configuration using structlog.

Provides consistent, context-aware log output:
  - JSON format in production (machine-parseable, log aggregator ready)
  - Human-readable colored output in development
  - Request-ID context propagation through all log events in a request lifecycle
  - Configurable log level via LOG_LEVEL environment variable

Usage
-----
Call ``setup_logging()`` once at application startup (inside the lifespan).
Use ``get_logger(__name__)`` everywhere else.

Context variables (set per-request by RequestIdMiddleware):
  - request_id  : UUID string injected by middleware
  - method      : HTTP method
  - path        : URL path
"""

from __future__ import annotations

import logging
import sys

import structlog

from app.core.config import get_settings


def setup_logging() -> None:
    """Configure structlog for the application.

    Called once during application startup.  Subsequent calls are
    idempotent because structlog is already configured.
    """
    settings = get_settings()

    # Processors applied before rendering — shared between stdlib and structlog
    shared_processors: list[structlog.types.Processor] = [
        # Merge context variables bound via structlog.contextvars (request-ID etc.)
        structlog.contextvars.merge_contextvars,
        # Add the logger name (module path) to every event
        structlog.stdlib.add_logger_name,
        # Add the log level string ("info", "error", etc.)
        structlog.stdlib.add_log_level,
        # Support %s-style positional arguments in log messages
        structlog.stdlib.PositionalArgumentsFormatter(),
        # ISO-8601 timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Render exception tracebacks inline
        structlog.processors.StackInfoRenderer(),
        structlog.processors.ExceptionRenderer(),
    ]

    # Choose renderer based on environment
    if settings.is_development:
        # Colored, human-readable output — easier to read during local development
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.plain_traceback,
        )
    else:
        # Compact JSON — ingest into Render log drain / Datadog / Grafana
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        # Processors that only run inside the stdlib formatter
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        # Foreign pre-chain for log records NOT originating from structlog
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Apply to root logger — all stdlib loggers inherit this
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Silence noisy third-party loggers unless in DEBUG mode
    if not settings.DEBUG:
        for logger_name in (
            "uvicorn.access",
            "httpx",
            "httpcore",
            "asyncpg",
        ):
            logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a named structlog logger.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A BoundLogger that supports context-variable propagation.
    """
    return structlog.get_logger(name)  # type: ignore[return-value]
