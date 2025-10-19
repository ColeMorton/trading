"""
Test CLI strategy sweep with database persistence.
"""
import asyncio
from app.database.config import db_manager


async def test_cli_with_database():
    """Initialize database then test CLI command."""
    print("🔧 Initializing database connection...")
    await db_manager.initialize()
    print("✅ Database initialized\n")
    
    # Now run the CLI command
    import subprocess
    import sys
    
    print("🚀 Running strategy sweep with --database flag...\n")
    result = subprocess.run(
        [
            sys.executable, "-m", "app.cli.main",
            "strategy", "sweep",
            "--ticker", "AAPL",
            "--strategy", "SMA",
            "--fast-min", "10",
            "--fast-max", "11",
            "--slow-min", "30",
            "--slow-max", "31",
            "--years", "1",
            "--database"
        ],
        cwd="/Users/colemorton/Projects/trading",
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # Clean up
    await db_manager.close()
    
    return result.returncode == 0


if __name__ == "__main__":
    success = asyncio.run(test_cli_with_database())
    print(f"\n{'✅' if success else '❌'} Test {'passed' if success else 'failed'}")

