"""
ARQ task definitions for executing CLI commands.

This module defines all async task functions that are executed by the ARQ worker.
Each task corresponds to a CLI subcommand and handles job execution with
progress tracking and error handling.
"""

import asyncio
from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import select, update

from ..core.redis import redis_manager
from ..models.tables import Job, JobStatus
from ..services.command_services.strategy_service import StrategyService
from ..services.webhook_service import WebhookService
from .progress import ProgressTracker


async def update_job_status(db_manager, job_id: str, status: str, **kwargs) -> None:
    """Update job status in database and trigger webhooks on completion."""
    async with db_manager.get_async_session() as session:
        values = {"status": status}
        if status == JobStatus.RUNNING.value:
            values["started_at"] = datetime.utcnow()
        elif status in [
            JobStatus.COMPLETED.value,
            JobStatus.FAILED.value,
            JobStatus.CANCELLED.value,
        ]:
            values["completed_at"] = datetime.utcnow()

        values.update(kwargs)

        await session.execute(
            update(Job).where(Job.id == uuid.UUID(job_id)).values(**values),
        )
        await session.commit()

        # Trigger webhook if job is complete and has webhook_url
        if status in [
            JobStatus.COMPLETED.value,
            JobStatus.FAILED.value,
            JobStatus.CANCELLED.value,
        ]:
            # Fetch job with webhook details
            result = await session.execute(
                select(Job).where(Job.id == uuid.UUID(job_id)),
            )
            job = result.scalar_one_or_none()

            if job and job.webhook_url:
                # Send webhook asynchronously (don't block)
                asyncio.create_task(
                    WebhookService.notify_job_completion(db_manager, job),
                )


# Strategy Tasks


async def execute_strategy_run(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute strategy run command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)

        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        service = StrategyService(progress_tracker)

        from ..models.schemas import StrategyRunRequest

        request = StrategyRunRequest(**parameters)

        result = await service.execute_run(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )

        return result

    except Exception as e:
        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.FAILED.value,
            error_message=str(e),
        )
        raise


async def execute_strategy_sweep(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute strategy parameter sweep."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)

        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        service = StrategyService(progress_tracker)

        from ..models.schemas import StrategySweepRequest

        request = StrategySweepRequest(**parameters)

        result = await service.execute_sweep(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )

        return result

    except Exception as e:
        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.FAILED.value,
            error_message=str(e),
        )
        raise


async def execute_strategy_review(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute strategy review command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)

        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        service = StrategyService(progress_tracker)

        from ..models.schemas import StrategyReviewRequest

        request = StrategyReviewRequest(**parameters)

        result = await service.execute_review(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )

        return result

    except Exception as e:
        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.FAILED.value,
            error_message=str(e),
        )
        raise


async def execute_sector_compare(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute sector comparison analysis."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)

        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        service = StrategyService(progress_tracker)

        from ..models.schemas import SectorCompareRequest

        request = SectorCompareRequest(**parameters)

        result = await service.execute_sector_compare(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )

        return result

    except Exception as e:
        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.FAILED.value,
            error_message=str(e),
        )
        raise


# Config Tasks


async def execute_config_list(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute config list command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)

        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..services.command_services.config_service import ConfigService

        service = ConfigService(progress_tracker)

        from ..models.schemas import ConfigListRequest

        request = ConfigListRequest(**parameters)

        result = await service.execute_list(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )

        return result

    except Exception as e:
        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.FAILED.value,
            error_message=str(e),
        )
        raise


async def execute_config_show(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute config show command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)

        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..services.command_services.config_service import ConfigService

        service = ConfigService(progress_tracker)

        from ..models.schemas import ConfigShowRequest

        request = ConfigShowRequest(**parameters)

        result = await service.execute_show(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )

        return result

    except Exception as e:
        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.FAILED.value,
            error_message=str(e),
        )
        raise


async def execute_config_verify_defaults(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute config verify-defaults command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)

        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..services.command_services.config_service import ConfigService

        service = ConfigService(progress_tracker)

        from ..models.schemas import ConfigVerifyDefaultsRequest

        request = ConfigVerifyDefaultsRequest(**parameters)

        result = await service.execute_verify_defaults(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )

        return result

    except Exception as e:
        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.FAILED.value,
            error_message=str(e),
        )
        raise


async def execute_config_set_default(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute config set-default command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)

        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..services.command_services.config_service import ConfigService

        service = ConfigService(progress_tracker)

        from ..models.schemas import ConfigSetDefaultRequest

        request = ConfigSetDefaultRequest(**parameters)

        result = await service.execute_set_default(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )

        return result

    except Exception as e:
        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.FAILED.value,
            error_message=str(e),
        )
        raise


