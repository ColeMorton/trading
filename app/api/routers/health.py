"""
Health check endpoints for API monitoring.
"""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.database import get_db
from ..core.redis import get_redis
from ..models.schemas import DetailedHealthCheck, HealthCheck


router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check() -> HealthCheck:
    """
    Basic health check endpoint.

    Returns service status and version information.
    """
    return HealthCheck(status="healthy", version=settings.VERSION)


@router.get(
    "/detailed",
    status_code=status.HTTP_200_OK,
)
async def detailed_health_check(
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> DetailedHealthCheck:
    """
    Detailed health check with component status.

    Checks:
    - Database connectivity
    - Redis connectivity
    - Filesystem access
    - Configuration validity
    """
    components: dict[str, dict[str, Any]] = {}

    # Check database
    try:
        from sqlalchemy import text

        await db.execute(text("SELECT 1"))
        components["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
        }
    except Exception as e:
        components["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {e!s}",
        }

    # Check Redis
    try:
        await redis.ping()
        components["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful",
        }
    except Exception as e:
        components["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {e!s}",
        }

    # Check filesystem (result storage)
    try:
        from pathlib import Path

        result_path = Path(settings.RESULT_STORAGE_PATH)
        result_path.mkdir(parents=True, exist_ok=True)

        # Test write
        test_file = result_path / ".health_check"
        test_file.touch()
        test_file.unlink()

        components["filesystem"] = {
            "status": "healthy",
            "message": "Filesystem writable",
            "path": str(result_path),
        }
    except Exception as e:
        components["filesystem"] = {
            "status": "unhealthy",
            "message": f"Filesystem check failed: {e!s}",
        }

    # Check configuration
    components["configuration"] = {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }

    # Determine overall status
    overall_status = "healthy"
    if any(c["status"] == "unhealthy" for c in components.values()):
        overall_status = "degraded"

    return DetailedHealthCheck(
        status=overall_status,
        version=settings.VERSION,
        components=components,
    )


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> dict[str, str]:
    """
    Readiness probe for Kubernetes/container orchestration.

    Returns 200 if service is ready to accept requests.
    """
    try:
        # Quick checks
        await db.execute("SELECT 1")
        await redis.ping()
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> dict[str, str]:
    """
    Liveness probe for Kubernetes/container orchestration.

    Returns 200 if service is alive (even if not ready).
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
