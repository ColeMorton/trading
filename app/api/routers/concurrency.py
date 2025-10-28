"""
Concurrency analysis endpoints.

This router provides endpoints for concurrency analysis and strategy optimization.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import APIKey, require_scope
from ..models.schemas import (
    ConcurrencyAnalyzeRequest,
    ConcurrencyConstructRequest,
    ConcurrencyDemoRequest,
    ConcurrencyExportRequest,
    ConcurrencyHealthRequest,
    ConcurrencyMonteCarloRequest,
    ConcurrencyOptimizeRequest,
    ConcurrencyReviewRequest,
    JobResponse,
)
from ..services.job_service import JobService
from ..services.queue_service import enqueue_job
from typing import Annotated


router = APIRouter()


@router.post("/analyze", response_model=JobResponse)
async def concurrency_analyze(
    request: ConcurrencyAnalyzeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(require_scope("concurrency"))],
):
    """
    Execute comprehensive concurrency analysis.

    Analyzes concurrent exposure between strategies and calculates risk concentration.

    **Webhook Support:**
    Include `webhook_url` in request to receive a callback when analysis completes.
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="concurrency",
        command_name="analyze",
        parameters=request.model_dump(),
        webhook_url=request.webhook_url,
        webhook_headers=request.webhook_headers,
    )

    await enqueue_job("concurrency", "analyze", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/export", response_model=JobResponse)
async def concurrency_export(
    request: ConcurrencyExportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(require_scope("concurrency"))],
):
    """
    Export trade history data from portfolio analysis.

    **Webhook Support:**
    Include `webhook_url` in request to receive a callback when export completes.
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="concurrency",
        command_name="export",
        parameters=request.model_dump(),
        webhook_url=request.webhook_url,
        webhook_headers=request.webhook_headers,
    )

    await enqueue_job("concurrency", "export", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/review", response_model=JobResponse)
async def concurrency_review(
    request: ConcurrencyReviewRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(require_scope("concurrency"))],
):
    """
    Portfolio interaction analysis with visualization.

    **Webhook Support:**
    Include `webhook_url` in request to receive a callback when review completes.
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="concurrency",
        command_name="review",
        parameters=request.model_dump(),
        webhook_url=request.webhook_url,
        webhook_headers=request.webhook_headers,
    )

    await enqueue_job("concurrency", "review", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/construct", response_model=JobResponse)
async def concurrency_construct(
    request: ConcurrencyConstructRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(require_scope("concurrency"))],
):
    """
    Construct optimized portfolios from strategy selection.

    **Webhook Support:**
    Include `webhook_url` in request to receive a callback when construction completes.
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="concurrency",
        command_name="construct",
        parameters=request.model_dump(),
        webhook_url=request.webhook_url,
        webhook_headers=request.webhook_headers,
    )

    await enqueue_job("concurrency", "construct", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/optimize", response_model=JobResponse)
async def concurrency_optimize(
    request: ConcurrencyOptimizeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(require_scope("concurrency"))],
):
    """
    Find optimal strategy combinations using permutation analysis.

    This is a long-running operation that tests multiple combinations.

    **Webhook Support:**
    Include `webhook_url` in request to receive a callback when optimization completes.
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="concurrency",
        command_name="optimize",
        parameters=request.model_dump(),
        webhook_url=request.webhook_url,
        webhook_headers=request.webhook_headers,
    )

    await enqueue_job("concurrency", "optimize", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/monte-carlo", response_model=JobResponse)
async def concurrency_monte_carlo(
    request: ConcurrencyMonteCarloRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(require_scope("concurrency"))],
):
    """
    Run Monte Carlo simulations for risk analysis and forecasting.

    This is a long-running operation that may take several minutes.

    **Webhook Support:**
    Include `webhook_url` in request to receive a callback when simulation completes.
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="concurrency",
        command_name="monte_carlo",
        parameters=request.model_dump(),
        webhook_url=request.webhook_url,
        webhook_headers=request.webhook_headers,
    )

    await enqueue_job("concurrency", "monte_carlo", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/health", response_model=JobResponse)
async def concurrency_health(
    request: ConcurrencyHealthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(require_scope("concurrency"))],
):
    """
    Check concurrency analysis system health.

    **Webhook Support:**
    Include `webhook_url` in request to receive a callback when health check completes.
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="concurrency",
        command_name="health",
        parameters=request.model_dump(),
        webhook_url=request.webhook_url,
        webhook_headers=request.webhook_headers,
    )

    await enqueue_job("concurrency", "health", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/demo", response_model=JobResponse)
async def concurrency_demo(
    request: ConcurrencyDemoRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(require_scope("concurrency"))],
):
    """
    Run demo analysis with sample portfolio data.

    **Webhook Support:**
    Include `webhook_url` in request to receive a callback when demo completes.
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="concurrency",
        command_name="demo",
        parameters=request.model_dump(),
        webhook_url=request.webhook_url,
        webhook_headers=request.webhook_headers,
    )

    await enqueue_job("concurrency", "demo", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )
