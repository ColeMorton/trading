"""
API Server Main Module

This module initializes and configures the FastAPI application for the API server.
It sets up routing, middleware, and error handling.
"""

import os

import strawberry
import yaml
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from strawberry.fastapi import GraphQLRouter

from app.api.async_messaging import (
    operation_queue,
    progress_stream_handler,
    submit_data_analysis,
    submit_portfolio_optimization,
)
from app.api.dependencies import (
    configure_dependencies,
    configure_enhanced_dependencies,
    get_container_health,
    get_container_registrations,
)
from app.api.event_bus import TradingEvents, event_bus, publish_event
from app.api.graphql.context import get_graphql_context
from app.api.graphql.schema import schema
from app.api.migration_strategy import migration_guide, migration_planner
from app.api.routers import data, health, ma_cross, scripts, sensylate, viewer
from app.api.service_patterns import service_orchestrator
from app.api.utils.logging import setup_api_logging
from app.api.v1.main import v1_app
from app.api.versioning import APIVersion, version_manager, version_middleware
from app.database.config import (
    database_health_check,
    shutdown_database,
    startup_database,
)

# Define paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CSV_VIEWER_DIR = os.path.join(BASE_DIR, "app", "csv_viewer")
SENSYLATE_DIR = os.path.join(BASE_DIR, "app", "sensylate")
SENSYLATE_DIST_DIR = os.path.join(SENSYLATE_DIR, "dist")
OPENAPI_YAML_PATH = os.path.join(os.path.dirname(__file__), "openapi.yaml")


def load_openapi_spec():
    """Load the custom OpenAPI specification from yaml file."""
    try:
        with open(OPENAPI_YAML_PATH, "r", encoding="utf-8") as f:
            openapi_spec = yaml.safe_load(f)
        return openapi_spec
    except Exception as e:
        print(f"Warning: Could not load custom OpenAPI spec: {e}")
        return None


# Load custom OpenAPI specification
custom_openapi = load_openapi_spec()

# Create FastAPI application with custom OpenAPI spec
if custom_openapi:
    app = FastAPI(
        title=custom_openapi.get("info", {}).get("title", "Trading API"),
        description=custom_openapi.get("info", {}).get(
            "description", "API for executing trading scripts and retrieving data"
        ),
        version=custom_openapi.get("info", {}).get("version", "0.1.0"),
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Override the OpenAPI schema
    def custom_openapi_schema():
        if app.openapi_schema:
            return app.openapi_schema
        app.openapi_schema = custom_openapi
        return app.openapi_schema

    app.openapi = custom_openapi_schema
else:
    # Fallback to default FastAPI configuration
    app = FastAPI(
        title="Trading API",
        description="API for executing trading scripts and retrieving data",
        version="0.1.0",
    )

# Set up logging
log, log_close, logger, _ = setup_api_logging()

# Configure dependency injection
configure_dependencies()
configure_enhanced_dependencies()

# Import security
from app.api.security import get_cors_origins, setup_security_middleware

# Set up security middleware
setup_security_middleware(app)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
)

# Add versioning middleware
app.middleware("http")(version_middleware)


# Custom middleware to handle specific 404 errors gracefully
@app.middleware("http")
async def handle_specific_404(request: Request, call_next):
    """
    Middleware to handle specific 404 errors gracefully.

    This middleware specifically catches requests to /viewer/last-modified
    and returns a 204 No Content response instead of a 404 error.
    """
    response = await call_next(request)

    # Check if this is a 404 for the /viewer/last-modified endpoint
    if response.status_code == 404 and request.url.path == "/viewer/last-modified":
        logger.info(
            f"Suppressing 404 for {request.url.path} - returning 204 No Content"
        )
        return JSONResponse(status_code=204, content=None)  # No Content

    return response


# Import GraphQL context
from app.api.graphql.context import get_graphql_context

# Create GraphQL router
graphql_app = GraphQLRouter(
    schema,
    graphiql=True,  # Enable GraphiQL interface for development
    context_getter=get_graphql_context,
)

# Mount versioned API applications
app.mount("/api/v1", v1_app)

# Include routers (for backward compatibility - these will be deprecated)
app.include_router(
    health.router, tags=["health", "legacy"]
)  # Health endpoints at root level
app.include_router(scripts.router, prefix="/api/scripts", tags=["scripts", "legacy"])
app.include_router(data.router, prefix="/api/data", tags=["data", "legacy"])
app.include_router(
    viewer.router, prefix="/viewer", tags=["viewer"]
)  # Keep non-API routes as-is
app.include_router(
    sensylate.router, prefix="/sensylate", tags=["sensylate"]
)  # Keep non-API routes as-is
app.include_router(ma_cross.router, prefix="/api/ma-cross", tags=["ma-cross", "legacy"])
app.include_router(graphql_app, prefix="/graphql", tags=["graphql"])

# Mount static files directories
app.mount("/static", StaticFiles(directory=CSV_VIEWER_DIR), name="static")

# Check if the dist directory exists before mounting
if os.path.exists(SENSYLATE_DIST_DIR):
    # For production, serve from the dist directory
    app.mount(
        "/sensylate-static",
        StaticFiles(directory=SENSYLATE_DIST_DIR),
        name="sensylate-static",
    )
