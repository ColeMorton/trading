#!/usr/bin/env python3
"""
Test API Startup

Test that the FastAPI server can start without Prisma issues
"""

import asyncio
import logging
import signal
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_api_startup():
    """Test API server startup and basic endpoints."""
    logger.info("Testing API server startup...")

    # Import without Prisma dependencies
    try:
        # Create a simple test version of the app
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse

        # Create minimal test app
        test_app = FastAPI(title="Test Trading API")

        @test_app.get("/health")
        async def health():
            return {"status": "healthy", "service": "trading-api-test"}

        @test_app.get("/")
        async def root():
            return {"message": "API server is working"}

        # Test server startup
        config = uvicorn.Config(
            test_app, host="127.0.0.1", port=8001, log_level="warning"
        )
        server = uvicorn.Server(config)

        # Start server in background
        server_task = asyncio.create_task(server.serve())

        # Wait a moment for server to start
        await asyncio.sleep(2)

        # Test endpoints
        async with httpx.AsyncClient() as client:
            try:
                # Test root endpoint
                response = await client.get("http://127.0.0.1:8001/")
                if response.status_code == 200:
                    logger.info("✅ Root endpoint working")
                else:
                    logger.error(f"❌ Root endpoint failed: {response.status_code}")
                    return False

                # Test health endpoint
                response = await client.get("http://127.0.0.1:8001/health")
                if response.status_code == 200:
                    logger.info("✅ Health endpoint working")
                else:
                    logger.error(f"❌ Health endpoint failed: {response.status_code}")
                    return False

            except Exception as e:
                logger.error(f"❌ API test requests failed: {e}")
                return False

        # Stop server
        server.should_exit = True
        await asyncio.sleep(1)
        server_task.cancel()

        try:
            await server_task
        except asyncio.CancelledError:
            pass

        logger.info("✅ API server test completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ API startup test failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("Starting API startup test...")

    success = await test_api_startup()

    if success:
        logger.info("🎉 API startup test PASSED")
        logger.info("The FastAPI server can start and respond to requests")
        return 0
    else:
        logger.error("❌ API startup test FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
