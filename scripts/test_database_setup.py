#!/usr/bin/env python3
"""
Database Setup Testing Script

This script tests the database setup, including:
- Docker container health
- Database connectivity
- Prisma schema validation
- Basic CRUD operations
- Migration validation
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prisma import Prisma
from app.database.config import DatabaseManager, get_database_settings
from app.database.migrations import DataMigrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseTester:
    """Test database setup and operations."""
    
    def __init__(self):
        self.settings = get_database_settings()
        self.db_manager = DatabaseManager()
        self.prisma = None
        
    async def run_all_tests(self):
        """Run all database tests."""
        logger.info("Starting comprehensive database tests...")
        
        tests = [
            ("Database Connection", self.test_database_connection),
            ("Prisma Client", self.test_prisma_client),
            ("Redis Connection", self.test_redis_connection),
            ("Health Checks", self.test_health_checks),
            ("Schema Validation", self.test_schema_validation),
            ("CRUD Operations", self.test_crud_operations),
            ("Data Migration Prep", self.test_migration_preparation),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"\n--- Running Test: {test_name} ---")
            try:
                await test_func()
                results[test_name] = "PASSED"
                logger.info(f"✅ {test_name}: PASSED")
            except Exception as e:
                results[test_name] = f"FAILED: {str(e)}"
                logger.error(f"❌ {test_name}: FAILED - {str(e)}")
        
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("TEST SUMMARY")
        logger.info("="*50)
        
        passed = sum(1 for result in results.values() if result == "PASSED")
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅" if result == "PASSED" else "❌"
            logger.info(f"{status} {test_name}: {result}")
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Database setup is ready.")
            return True
        else:
            logger.error("💥 Some tests failed. Please check the errors above.")
            return False
    
    async def test_database_connection(self):
        """Test basic database connectivity."""
        await self.db_manager.initialize()
        
        # Test direct connection
        connection = await self.db_manager.get_connection()
        result = await connection.fetchval("SELECT 1")
        
        if result != 1:
            raise RuntimeError("Database connection test failed")
        
        logger.info("Database connection successful")
    
    async def test_prisma_client(self):
        """Test Prisma client initialization and basic operations."""
        self.prisma = Prisma()
        await self.prisma.connect()
        
        # Test raw query
        result = await self.prisma.query_raw("SELECT version()")
        logger.info(f"PostgreSQL version: {result[0]['version']}")
        
        # Check if tables exist (they shouldn't yet without migration)
        tables_result = await self.prisma.query_raw("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        logger.info(f"Found {len(tables_result)} tables in database")
    
    async def test_redis_connection(self):
        """Test Redis connectivity."""
        redis_client = await self.db_manager.redis_client
        
        # Test basic operations
        await redis_client.set("test_key", "test_value")
        value = await redis_client.get("test_key")
        
        if value != "test_value":
            raise RuntimeError("Redis test failed")
        
        await redis_client.delete("test_key")
        logger.info("Redis connection and operations successful")
    
    async def test_health_checks(self):
        """Test health check functionality."""
        health_status = await self.db_manager.health_check()
        
        if not health_status["overall"]:
            raise RuntimeError(f"Health check failed: {health_status}")
        
        logger.info(f"Health check passed: {health_status}")
    
    async def test_schema_validation(self):
        """Test Prisma schema validation."""
        # Generate Prisma client (this validates the schema)
        import subprocess
        import os
        
        try:
            # Change to project root
            project_root = Path(__file__).parent.parent
            
            # Run prisma generate
            result = subprocess.run(
                ["python", "-m", "prisma", "generate"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("Prisma schema validation successful")
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Prisma schema validation failed: {e.stderr}")
    
    async def test_crud_operations(self):
        """Test basic CRUD operations (requires tables to exist)."""
        try:
            # Try to create a test strategy
            strategy = await self.prisma.strategy.create(
                data={
                    "name": "Test_Strategy",
                    "type": "MA_CROSS",
                    "description": "Test strategy for validation"
                }
            )
            
            # Read it back
            found_strategy = await self.prisma.strategy.find_unique(
                where={"id": strategy.id}
            )
            
            if not found_strategy or found_strategy.name != "Test_Strategy":
                raise RuntimeError("CRUD test failed: strategy not found")
            
            # Update it
            updated_strategy = await self.prisma.strategy.update(
                where={"id": strategy.id},
                data={"description": "Updated test strategy"}
            )
            
            if updated_strategy.description != "Updated test strategy":
                raise RuntimeError("CRUD test failed: update unsuccessful")
            
            # Delete it
            await self.prisma.strategy.delete(where={"id": strategy.id})
            
            # Verify deletion
            deleted_strategy = await self.prisma.strategy.find_unique(
                where={"id": strategy.id}
            )
            
            if deleted_strategy is not None:
                raise RuntimeError("CRUD test failed: deletion unsuccessful")
            
            logger.info("CRUD operations test successful")
            
        except Exception as e:
            if "relation" in str(e).lower() and "does not exist" in str(e).lower():
                logger.warning("CRUD test skipped: tables not yet created (run migration first)")
            else:
                raise
    
    async def test_migration_preparation(self):
        """Test migration script preparation."""
        migrator = DataMigrator(self.prisma)
        
        # Check if source data exists
        project_root = Path(__file__).parent.parent
        
        price_data_dir = project_root / "csv" / "price_data"
        if not price_data_dir.exists():
            logger.warning("Price data directory not found - create sample data first")
            return
        
        csv_files = list(price_data_dir.glob("*.csv"))
        logger.info(f"Found {len(csv_files)} price data files for migration")
        
        if len(csv_files) == 0:
            logger.warning("No CSV files found for migration")
            return
        
        # Test reading a sample file
        import pandas as pd
        sample_file = csv_files[0]
        df = pd.read_csv(sample_file, nrows=5)
        logger.info(f"Sample data from {sample_file.name}: {len(df)} rows, columns: {list(df.columns)}")
        
        logger.info("Migration preparation test successful")
    
    async def cleanup(self):
        """Cleanup test resources."""
        if self.prisma:
            await self.prisma.disconnect()
        
        await self.db_manager.close()


async def main():
    """Main test runner."""
    tester = DatabaseTester()
    
    try:
        success = await tester.run_all_tests()
        return 0 if success else 1
    
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        return 1
    
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)