else:
    # For development, serve from the src directory
    app.mount(
        "/sensylate-static",
        StaticFiles(directory=os.path.join(SENSYLATE_DIR, "src")),
        name="sensylate-static",
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for the API."""
    error_id = os.urandom(8).hex()
    logger.error(f"Error ID: {error_id} - {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An unexpected error occurred",
            "error_id": error_id,
            "detail": str(exc),
        },
    )


@app.get("/", tags=["root"])
async def root():
    """Root endpoint that returns basic API information."""
    return {
        "name": "Trading API",
        "version": "0.1.0",
        "description": "API for executing trading scripts and retrieving data",
        "api_versions": {
            "current": "v1",
            "supported": ["v1"],
            "deprecated": [],
            "links": {"v1": "/api/v1", "v1_docs": "/api/v1/docs"},
        },
    }


@app.get("/api/versions", tags=["versioning"])
async def get_api_versions():
    """Get information about all API versions."""
    versions = version_manager.get_all_versions()
    return {
        "versions": [
            {
                "version": v.version.value,
                "status": v.status.value,
                "introduced": v.introduced.isoformat(),
                "deprecated_date": v.deprecated_date.isoformat()
                if v.deprecated_date
                else None,
                "sunset_date": v.sunset_date.isoformat() if v.sunset_date else None,
                "migration_guide_url": v.migration_guide_url,
                "docs_url": f"/api/{v.version.value}/docs",
                "openapi_url": f"/api/{v.version.value}/openapi.json",
            }
            for v in versions
        ],
        "default_version": version_manager.default_version.value,
    }


@app.get("/api/migration/{from_version}/to/{to_version}", tags=["migration"])
async def get_migration_guide(from_version: str, to_version: str):
    """Get migration guide between two API versions."""
    try:
        from_ver = APIVersion(from_version)
        to_ver = APIVersion(to_version)
        return migration_guide.generate_migration_guide(from_ver, to_ver)
    except ValueError as e:
        return {"error": f"Invalid version: {str(e)}"}


@app.get("/api/deprecation/{version}", tags=["migration"])
async def get_deprecation_notice(version: str):
    """Get deprecation notice for a specific API version."""
    try:
        ver = APIVersion(version)
        return migration_guide.generate_deprecation_notice(ver)
    except ValueError as e:
        return {"error": f"Invalid version: {str(e)}"}


@app.get("/api/container/health", tags=["container"])
async def get_dependency_container_health():
    """Get health status of all services in the dependency container."""
    return await get_container_health()


@app.get("/api/container/registrations", tags=["container"])
async def get_dependency_container_registrations():
    """Get information about all service registrations in the dependency container."""
    return get_container_registrations()


@app.get("/api/services/health", tags=["services"])
async def get_services_health():
    """Get health status of all services managed by the service orchestrator."""
    return await service_orchestrator.health_check_all()


@app.post("/api/services/initialize", tags=["services"])
async def initialize_all_services():
    """Initialize all registered services."""
    try:
        await service_orchestrator.initialize_all()
        return {"status": "success", "message": "All services initialized"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/services/shutdown", tags=["services"])
async def shutdown_all_services():
    """Shutdown all services gracefully."""
    try:
        await service_orchestrator.shutdown_all()
        return {"status": "success", "message": "All services shutdown"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/events/metrics", tags=["events"])
async def get_event_bus_metrics():
    """Get event bus metrics."""
    return event_bus.get_metrics()


@app.get("/api/events/subscriptions", tags=["events"])
async def get_event_subscriptions():
    """Get information about current event subscriptions."""
    return event_bus.get_subscriptions()


@app.get("/api/events/history", tags=["events"])
async def get_event_history(limit: int = 50):
    """Get recent event history."""
    return event_bus.get_event_history(limit)


@app.post("/api/events/publish", tags=["events"])
async def publish_test_event(event_type: str, data: dict, source: str = "api"):
    """Publish a test event."""
    event_id = await publish_event(event_type, data, source)
    return {"event_id": event_id, "status": "published"}


@app.get("/api/operations/metrics", tags=["operations"])
async def get_operation_metrics():
    """Get operation queue metrics."""
    return operation_queue.get_metrics()


@app.get("/api/operations", tags=["operations"])
async def list_operations(status: str = None):
    """List operations with optional status filter."""
    from app.api.async_messaging import OperationStatus

    status_filter = None
    if status:
        try:
            status_filter = OperationStatus(status)
        except ValueError:
            return {"error": f"Invalid status: {status}"}

    operations = operation_queue.list_operations(status_filter)
    return [op.__dict__ for op in operations]


@app.get("/api/operations/{operation_id}", tags=["operations"])
async def get_operation_status(operation_id: str):
    """Get status of a specific operation."""
    result = operation_queue.get_operation_status(operation_id)
    if result:
        return result.__dict__
    return {"error": "Operation not found"}


@app.post("/api/operations/data-analysis", tags=["operations"])
async def start_data_analysis(dataset_size: int = 1000, timeout: int = 300):
    """Start a data analysis operation."""
    operation_id = await submit_data_analysis(dataset_size, timeout)
    return {"operation_id": operation_id, "status": "submitted"}


@app.post("/api/operations/portfolio-optimization", tags=["operations"])
async def start_portfolio_optimization(symbols: list, timeout: int = 600):
    """Start a portfolio optimization operation."""
    operation_id = await submit_portfolio_optimization(symbols, timeout)
    return {"operation_id": operation_id, "status": "submitted"}


@app.delete("/api/operations/{operation_id}", tags=["operations"])
async def cancel_operation(operation_id: str):
    """Cancel a running operation."""
    cancelled = await operation_queue.cancel_operation(operation_id)
    if cancelled:
        return {"status": "cancelled"}
    return {"error": "Operation not found or not cancellable"}


# Health endpoints are now handled by the health router


# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting Trading API application...")
    try:
        await startup_database()

        # Start event bus and operation queue
        await event_bus.start()
        await operation_queue.start()

        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down Trading API application...")
    try:
        # Stop event bus and operation queue
        await operation_queue.stop()
        await event_bus.stop()

        await shutdown_database()
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"Application shutdown failed: {e}")
        raise
