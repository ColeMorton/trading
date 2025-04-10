"""
API Server Runner

This script runs the FastAPI application using Uvicorn.
"""

import os
import uvicorn
import argparse
from app.api.config import get_config

def main():
    """Run the API server."""
    parser = argparse.ArgumentParser(description="Run the API server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    config = get_config()
    os.makedirs(config["LOG_DIR"], exist_ok=True)
    
    print(f"Starting API server at http://{args.host}:{args.port}")
    print(f"API documentation available at http://{args.host}:{args.port}/docs")
    
    # Run the server
    uvicorn.run(
        "app.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level
    )

if __name__ == "__main__":
    main()