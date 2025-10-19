"""
ARQ worker configuration for async job processing.

This module configures the ARQ worker for processing trading CLI commands
asynchronously with Redis queue.
"""

from typing import Any

from arq import create_pool
from arq.connections import RedisSettings
from redis.asyncio import Redis

from ..core.config import settings
from ..core.database import db_manager


async def startup(ctx: dict[str, Any]) -> None:
    """
    Worker startup hook.

    Initializes shared resources like database connections.

    Args:
        ctx: Worker context dictionary
    """
    print("🔧 Initializing ARQ worker...")

    # Initialize database connection
    db_manager.create_async_engine()
    ctx["db_manager"] = db_manager

    # Create Redis client for progress tracking
    ctx["redis"] = await create_pool(
        RedisSettings.from_dsn(settings.REDIS_URL), encoding="utf-8"
    )

    print("✅ ARQ worker initialized successfully!")


async def shutdown(ctx: dict[str, Any]) -> None:
    """
    Worker shutdown hook.

    Cleans up resources.

    Args:
        ctx: Worker context dictionary
    """
    print("👋 Shutting down ARQ worker...")

    # Close Redis connection
    if "redis" in ctx:
        await ctx["redis"].close()

    # Close database connections
    if "db_manager" in ctx:
        await ctx["db_manager"].dispose()

    print("✅ ARQ worker shut down successfully!")


# Worker settings
class WorkerSettings:
    """ARQ worker configuration."""

    # Redis connection
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)

    # Queue configuration
    queue_name = settings.ARQ_QUEUE_NAME
    max_jobs = settings.MAX_CONCURRENT_JOBS
    job_timeout = settings.JOB_TIMEOUT
    max_tries = settings.JOB_RETRY_ATTEMPTS

    # Lifecycle hooks
    on_startup = startup
    on_shutdown = shutdown

    # Task functions
    from .tasks import (
        execute_concurrency_analyze,
        execute_concurrency_construct,
        execute_concurrency_demo,
        execute_concurrency_export,
        execute_concurrency_health,
        execute_concurrency_monte_carlo,
        execute_concurrency_optimize,
        execute_concurrency_review,
        execute_config_edit,
        execute_config_list,
        execute_config_set_default,
        execute_config_show,
        execute_config_validate,
        execute_config_verify_defaults,
        execute_seasonality_clean,
        execute_seasonality_current,
        execute_seasonality_list,
        execute_seasonality_portfolio,
        execute_seasonality_results,
        execute_seasonality_run,
        execute_sector_compare,
        execute_strategy_review,
        execute_strategy_run,
        execute_strategy_sweep,
    )

    functions = [
        # Strategy tasks
        execute_strategy_run,
        execute_strategy_sweep,
        execute_strategy_review,
        execute_sector_compare,
        # Config tasks
        execute_config_list,
        execute_config_show,
        execute_config_verify_defaults,
        execute_config_set_default,
        execute_config_edit,
        execute_config_validate,
        # Concurrency tasks
        execute_concurrency_analyze,
        execute_concurrency_export,
        execute_concurrency_review,
        execute_concurrency_construct,
        execute_concurrency_optimize,
        execute_concurrency_monte_carlo,
        execute_concurrency_health,
        execute_concurrency_demo,
        # Seasonality tasks
        execute_seasonality_run,
        execute_seasonality_list,
        execute_seasonality_results,
        execute_seasonality_clean,
        execute_seasonality_current,
        execute_seasonality_portfolio,
        # TODO: Add remaining task functions as they're implemented
    ]

    # Health check interval
    health_check_interval = 60

    # Worker configuration
    allow_abort_jobs = True
    log_results = bool(settings.DEBUG)


# Convenience function to create worker pool
async def create_worker_pool() -> Redis:
    """
    Create ARQ worker Redis pool.

    Returns:
        Redis pool for ARQ
    """
    return await create_pool(
        RedisSettings.from_dsn(settings.REDIS_URL), encoding="utf-8"
    )
