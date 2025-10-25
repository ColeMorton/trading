"""
Strategy command endpoints.

This router provides endpoints for all strategy-related commands:
- run: Execute single strategy analysis
- sweep: Parameter sweep optimization
- review: Detailed strategy review
- sector-compare: Cross-sector performance comparison
"""

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import APIKey, require_scope
from ..models.schemas import (
    JobResponse,
    SectorCompareRequest,
    StrategyReviewRequest,
    StrategyRunRequest,
    StrategySweepRequest,
)
from ..services.job_service import JobService
from ..services.queue_service import enqueue_job


router = APIRouter()


@router.post("/run", response_model=JobResponse)
async def strategy_run(
    request: StrategyRunRequest,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(require_scope("strategy")),
):
    """
    Execute strategy run command.

    Runs a backtest for a single set of parameters on a specific ticker.

    Example:
    ```json
    {
        "ticker": "BTC-USD",
        "fast_period": 20,
        "slow_period": 50,
        "strategy_type": "SMA",
        "direction": "Long",
        "webhook_url": "https://your-n8n.com/webhook/abc123"
    }
    ```

    **Webhook Support:**
    Include `webhook_url` to receive a callback when the job completes.
    """
    # Create job record
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="strategy",
        command_name="run",
        parameters=request.model_dump(),
        webhook_url=request.webhook_url,
        webhook_headers=request.webhook_headers,
    )

    # Enqueue to ARQ worker
    await enqueue_job("strategy", "run", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/sweep", response_model=JobResponse)
async def strategy_sweep(
    request: StrategySweepRequest = Body(...),
    # Dependencies
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(require_scope("strategy")),
):
    """
    Execute parameter sweep analysis.

    Tests multiple parameter combinations to find optimal settings.
    This is a long-running operation that always executes in the background.

    **Accepts both form-encoded and JSON data.**

    Form-encoded example (key-value pairs):
    ```
    ticker: "AAPL"
    fast_range_min: 5
    fast_range_max: 50
    slow_range_min: 10
    slow_range_max: 200
    min_trades: 50
    step: 5
    config_path: "app/cli/profiles/strategies/minimum.yaml"
    webhook_url: "https://your-n8n.com/webhook/abc123"
    ```

    JSON example:
    ```json
    {
        "ticker": "AAPL",
        "fast_range_min": 5,
        "fast_range_max": 50,
        "slow_range_min": 10,
        "slow_range_max": 200,
        "min_trades": 50,
        "step": 5,
        "webhook_url": "https://your-n8n.com/webhook/abc123"
    }
    ```

    Or with array format:
    ```json
    {
        "ticker": "AAPL",
        "fast_range": [5, 50],
        "slow_range": [10, 200],
        "step": 5,
        "webhook_url": "https://your-n8n.com/webhook/abc123"
    }
    ```

    **Webhook Support:**
    Include `webhook_url` to receive a callback when the sweep completes.
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="strategy",
        command_name="sweep",
        parameters=request.model_dump(),
        webhook_url=request.webhook_url,
        webhook_headers=request.webhook_headers,
    )

    # Enqueue to ARQ worker
    await enqueue_job("strategy", "sweep", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/review", response_model=JobResponse)
async def strategy_review(
    request: StrategyReviewRequest,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(require_scope("strategy")),
):
    """
    Execute detailed strategy review.

    Provides comprehensive analysis of a specific strategy configuration.

    Example:
    ```json
    {
        "ticker": "BTC-USD",
        "fast_period": 9,
        "slow_period": 21,
        "strategy_type": "SMA",
        "webhook_url": "https://your-n8n.com/webhook/abc123"
    }
    ```

    **Webhook Support:**
    Include `webhook_url` to receive a callback when the review completes.
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="strategy",
        command_name="review",
        parameters=request.model_dump(),
        webhook_url=request.webhook_url,
        webhook_headers=request.webhook_headers,
    )

    # Enqueue to ARQ worker
    await enqueue_job("strategy", "review", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/sector-compare", response_model=JobResponse)
async def sector_compare(
    request: SectorCompareRequest,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(require_scope("strategy")),
):
    """
    Compare strategy performance across sectors.

    Analyzes how strategies perform across different market sectors.

    Example:
    ```json
    {
        "output_format": "json",
        "webhook_url": "https://your-n8n.com/webhook/abc123"
    }
    ```

    **Webhook Support:**
    Include `webhook_url` to receive a callback when the comparison completes.
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="strategy",
        command_name="sector-compare",
        parameters=request.model_dump(),
        webhook_url=request.webhook_url,
        webhook_headers=request.webhook_headers,
    )

    # Enqueue to ARQ worker
    await enqueue_job("strategy", "sector_compare", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )
