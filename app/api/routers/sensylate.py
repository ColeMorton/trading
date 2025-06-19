"""
Sensylate Router

This module provides API endpoints for Sensylate - a sensitivity analysis tool for portfolio simulation and strategy creation.
"""

import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

from app.api.utils.logging import setup_api_logging

# Create router
router = APIRouter()

# Set up logging
log, _, logger, _ = setup_api_logging()

# Define directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SENSYLATE_DIR = os.path.join(BASE_DIR, "app", "frontend", "sensylate")
SENSYLATE_DIST_DIR = os.path.join(SENSYLATE_DIR, "dist")


@router.get(
    "/",
    response_class=HTMLResponse,
    summary="Sensylate",
    description="Sensitivity analysis meets portfolio simulation and strategy creation.",
)
async def sensylate(request: Request):
    """
    Serve the Sensylate application.

    Args:
        request (Request): The incoming request

    Returns:
        HTMLResponse or FileResponse: The Sensylate HTML page
    """
    try:
        log("Serving Sensylate application")

        # Check if we have a production build
        dist_html_path = os.path.join(SENSYLATE_DIST_DIR, "index.html")

        if os.path.exists(dist_html_path):
            # Use the production build
            return FileResponse(dist_html_path)

        # Fall back to the source file for development
        html_path = os.path.join(SENSYLATE_DIR, "src", "index.html")

        with open(html_path, "r") as f:
            html_content = f.read()

        return HTMLResponse(content=html_content)
    except Exception as e:
        log(f"Error serving Sensylate application: {str(e)}", "error")
        raise HTTPException(
            status_code=500, detail=f"Error serving Sensylate application: {str(e)}"
        )
