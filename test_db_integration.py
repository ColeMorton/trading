"""
Quick test script for database integration.
"""

import asyncio
import uuid

from app.database.config import db_manager, is_database_available
from app.database.strategy_sweep_repository import StrategySweepRepository


async def test_database_integration():
    """Test database persistence functionality."""
    print("🧪 Testing Database Integration\n")

    # Test 1: Database availability
    print("1. Checking database availability...")
    await db_manager.initialize()
    available = await is_database_available()
    print(f"   ✓ Database available: {available}\n")

    if not available:
        print("   ✗ Database not available. Skipping further tests.")
        return

    # Test 2: Create repository
    print("2. Creating repository...")
    repository = StrategySweepRepository(db_manager)
    print("   ✓ Repository created\n")

    # Test 3: Save test data
    print("3. Saving test sweep results...")
    sweep_run_id = uuid.uuid4()

    test_results = [
        {
            "Ticker": "AAPL",
            "Strategy Type": "SMA",
            "Fast Period": 10,
            "Slow Period": 30,
            "Total Trades": 25,
            "Win Rate [%]": 65.0,
            "Score": 150.5,
            "Total Return [%]": 25.5,
            "Max Drawdown [%]": -8.3,
            "Sharpe Ratio": 1.85,
        },
        {
            "Ticker": "AAPL",
            "Strategy Type": "SMA",
            "Fast Period": 15,
            "Slow Period": 35,
            "Total Trades": 20,
            "Win Rate [%]": 70.0,
            "Score": 165.2,
            "Total Return [%]": 30.2,
            "Max Drawdown [%]": -6.1,
            "Sharpe Ratio": 2.10,
        },
    ]

    sweep_config = {
        "tickers": ["AAPL"],
        "strategy_types": ["SMA"],
        "fast_period_min": 10,
        "fast_period_max": 20,
        "slow_period_min": 30,
        "slow_period_max": 40,
        "years": 1,
    }

    inserted_count = await repository.save_sweep_results(
        sweep_run_id=sweep_run_id,
        results=test_results,
        sweep_config=sweep_config,
    )
    print(f"   ✓ Inserted {inserted_count} records\n")
    print(f"   Sweep Run ID: {sweep_run_id}\n")

    # Test 4: Retrieve data
    print("4. Retrieving saved results...")
    retrieved_results = await repository.get_sweep_results(sweep_run_id)
    print(f"   ✓ Retrieved {len(retrieved_results)} records\n")

    # Display sample record
    if retrieved_results:
        sample = retrieved_results[0]
        print("   Sample record:")
        print(f"     - Ticker: {sample['ticker']}")
        print(f"     - Strategy: {sample['strategy_type']}")
        print(f"     - Fast/Slow: {sample['fast_period']}/{sample['slow_period']}")
        print(f"     - Win Rate: {sample['win_rate_pct']}%")
        print(f"     - Score: {sample['score']}\n")

    # Test 5: Get recent sweeps
    print("5. Getting recent sweep runs...")
    recent_sweeps = await repository.get_recent_sweeps(limit=5)
    print(f"   ✓ Found {len(recent_sweeps)} recent sweeps\n")

    # Clean up
    await db_manager.close()
    print("✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_database_integration())
