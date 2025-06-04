#!/usr/bin/env python3
"""
Simple Database Test

Test basic database connectivity without Prisma
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
import redis.asyncio as redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleSettings:
    """Simple settings without Prisma dependency."""

    def __init__(self):
        # Load from environment or use defaults
        self.database_url = os.getenv(
            "DATABASE_URL", "postgresql://colemorton@localhost:5432/trading_db"
        )
        self.database_host = os.getenv("DATABASE_HOST", "localhost")
        self.database_port = int(os.getenv("DATABASE_PORT", "5432"))
        self.database_name = os.getenv("DATABASE_NAME", "trading_db")
        self.database_user = os.getenv("DATABASE_USER", "colemorton")
        self.database_password = os.getenv("DATABASE_PASSWORD", "")

        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_password = os.getenv("REDIS_PASSWORD")


async def test_database_connectivity():
    """Test database connectivity without Prisma."""
    settings = SimpleSettings()

    logger.info("Testing database connectivity...")

    # Test PostgreSQL
    try:
        # Use asyncpg directly
        conn = await asyncpg.connect(settings.database_url)

        # Test connection
        result = await conn.fetchval("SELECT version()")
        logger.info(f"✅ PostgreSQL connected: {result}")

        # Test if database exists
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", settings.database_name
        )

        if db_exists:
            logger.info(f"✅ Database '{settings.database_name}' exists")
        else:
            logger.warning(f"⚠️  Database '{settings.database_name}' does not exist")

        await conn.close()

    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        return False

    # Test Redis
    try:
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            decode_responses=True,
        )

        # Test connection
        await redis_client.ping()
        logger.info("✅ Redis connected successfully")

        # Test basic operations
        await redis_client.set("test_key", "test_value")
        value = await redis_client.get("test_key")

        if value == "test_value":
            logger.info("✅ Redis operations working")
        else:
            logger.error("❌ Redis operations failed")
            return False

        await redis_client.delete("test_key")
        await redis_client.close()

    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False

    logger.info("🎉 All database connectivity tests passed!")
    return True


async def create_basic_schema():
    """Create basic database schema using raw SQL."""
    settings = SimpleSettings()

    logger.info("Creating basic database schema...")

    try:
        conn = await asyncpg.connect(settings.database_url)

        # Create a simple test table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS health_check (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT NOW(),
                status TEXT NOT NULL
            )
        """
        )

        # Insert a test record
        await conn.execute(
            "INSERT INTO health_check (status) VALUES ($1)", "Database setup successful"
        )

        # Verify the table
        count = await conn.fetchval("SELECT COUNT(*) FROM health_check")
        logger.info(f"✅ Test table created with {count} records")

        await conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Schema creation failed: {e}")
        return False


async def test_api_startup():
    """Test if we can start the API without Prisma."""
    logger.info("Testing API startup...")

    try:
        # Import FastAPI app
        from app.api.main import app

        logger.info("✅ FastAPI app imported successfully")

        # Try to start with minimal config
        import uvicorn

        # Start server in a way that doesn't block
        config = uvicorn.Config(app, host="127.0.0.1", port=8001, log_level="info")
        server = uvicorn.Server(config)

        logger.info("✅ API server configuration successful")
        logger.info("Note: Not actually starting server to avoid blocking")

        return True

    except Exception as e:
        logger.error(f"❌ API startup test failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("Starting simple database tests...")

    # Test connectivity
    if not await test_database_connectivity():
        logger.error("Database connectivity tests failed")
        return 1

    # Test schema creation
    if not await create_basic_schema():
        logger.error("Schema creation tests failed")
        return 1

    # Test API startup (without Prisma)
    if not await test_api_startup():
        logger.warning("API startup test failed (expected due to Prisma dependency)")

    logger.info("✅ Basic tests passed! Database connectivity is working.")
    logger.info("\nNext steps:")
    logger.info("1. Fix Prisma client generation issue")
    logger.info("2. Run: poetry run prisma generate")
    logger.info("3. Create database schema: poetry run prisma db push")
    logger.info("4. Start the API server: make dev-local")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
