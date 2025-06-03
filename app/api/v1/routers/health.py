"""
Enhanced health check endpoints for production monitoring
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import asyncio
import psutil
import os
from app.database.config import get_prisma, get_redis, get_database_manager
from app.api.dependencies import get_current_version
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

async def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and performance"""
    try:
        start_time = datetime.now(timezone.utc)
        
        # Check Prisma connection
        db = await get_prisma()
        await db.query_raw("SELECT 1")
        
        # Check database manager for connection info
        db_manager = await get_database_manager()
        # Since we're using Prisma, we don't have direct pool access
        
        response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "database": "prisma_connected"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity and performance"""
    try:
        start_time = datetime.now(timezone.utc)
        
        redis = await get_redis()
        
        # Ping Redis
        await redis.ping()
        
        # Get Redis info
        info = await redis.info()
        
        response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "version": info.get("redis_version", "unknown"),
            "used_memory": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0)
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

def get_system_health() -> Dict[str, Any]:
    """Get system resource usage"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Process info
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        return {
            "status": "healthy",
            "cpu": {
                "usage_percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "process_rss": process_memory.rss,
                "process_vms": process_memory.vms
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "percent": disk.percent
            }
        }
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "trading-api"
    }

@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return {"status": "live"}

@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    # Check if essential services are ready
    checks = await asyncio.gather(
        check_database_health(),
        check_redis_health(),
        return_exceptions=True
    )
    
    # If any check failed, service is not ready
    for check in checks:
        if isinstance(check, Exception) or (isinstance(check, dict) and check.get("status") != "healthy"):
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready", "reason": str(check)}
            )
    
    return {"status": "ready"}

@router.get("/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check(version: str = Depends(get_current_version)):
    """Detailed health check with all subsystem statuses"""
    
    # Run all health checks concurrently
    checks = await asyncio.gather(
        check_database_health(),
        check_redis_health(),
        return_exceptions=True
    )
    
    database_health = checks[0] if not isinstance(checks[0], Exception) else {"status": "error", "error": str(checks[0])}
    redis_health = checks[1] if not isinstance(checks[1], Exception) else {"status": "error", "error": str(checks[1])}
    system_health = get_system_health()
    
    # Determine overall status
    overall_status = "healthy"
    if any(check.get("status") != "healthy" for check in [database_health, redis_health, system_health]):
        overall_status = "degraded"
    if all(check.get("status") == "unhealthy" for check in [database_health, redis_health]):
        overall_status = "unhealthy"
    
    response = {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": version,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "uptime_seconds": (datetime.now(timezone.utc) - datetime.fromtimestamp(psutil.boot_time(), timezone.utc)).total_seconds(),
        "checks": {
            "database": database_health,
            "redis": redis_health,
            "system": system_health
        }
    }
    
    # Set appropriate status code
    if overall_status == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response
        )
    elif overall_status == "degraded":
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response
        )
    
    return response

@router.get("/metrics", status_code=status.HTTP_200_OK)
async def metrics_endpoint():
    """Prometheus-compatible metrics endpoint"""
    metrics = []
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    metrics.extend([
        f"# HELP cpu_usage_percent CPU usage percentage",
        f"# TYPE cpu_usage_percent gauge",
        f"cpu_usage_percent {cpu_percent}",
        "",
        f"# HELP memory_usage_percent Memory usage percentage",
        f"# TYPE memory_usage_percent gauge", 
        f"memory_usage_percent {memory.percent}",
        "",
        f"# HELP disk_usage_percent Disk usage percentage",
        f"# TYPE disk_usage_percent gauge",
        f"disk_usage_percent {disk.percent}",
        ""
    ])
    
    # Database metrics
    try:
        pool = await get_asyncpg_pool()
        pool_size = pool.get_size()
        pool_free = pool.get_idle_size()
        
        metrics.extend([
            f"# HELP db_pool_size Database connection pool size",
            f"# TYPE db_pool_size gauge",
            f"db_pool_size {pool_size}",
            "",
            f"# HELP db_pool_free Database connection pool free connections",
            f"# TYPE db_pool_free gauge",
            f"db_pool_free {pool_free}",
            ""
        ])
    except:
        pass
    
    return "\n".join(metrics)