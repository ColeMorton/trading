"""
Seasonality analysis endpoints.

This router provides endpoints for seasonality pattern detection and analysis.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import APIKey, require_scope
from ..models.schemas import (
    JobResponse,
    SeasonalityCleanRequest,
    SeasonalityCurrentRequest,
    SeasonalityListRequest,
    SeasonalityPortfolioRequest,
    SeasonalityResultsRequest,
    SeasonalityRunRequest,
)
from ..services.job_service import JobService
from ..services.queue_service import enqueue_job


router = APIRouter()


@router.post("/run", response_model=JobResponse)
async def seasonality_run(
    request: SeasonalityRunRequest,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(require_scope("seasonality")),
):
    """
    Run seasonality analysis on stock price data.

    Analyzes historical price patterns to identify seasonal trends.
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="seasonality",
        command_name="run",
        parameters=request.model_dump(),
    )

    await enqueue_job("seasonality", "run", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/list", response_model=JobResponse)
async def seasonality_list(
    request: SeasonalityListRequest,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(require_scope("seasonality")),
):
    """List available tickers for seasonality analysis."""
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="seasonality",
        command_name="list",
        parameters=request.model_dump(),
    )

    await enqueue_job("seasonality", "list", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/results", response_model=JobResponse)
async def seasonality_results(
    request: SeasonalityResultsRequest,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(require_scope("seasonality")),
):
    """View seasonality analysis results for specific ticker."""
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="seasonality",
        command_name="results",
        parameters=request.model_dump(),
    )

    await enqueue_job("seasonality", "results", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/clean", response_model=JobResponse)
async def seasonality_clean(
    request: SeasonalityCleanRequest,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(require_scope("seasonality")),
):
    """Clean up seasonality results directory."""
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="seasonality",
        command_name="clean",
        parameters=request.model_dump(),
    )

    await enqueue_job("seasonality", "clean", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/current", response_model=JobResponse)
async def seasonality_current(
    request: SeasonalityCurrentRequest,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(require_scope("seasonality")),
):
    """
    Generate current seasonality expectancy analysis.

    Provides forward-looking analysis for trading opportunities based on seasonal patterns.
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="seasonality",
        command_name="current",
        parameters=request.model_dump(),
    )

    await enqueue_job("seasonality", "current", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/portfolio", response_model=JobResponse)
async def seasonality_portfolio(
    request: SeasonalityPortfolioRequest,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(require_scope("seasonality")),
):
    """
    Run seasonality analysis on all tickers in a portfolio.

    Uses intelligent time period determination based on signal entry data.
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="seasonality",
        command_name="portfolio",
        parameters=request.model_dump(),
    )

    await enqueue_job("seasonality", "portfolio", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )
