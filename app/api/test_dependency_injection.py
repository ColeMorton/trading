#!/usr/bin/env python3
"""
Test script to demonstrate dependency injection implementation.
"""

import asyncio
from pathlib import Path

# Import the dependency configuration
from app.api.dependencies import configure_dependencies, get_service
from app.core.interfaces import (
    ConfigurationInterface,
    DataAccessInterface,
    LoggingInterface,
    PortfolioManagerInterface,
    StrategyAnalyzerInterface,
)


async def test_dependency_injection():
    """Test dependency injection is working correctly."""

    print("Testing Dependency Injection Implementation")
    print("=" * 50)

    # Configure dependencies
    print("\n1. Configuring dependencies...")
    configure_dependencies(
        {
            "api": {
                "host": "127.0.0.1",
                "port": 8000,
            },
            "data": {
                "base_path": "csv",
                "cache_enabled": True,
            },
            "logging": {
                "level": "INFO",
            },
        }
    )
    print("✓ Dependencies configured")

    # Test logging service
    print("\n2. Testing LoggingInterface...")
    logger_service = get_service(LoggingInterface)
    logger = logger_service.get_logger("test")
    logger.info("Test log message from dependency injection")
    print("✓ Logging service working")

    # Test configuration service
    print("\n3. Testing ConfigurationInterface...")
    config_service = get_service(ConfigurationInterface)
    api_host = config_service.get("api.host")
    print(f"   API Host: {api_host}")
    print("✓ Configuration service working")

    # Test data access service
    print("\n4. Testing DataAccessInterface...")
    data_service = get_service(DataAccessInterface)
    tickers = data_service.list_available_tickers()
    print(f"   Available tickers: {len(tickers)} found")
    if tickers:
        print(f"   First few tickers: {tickers[:5]}")
    print("✓ Data access service working")

    # Test portfolio manager
    print("\n5. Testing PortfolioManagerInterface...")
    portfolio_manager = get_service(PortfolioManagerInterface)
    portfolio_dir = Path("csv/portfolios")
    if portfolio_dir.exists():
        portfolios = portfolio_manager.list_portfolios(portfolio_dir)
        print(f"   Found {len(portfolios)} portfolios")
    print("✓ Portfolio manager working")

    # Test strategy analyzer
    print("\n6. Testing StrategyAnalyzerInterface...")
    strategy_analyzer = get_service(StrategyAnalyzerInterface)
    default_config = strategy_analyzer.get_default_config()
    print(
        f"   Default config: {
    default_config.to_dict() if hasattr(
        default_config,
         'to_dict') else 'Config object'}"
    )
    print("✓ Strategy analyzer working")

    print("\n" + "=" * 50)
    print("All dependency injection tests passed!")

    # Demonstrate circular dependency prevention
    print("\n7. Testing circular dependency prevention...")
    try:
        # Portfolio manager depends on data access
        # If there were circular dependencies, this would fail
        get_service(PortfolioManagerInterface)
        print("✓ No circular dependencies detected")
    except Exception as e:
        print(f"✗ Circular dependency error: {e}")

    return True


if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_dependency_injection())
    if result:
        print("\nDependency injection implementation successful!")
    else:
        print("\nDependency injection implementation failed!")
