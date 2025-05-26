"""
API Server Main Module

This module initializes and configures the FastAPI application for the API server.
It sets up routing, middleware, and error handling.
"""

import os
import yaml
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routers import scripts, data, viewer, sensylate, ma_cross
from app.api.utils.logging import setup_api_logging

# Define paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CSV_VIEWER_DIR = os.path.join(BASE_DIR, 'app', 'csv_viewer')
SENSYLATE_DIR = os.path.join(BASE_DIR, 'app', 'sensylate')
SENSYLATE_DIST_DIR = os.path.join(SENSYLATE_DIR, 'dist')
OPENAPI_YAML_PATH = os.path.join(os.path.dirname(__file__), 'openapi.yaml')

def load_openapi_spec():
    """Load the custom OpenAPI specification from yaml file."""
    try:
        with open(OPENAPI_YAML_PATH, 'r', encoding='utf-8') as f:
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
        title=custom_openapi.get('info', {}).get('title', 'Trading API'),
        description=custom_openapi.get('info', {}).get('description', 'API for executing trading scripts and retrieving data'),
        version=custom_openapi.get('info', {}).get('version', '0.1.0'),
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc"
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
        version="0.1.0"
    )

# Set up logging
log, log_close, logger, _ = setup_api_logging()

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        logger.info(f"Suppressing 404 for {request.url.path} - returning 204 No Content")
        return JSONResponse(
            status_code=204,  # No Content
            content=None
        )
    
    return response

# Include routers
app.include_router(scripts.router, prefix="/api/scripts", tags=["scripts"])
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(viewer.router, prefix="/viewer", tags=["viewer"])
app.include_router(sensylate.router, prefix="/sensylate", tags=["sensylate"])
app.include_router(ma_cross.router, prefix="/api/ma-cross", tags=["ma-cross"])

# Mount static files directories
app.mount("/static", StaticFiles(directory=CSV_VIEWER_DIR), name="static")

# Check if the dist directory exists before mounting
if os.path.exists(SENSYLATE_DIST_DIR):
    # For production, serve from the dist directory
    app.mount("/sensylate-static", StaticFiles(directory=SENSYLATE_DIST_DIR), name="sensylate-static")
else:
    # For development, serve from the src directory
    app.mount("/sensylate-static", StaticFiles(directory=os.path.join(SENSYLATE_DIR, 'src')), name="sensylate-static")

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
            "detail": str(exc)
        }
    )

@app.get("/", tags=["root"])
async def root():
    """Root endpoint that returns basic API information."""
    return {
        "name": "Trading API",
        "version": "0.1.0",
        "description": "API for executing trading scripts and retrieving data"
    }

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}