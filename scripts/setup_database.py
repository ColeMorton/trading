#!/usr/bin/env python3
"""
Database Setup Script

This script sets up the complete database environment:
1. Generates Prisma client
2. Applies database schema
3. Runs data migration
4. Validates setup
"""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.migrations import run_migration
from prisma import Prisma

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_database():
    """Complete database setup process."""
    project_root = Path(__file__).parent.parent

    logger.info("Starting database setup...")

    try:
        # Step 1: Generate Prisma client
        logger.info("Step 1: Generating Prisma client...")
        result = subprocess.run(
            ["python", "-m", "prisma", "generate"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error(f"Prisma generate failed: {result.stderr}")
            return False

        logger.info("✅ Prisma client generated successfully")

        # Step 2: Apply database schema (push schema to database)
        logger.info("Step 2: Applying database schema...")
        result = subprocess.run(
            ["python", "-m", "prisma", "db", "push"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error(f"Prisma db push failed: {result.stderr}")
            return False

        logger.info("✅ Database schema applied successfully")

        # Step 3: Run data migration
        logger.info("Step 3: Running data migration...")
        try:
            await run_migration()
            logger.info("✅ Data migration completed successfully")
        except Exception as e:
            logger.error(f"Data migration failed: {e}")
            logger.info(
                "⚠️ You can run migration later with: python app/database/migrations.py"
            )

        # Step 4: Validate setup
        logger.info("Step 4: Validating database setup...")
        prisma = Prisma()
        await prisma.connect()

        # Check tables exist
        tables_result = await prisma.query_raw(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        )

        table_names = [row["table_name"] for row in tables_result]
        logger.info(f"✅ Database tables created: {', '.join(table_names)}")

        # Check some basic data
        strategy_count = await prisma.strategy.count()
        ticker_count = await prisma.ticker.count()

        logger.info(
            f"✅ Initial data: {strategy_count} strategies, {ticker_count} tickers"
        )

        await prisma.disconnect()

        logger.info("\n🎉 Database setup completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Start the application: docker-compose up")
        logger.info("2. Access health checks: http://localhost:8000/health/database")
        logger.info("3. View API docs: http://localhost:8000/docs")

        return True

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(setup_database())
    sys.exit(0 if success else 1)
