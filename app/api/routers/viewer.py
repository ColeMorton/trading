"""
CSV Viewer Router

This module provides API endpoints for the CSV viewer.
"""

import logging
import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.api.utils.logging import setup_api_logging

# Create router
router = APIRouter()

# Set up logging
log, _, logger, _ = setup_api_logging()

# Define templates directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CSV_VIEWER_DIR = os.path.join(BASE_DIR, "app", "csv_viewer")


@router.get(
    "/",
    response_class=HTMLResponse,
    summary="CSV Viewer",
    description="Web-based CSV viewer for displaying and analyzing CSV files.",
)
async def csv_viewer(request: Request):
    """
    Serve the CSV viewer HTML file.

    Args:
        request (Request): The incoming request

    Returns:
        HTMLResponse: The CSV viewer HTML page
    """
    try:
        log(f"Serving CSV viewer")

        # Read the HTML file
        html_path = os.path.join(CSV_VIEWER_DIR, "index.html")

        with open(html_path, "r") as f:
            html_content = f.read()

        return HTMLResponse(content=html_content)
    except Exception as e:
        log(f"Error serving CSV viewer: {str(e)}", "error")
        raise HTTPException(
            status_code=500, detail=f"Error serving CSV viewer: {str(e)}"
        )
