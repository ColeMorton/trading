"""
Config management endpoints.

This router provides endpoints for configuration and profile management.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import APIKey, require_scope
from ..models.schemas import (
    ConfigEditRequest,
    ConfigListRequest,
    ConfigSetDefaultRequest,
    ConfigShowRequest,
    ConfigValidateRequest,
    ConfigVerifyDefaultsRequest,
    JobResponse,
)
from ..services.job_service import JobService
from ..services.queue_service import enqueue_job


router = APIRouter()


@router.post("/list", response_model=JobResponse)
async def config_list(
    request: ConfigListRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(require_scope("config"))],
):
    """
    List all available configuration profiles.

    Example:
    ```json
    {
        "detailed": false
    }
    ```
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="config",
        command_name="list",
        parameters=request.model_dump(),
    )

    await enqueue_job("config", "list", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/show", response_model=JobResponse)
async def config_show(
    request: ConfigShowRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(require_scope("config"))],
):
    """
    Show configuration details for a specific profile.

    Example:
    ```json
    {
        "profile_name": "ma_cross_crypto",
        "resolved": false,
        "format": "json"
    }
    ```
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="config",
        command_name="show",
        parameters=request.model_dump(),
    )

    await enqueue_job("config", "show", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/verify-defaults", response_model=JobResponse)
async def config_verify_defaults(
    request: ConfigVerifyDefaultsRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(require_scope("config"))],
):
    """
    Verify that required default configuration profiles exist.

    Example:
    ```json
    {}
    ```
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="config",
        command_name="verify_defaults",
        parameters=request.model_dump(),
    )

    await enqueue_job("config", "verify_defaults", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/set-default", response_model=JobResponse)
async def config_set_default(
    request: ConfigSetDefaultRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(require_scope("config"))],
):
    """
    Set the default configuration profile.

    Example:
    ```json
    {
        "profile_name": "ma_cross_crypto"
    }
    ```
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="config",
        command_name="set_default",
        parameters=request.model_dump(),
    )

    await enqueue_job("config", "set_default", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/edit", response_model=JobResponse)
async def config_edit(
    request: ConfigEditRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(require_scope("config"))],
):
    """
    Edit a configuration profile.

    Example:
    ```json
    {
        "profile_name": "ma_cross_crypto",
        "set_field": ["fast_period=10", "slow_period=50"]
    }
    ```
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="config",
        command_name="edit",
        parameters=request.model_dump(),
    )

    await enqueue_job("config", "edit", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post("/validate", response_model=JobResponse)
async def config_validate(
    request: ConfigValidateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(require_scope("config"))],
):
    """
    Validate configuration profiles.

    Example:
    ```json
    {
        "profile_name": "ma_cross_crypto",
        "detailed": true
    }
    ```
    """
    job = await JobService.create_job(
        db=db,
        api_key_id=api_key.id,
        command_group="config",
        command_name="validate",
        parameters=request.model_dump(),
    )

    await enqueue_job("config", "validate", str(job.id), request.model_dump())

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}",
    )