async def execute_config_edit(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute config edit command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)

        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..services.command_services.config_service import ConfigService

        service = ConfigService(progress_tracker)

        from ..models.schemas import ConfigEditRequest

        request = ConfigEditRequest(**parameters)

        result = await service.execute_edit(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )

        return result

    except Exception as e:
        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.FAILED.value,
            error_message=str(e),
        )
        raise


async def execute_config_validate(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute config validate command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)

        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..services.command_services.config_service import ConfigService

        service = ConfigService(progress_tracker)

        from ..models.schemas import ConfigValidateRequest

        request = ConfigValidateRequest(**parameters)

        result = await service.execute_validate(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )

        return result

    except Exception as e:
        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.FAILED.value,
            error_message=str(e),
        )
        raise


# Concurrency Tasks


async def execute_concurrency_analyze(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute concurrency analyze command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)
        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..models.schemas import ConcurrencyAnalyzeRequest
        from ..services.command_services.concurrency_service import ConcurrencyService

        service = ConcurrencyService(progress_tracker)
        request = ConcurrencyAnalyzeRequest(**parameters)
        result = await service.execute_analyze(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )
        return result
    except Exception as e:
        await update_job_status(
            ctx["db_manager"], job_id, JobStatus.FAILED.value, error_message=str(e),
        )
        raise


async def execute_concurrency_export(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute concurrency export command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)
        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..models.schemas import ConcurrencyExportRequest
        from ..services.command_services.concurrency_service import ConcurrencyService

        service = ConcurrencyService(progress_tracker)
        request = ConcurrencyExportRequest(**parameters)
        result = await service.execute_export(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )
        return result
    except Exception as e:
        await update_job_status(
            ctx["db_manager"], job_id, JobStatus.FAILED.value, error_message=str(e),
        )
        raise


async def execute_concurrency_review(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute concurrency review command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)
        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..models.schemas import ConcurrencyReviewRequest
        from ..services.command_services.concurrency_service import ConcurrencyService

        service = ConcurrencyService(progress_tracker)
        request = ConcurrencyReviewRequest(**parameters)
        result = await service.execute_review(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )
        return result
    except Exception as e:
        await update_job_status(
            ctx["db_manager"], job_id, JobStatus.FAILED.value, error_message=str(e),
        )
        raise


async def execute_concurrency_construct(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute concurrency construct command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)
        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..models.schemas import ConcurrencyConstructRequest
        from ..services.command_services.concurrency_service import ConcurrencyService

        service = ConcurrencyService(progress_tracker)
        request = ConcurrencyConstructRequest(**parameters)
        result = await service.execute_construct(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )
        return result
    except Exception as e:
        await update_job_status(
            ctx["db_manager"], job_id, JobStatus.FAILED.value, error_message=str(e),
        )
        raise


async def execute_concurrency_optimize(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute concurrency optimize command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)
        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..models.schemas import ConcurrencyOptimizeRequest
        from ..services.command_services.concurrency_service import ConcurrencyService

        service = ConcurrencyService(progress_tracker)
        request = ConcurrencyOptimizeRequest(**parameters)
        result = await service.execute_optimize(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )
        return result
    except Exception as e:
        await update_job_status(
            ctx["db_manager"], job_id, JobStatus.FAILED.value, error_message=str(e),
        )
        raise


async def execute_concurrency_monte_carlo(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute concurrency monte-carlo command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)
        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..models.schemas import ConcurrencyMonteCarloRequest
        from ..services.command_services.concurrency_service import ConcurrencyService

        service = ConcurrencyService(progress_tracker)
        request = ConcurrencyMonteCarloRequest(**parameters)
        result = await service.execute_monte_carlo(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )
        return result
    except Exception as e:
        await update_job_status(
            ctx["db_manager"], job_id, JobStatus.FAILED.value, error_message=str(e),
        )
        raise


async def execute_concurrency_health(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute concurrency health command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)
        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..models.schemas import ConcurrencyHealthRequest
        from ..services.command_services.concurrency_service import ConcurrencyService

        service = ConcurrencyService(progress_tracker)
        request = ConcurrencyHealthRequest(**parameters)
        result = await service.execute_health(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )
        return result
    except Exception as e:
        await update_job_status(
            ctx["db_manager"], job_id, JobStatus.FAILED.value, error_message=str(e),
        )
        raise


async def execute_concurrency_demo(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute concurrency demo command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)
        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..models.schemas import ConcurrencyDemoRequest
        from ..services.command_services.concurrency_service import ConcurrencyService

        service = ConcurrencyService(progress_tracker)
        request = ConcurrencyDemoRequest(**parameters)
        result = await service.execute_demo(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )
        return result
    except Exception as e:
        await update_job_status(
            ctx["db_manager"], job_id, JobStatus.FAILED.value, error_message=str(e),
        )
        raise


