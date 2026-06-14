"""Redis client configuration and lifecycle management.

Provides a shared asynchronous Redis connection pool and client factory.
"""

import logging
from typing import AsyncGenerator

from redis.asyncio import Redis, ConnectionPool

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Global connection pool instance
_redis_pool: ConnectionPool | None = None


async def init_redis() -> None:
    """Initialize the Redis connection pool.
    
    This function should be called during application startup.
    It creates an asynchronous connection pool using the REDIS_URL from settings.
    """
    global _redis_pool
    if _redis_pool is not None:
        logger.warning("Redis pool is already initialized.")
        return

    settings = get_settings()
    logger.info("Initializing Redis connection pool...")
    
    try:
        _redis_pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            # Additional connection pool settings can be configured here
        )
        logger.info("Redis connection pool initialized.")
    except Exception as e:
        logger.exception("Failed to initialize Redis connection pool")
        raise


async def close_redis() -> None:
    """Close the Redis connection pool.
    
    This function should be called during application shutdown to release
    all open connections.
    """
    global _redis_pool
    if _redis_pool is None:
        return

    logger.info("Closing Redis connection pool...")
    try:
        await _redis_pool.disconnect()
        logger.info("Redis connection pool closed.")
    except Exception as e:
        logger.exception("Error while closing Redis connection pool")
    finally:
        _redis_pool = None


async def get_redis() -> AsyncGenerator[Redis, None]:
    """Dependency injection function to get a Redis client.
    
    Yields an asynchronous Redis client from the connection pool.
    """
    if _redis_pool is None:
        raise RuntimeError("Redis connection pool is not initialized. Call init_redis() first.")
    
    client = Redis(connection_pool=_redis_pool)
    try:
        yield client
    finally:
        # Closing the client returns the connection to the pool
        await client.aclose()
