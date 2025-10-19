"""
Main FastAPI application for Trading CLI API.

This module provides the FastAPI application instance with all routers,
middleware, and lifecycle event handlers.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.database import db_manager
from .core.redis import redis_manager
from .models.schemas import ErrorResponse
from .routers import health


# Create lifespan context manager for startup/shutdown


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.

    Handles startup and shutdown events for database and Redis connections.
    """
    # Startup
    print("🚀 Starting Trading CLI API...")

    # Initialize database
    print("📊 Connecting to database...")
    db_manager.create_async_engine()

    # Initialize Redis
    print("🔴 Connecting to Redis...")
    await redis_manager.connect()

    # Create result storage directory
    from pathlib import Path

    Path(settings.RESULT_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

    print("✅ Trading CLI API started successfully!")

    yield

    # Shutdown
    print("👋 Shutting down Trading CLI API...")

    # Close connections
    await redis_manager.disconnect()
    await db_manager.dispose()

    print("✅ Trading CLI API shut down successfully!")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Exception handlers


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors with detailed field information."""
    error_resp = ErrorResponse(
        error="Validation Error",
        detail=str(exc),
        code="VALIDATION_ERROR",
    )
    # Convert to dict and manually serialize datetime
    content = error_resp.model_dump()
    content["timestamp"] = (
        content["timestamp"].isoformat()
        if isinstance(content.get("timestamp"), datetime)
        else content.get("timestamp")
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=content,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    if settings.DEBUG:
        detail = str(exc)
    else:
        detail = "An unexpected error occurred"

    error_resp = ErrorResponse(
        error="Internal Server Error", detail=detail, code="INTERNAL_ERROR"
    )
    # Convert to dict and manually serialize datetime
    content = error_resp.model_dump()
    content["timestamp"] = (
        content["timestamp"].isoformat()
        if isinstance(content.get("timestamp"), datetime)
        else content.get("timestamp")
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content,
    )


# Configure OpenAPI schema with API key security
def custom_openapi():
    """
    Customize OpenAPI schema to include API key security scheme.

    This makes Swagger UI display an "Authorize" button where users
    can enter their API key once and have it applied to all requests.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add API key security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication. Use: dev-key-000000000000000000000000 for development.",
        }
    }

    # Apply security to all endpoints except health and root
    # Health endpoints are public, others require API key
    for path, path_item in openapi_schema["paths"].items():
        if not path.startswith("/health") and path != "/":
            for operation in path_item.values():
                if isinstance(operation, dict) and "operationId" in operation:
                    operation["security"] = [{"APIKeyHeader": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])

# Import and include completed routers
from .routers import concurrency, config, jobs, seasonality, strategy


app.include_router(jobs.router, prefix=f"{settings.API_V1_PREFIX}/jobs", tags=["Jobs"])
app.include_router(
    strategy.router, prefix=f"{settings.API_V1_PREFIX}/strategy", tags=["Strategy"]
)
app.include_router(
    config.router, prefix=f"{settings.API_V1_PREFIX}/config", tags=["Config"]
)
app.include_router(
    concurrency.router,
    prefix=f"{settings.API_V1_PREFIX}/concurrency",
    tags=["Concurrency"],
)
app.include_router(
    seasonality.router,
    prefix=f"{settings.API_V1_PREFIX}/seasonality",
    tags=["Seasonality"],
)

# TODO: Add more routers as they're implemented
# from .routers import portfolio, spds, trade_history, tools, positions
# app.include_router(portfolio.router, prefix=f"{settings.API_V1_PREFIX}/portfolio", tags=["Portfolio"])
# app.include_router(spds.router, prefix=f"{settings.API_V1_PREFIX}/spds", tags=["SPDS"])
# app.include_router(trade_history.router, prefix=f"{settings.API_V1_PREFIX}/trade-history", tags=["Trade History"])
# app.include_router(tools.router, prefix=f"{settings.API_V1_PREFIX}/tools", tags=["Tools"])
# app.include_router(positions.router, prefix=f"{settings.API_V1_PREFIX}/positions", tags=["Positions"])


# Root endpoint


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "docs_url": "/api/docs" if settings.DEBUG else None,
        "health_url": "/health",
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