# Seasonality Tasks


async def execute_seasonality_run(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute seasonality run command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)
        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..models.schemas import SeasonalityRunRequest
        from ..services.command_services.seasonality_service import SeasonalityService

        service = SeasonalityService(progress_tracker)
        request = SeasonalityRunRequest(**parameters)
        result = await service.execute_run(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )
        return result
    except Exception as e:
        await update_job_status(
            ctx["db_manager"], job_id, JobStatus.FAILED.value, error_message=str(e),
        )
        raise


async def execute_seasonality_list(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute seasonality list command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)
        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..models.schemas import SeasonalityListRequest
        from ..services.command_services.seasonality_service import SeasonalityService

        service = SeasonalityService(progress_tracker)
        request = SeasonalityListRequest(**parameters)
        result = await service.execute_list(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )
        return result
    except Exception as e:
        await update_job_status(
            ctx["db_manager"], job_id, JobStatus.FAILED.value, error_message=str(e),
        )
        raise


async def execute_seasonality_results(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute seasonality results command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)
        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..models.schemas import SeasonalityResultsRequest
        from ..services.command_services.seasonality_service import SeasonalityService

        service = SeasonalityService(progress_tracker)
        request = SeasonalityResultsRequest(**parameters)
        result = await service.execute_results(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )
        return result
    except Exception as e:
        await update_job_status(
            ctx["db_manager"], job_id, JobStatus.FAILED.value, error_message=str(e),
        )
        raise


async def execute_seasonality_clean(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute seasonality clean command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)
        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..models.schemas import SeasonalityCleanRequest
        from ..services.command_services.seasonality_service import SeasonalityService

        service = SeasonalityService(progress_tracker)
        request = SeasonalityCleanRequest(**parameters)
        result = await service.execute_clean(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )
        return result
    except Exception as e:
        await update_job_status(
            ctx["db_manager"], job_id, JobStatus.FAILED.value, error_message=str(e),
        )
        raise


async def execute_seasonality_current(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute seasonality current command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)
        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..models.schemas import SeasonalityCurrentRequest
        from ..services.command_services.seasonality_service import SeasonalityService

        service = SeasonalityService(progress_tracker)
        request = SeasonalityCurrentRequest(**parameters)
        result = await service.execute_current(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )
        return result
    except Exception as e:
        await update_job_status(
            ctx["db_manager"], job_id, JobStatus.FAILED.value, error_message=str(e),
        )
        raise


async def execute_seasonality_portfolio(
    ctx: dict[str, Any], job_id: str, parameters: dict,
) -> dict:
    """Execute seasonality portfolio command."""
    try:
        await update_job_status(ctx["db_manager"], job_id, JobStatus.RUNNING.value)
        redis = await redis_manager.get_client()
        progress_tracker = ProgressTracker(job_id, redis)

        from ..models.schemas import SeasonalityPortfolioRequest
        from ..services.command_services.seasonality_service import SeasonalityService

        service = SeasonalityService(progress_tracker)
        request = SeasonalityPortfolioRequest(**parameters)
        result = await service.execute_portfolio(request)

        await update_job_status(
            ctx["db_manager"],
            job_id,
            JobStatus.COMPLETED.value,
            progress=100,
            result_data=result,
        )
        return result
    except Exception as e:
        await update_job_status(
            ctx["db_manager"], job_id, JobStatus.FAILED.value, error_message=str(e),
        )
        raise


# TODO: Add task functions for remaining command groups
# Portfolio Tasks (5)
# - execute_portfolio_update
# - execute_portfolio_process
# - execute_portfolio_aggregate
# - execute_portfolio_synthesize
# - execute_portfolio_review

# SPDS Tasks (7)
# - execute_spds_analyze
# - execute_spds_export
# - execute_spds_demo
# - execute_spds_health
# - execute_spds_configure
# - execute_spds_list_portfolios
# - execute_spds_interactive

# Trade History Tasks (6)
# - execute_trade_history_close
# - execute_trade_history_add
# - execute_trade_history_update
# - execute_trade_history_list
# - execute_trade_history_validate
# - execute_trade_history_health

# Tools Tasks (6)
# - execute_tools_schema
# - execute_tools_health
# - execute_tools_validate
# - execute_tools_export_ma_data
# - execute_tools_export_ma_data_sweep
# - execute_tools_pinescript

# Positions Tasks (5)
# - execute_positions_list
# - execute_positions_equity
# - execute_positions_validate
# - execute_positions_validate_equity
# - execute_positions_info
