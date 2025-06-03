"""
API Version 1 Main Module

This module creates and configures the FastAPI application for API version 1.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.versioning import APIVersion, create_versioned_app
from app.api.security import setup_security_middleware, get_cors_origins
from app.api.v1.routers import (
    scripts_router,
    data_router,
    ma_cross_router,
    health_router
)


def create_v1_app() -> FastAPI:
    """Create and configure the v1 API application."""
    
    # Create versioned app
    app = create_versioned_app(APIVersion.V1)
    
    # Set up security middleware
    setup_security_middleware(app)
    
    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Page", "X-Per-Page", "API-Version"],
    )
    
    # Include v1 routers (without /api prefix since they're already under /api/v1)
    app.include_router(health_router, tags=["health", "v1"])
    app.include_router(scripts_router, prefix="/scripts", tags=["scripts", "v1"])
    app.include_router(data_router, prefix="/data", tags=["data", "v1"])
    app.include_router(ma_cross_router, prefix="/ma-cross", tags=["ma-cross", "v1"])
    
    @app.get("/", tags=["root", "v1"])
    async def v1_root():
        """V1 API root endpoint."""
        return {
            "name": "Trading API v1",
            "version": "1.0.0",
            "api_version": "v1",
            "description": "Trading API version 1 - Current stable version"
        }
    
    return app


# Create the v1 app instance
v1_app = create_v1_app()