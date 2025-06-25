"""
Trade History Usage Examples

Comprehensive examples demonstrating how to use the generalized trade history system
for any ticker, strategy, and trading system configuration.

These examples show real-world usage patterns for:
- Setting up custom configurations
- Adding positions to any portfolio
- Bulk operations and migrations
- Portfolio analysis and comparison
- Cross-platform compatibility
"""

import logging
import sys
from pathlib import Path

# Add the trading system to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.tools.generalized_trade_history_exporter import (
    TradingSystemConfig,
    add_position_to_portfolio,
    add_qcom_position,
    bulk_add_positions_from_strategy_csv,
    create_position_record,
    get_config,
    set_config,
)
from app.tools.trade_history_utils import (
    bulk_update_trade_quality,
    compare_portfolios,
    export_portfolio_summary,
    get_portfolio_summary,
    list_portfolios,
    merge_portfolios,
    quick_add_position,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def example_1_basic_setup():
    """Example 1: Basic setup with default configuration."""
    print("\\n" + "=" * 60)
    print("EXAMPLE 1: Basic Setup with Default Configuration")
    print("=" * 60)

    # Use default configuration (current working directory)
    config = TradingSystemConfig()
    set_config(config)

    print(f"Base directory: {config.base_dir}")
    print(f"Price data directory: {config.price_data_dir}")
    print(f"Positions directory: {config.positions_dir}")

    # Add a simple position
    position_uuid = add_position_to_portfolio(
        ticker="AAPL",
        strategy_type="SMA",
        short_window=20,
        long_window=50,
        portfolio_name="example_portfolio",
    )

    print(f"Added position: {position_uuid}")


def example_2_custom_configuration():
    """Example 2: Custom configuration for different trading system."""
    print("\\n" + "=" * 60)
    print("EXAMPLE 2: Custom Configuration")
    print("=" * 60)

    # Custom configuration for a different base directory
    custom_config = TradingSystemConfig(base_dir="/tmp/custom_trading_system")
    set_config(custom_config)

    # Ensure directories exist
    custom_config.ensure_directories()

    print(f"Custom base directory: {custom_config.base_dir}")
    print(f"Custom price data: {custom_config.price_data_dir}")

    # Add positions with custom configuration
    positions = [
        ("MSFT", "EMA", 12, 26),
        ("GOOGL", "SMA", 15, 45),
        ("TSLA", "EMA", 8, 21),
    ]

    for ticker, strategy, short, long in positions:
        uuid = quick_add_position(ticker, strategy, short, long, "tech_portfolio")
        print(f"Added {ticker} {strategy} {short}/{long}: {uuid}")


def example_3_multiple_strategies():
    """Example 3: Adding multiple strategy types."""
    print("\\n" + "=" * 60)
    print("EXAMPLE 3: Multiple Strategy Types")
    print("=" * 60)

    # Different strategy configurations
    strategies = [
        {
            "ticker": "SPY",
            "strategy_type": "SMA",
            "short_window": 50,
            "long_window": 200,
            "portfolio_name": "index_portfolio",
        },
        {
            "ticker": "QQQ",
            "strategy_type": "EMA",
            "short_window": 20,
            "long_window": 50,
            "portfolio_name": "index_portfolio",
        },
        {
            "ticker": "IWM",
            "strategy_type": "SMA",
            "short_window": 10,
            "long_window": 30,
            "portfolio_name": "index_portfolio",
        },
    ]

    for strategy in strategies:
        try:
            uuid = add_position_to_portfolio(**strategy)
            print(f"✓ Added {strategy['ticker']} {strategy['strategy_type']}: {uuid}")
        except Exception as e:
            print(f"✗ Failed to add {strategy['ticker']}: {e}")


def example_4_closed_positions():
    """Example 4: Adding closed positions with P&L."""
    print("\\n" + "=" * 60)
    print("EXAMPLE 4: Closed Positions with P&L")
    print("=" * 60)

    # Add a closed position with exit data
    closed_position_uuid = add_position_to_portfolio(
        ticker="NFLX",
        strategy_type="SMA",
        short_window=20,
        long_window=50,
        entry_date="2025-01-01",
        entry_price=500.00,
        exit_date="2025-03-01",
        exit_price=550.00,
        position_size=100,
        portfolio_name="closed_trades",
    )

    print(f"Added closed position: {closed_position_uuid}")

    # Add another closed position (losing trade)
    losing_position_uuid = add_position_to_portfolio(
        ticker="META",
        strategy_type="EMA",
        short_window=12,
        long_window=26,
        entry_date="2025-01-15",
        entry_price=300.00,
        exit_date="2025-02-15",
        exit_price=280.00,
        position_size=50,
        portfolio_name="closed_trades",
    )

    print(f"Added losing position: {losing_position_uuid}")


def example_5_portfolio_analysis():
    """Example 5: Portfolio analysis and comparison."""
    print("\\n" + "=" * 60)
    print("EXAMPLE 5: Portfolio Analysis")
    print("=" * 60)

    # List all available portfolios
    portfolios = list_portfolios()
    print(f"Available portfolios: {portfolios}")

    # Analyze each portfolio
    for portfolio_name in portfolios:
        summary = get_portfolio_summary(portfolio_name)
        print(f"\\n{portfolio_name.upper()} PORTFOLIO SUMMARY:")
        print(f"  Total positions: {summary.get('total_positions', 0)}")
        print(f"  Open positions: {summary.get('open_positions', 0)}")
        print(f"  Closed positions: {summary.get('closed_positions', 0)}")

        # Strategy breakdown
        strategies = summary.get("strategy_breakdown", {})
        if strategies:
            print(f"  Strategies: {strategies}")

        # Performance metrics
        performance = summary.get("performance_metrics", {})
        if performance:
            print(
                f"  Win rate: {performance.get('win_rate', 'N/A'):.2%}"
                if performance.get("win_rate")
                else "  Win rate: N/A"
            )
            print(
                f"  Avg return: {performance.get('avg_return', 'N/A'):.2%}"
                if performance.get("avg_return")
                else "  Avg return: N/A"
            )


def example_6_bulk_operations():
    """Example 6: Bulk operations and data management."""
    print("\\n" + "=" * 60)
    print("EXAMPLE 6: Bulk Operations")
    print("=" * 60)

    # Bulk add multiple positions
    bulk_positions = [
        ("AMZN", "SMA", 30, 60),
        ("NVDA", "EMA", 15, 30),
        ("AMD", "SMA", 25, 50),
        ("INTC", "EMA", 10, 20),
    ]

    print("Adding bulk positions to semiconductor portfolio...")
    for ticker, strategy, short, long in bulk_positions:
        uuid = quick_add_position(
            ticker, strategy, short, long, "semiconductor_portfolio"
        )
        print(f"  {ticker}: {uuid}")

    # Update trade quality for all positions
    print("\\nUpdating trade quality assessments...")
    for portfolio in list_portfolios():
        updated = bulk_update_trade_quality(portfolio)
        if updated > 0:
            print(f"  Updated {updated} positions in {portfolio}")


def example_7_real_world_qcom():
    """Example 7: Real-world QCOM example."""
    print("\\n" + "=" * 60)
    print("EXAMPLE 7: Real-World QCOM Example")
    print("=" * 60)

    # Add the QCOM position as requested
    qcom_uuid = add_qcom_position(
        entry_date="2025-06-24", portfolio_name="live_signals"
    )
    print(f"Added QCOM SMA 49/66 position: {qcom_uuid}")

    # Get portfolio summary
    summary = get_portfolio_summary("live_signals")
    print(f"\\nLive Signals Portfolio Summary:")
    print(f"  Total positions: {summary.get('total_positions', 0)}")
    print(f"  Strategy breakdown: {summary.get('strategy_breakdown', {})}")


def example_8_cross_platform_compatibility():
    """Example 8: Cross-platform file path handling."""
    print("\\n" + "=" * 60)
    print("EXAMPLE 8: Cross-Platform Compatibility")
    print("=" * 60)

    # Test with different path formats
    test_configs = [
        "/tmp/trading_linux",  # Linux/Mac absolute path
        "C:\\\\Trading\\\\Windows",  # Windows absolute path
        "relative/trading/path",  # Relative path
    ]

    for test_path in test_configs:
        try:
            config = TradingSystemConfig(base_dir=test_path)
            print(f"✓ {test_path} -> {config.base_dir}")
            print(f"  Price data: {config.price_data_dir}")
        except Exception as e:
            print(f"✗ {test_path} failed: {e}")


def example_9_error_handling():
    """Example 9: Error handling and validation."""
    print("\\n" + "=" * 60)
    print("EXAMPLE 9: Error Handling and Validation")
    print("=" * 60)

    # Test invalid inputs
    invalid_cases = [
        {
            "ticker": "",  # Empty ticker
            "strategy_type": "SMA",
            "short_window": 20,
            "long_window": 50,
            "description": "Empty ticker",
        },
        {
            "ticker": "AAPL",
            "strategy_type": "INVALID",  # Invalid strategy
            "short_window": 20,
            "long_window": 50,
            "description": "Invalid strategy type",
        },
        {
            "ticker": "AAPL",
            "strategy_type": "SMA",
            "short_window": -10,  # Invalid window
            "long_window": 50,
            "description": "Negative short window",
        },
    ]

    for case in invalid_cases:
        try:
            description = case.pop("description")
            uuid = add_position_to_portfolio(portfolio_name="test_errors", **case)
            print(f"✗ {description}: Unexpectedly succeeded - {uuid}")
        except Exception as e:
            print(f"✓ {description}: Correctly failed - {e}")


def example_10_advanced_features():
    """Example 10: Advanced features and customization."""
    print("\\n" + "=" * 60)
    print("EXAMPLE 10: Advanced Features")
    print("=" * 60)

    # Create positions with custom parameters
    advanced_position = create_position_record(
        ticker="BTC-USD",
        strategy_type="EMA",
        short_window=12,
        long_window=26,
        signal_window=9,
        entry_date="2025-06-01",
        entry_price=65000.00,
        position_size=0.1,
        direction="Long",
    )

    print("Created advanced position record:")
    for key, value in advanced_position.items():
        if value is not None:
            print(f"  {key}: {value}")


def run_all_examples():
    """Run all examples in sequence."""
    print("TRADE HISTORY SYSTEM - USAGE EXAMPLES")
    print("=" * 60)
    print("Demonstrating generalized trade history system capabilities...")

    examples = [
        example_1_basic_setup,
        example_2_custom_configuration,
        example_3_multiple_strategies,
        example_4_closed_positions,
        example_5_portfolio_analysis,
        example_6_bulk_operations,
        example_7_real_world_qcom,
        example_8_cross_platform_compatibility,
        example_9_error_handling,
        example_10_advanced_features,
    ]

    for i, example_func in enumerate(examples, 1):
        try:
            example_func()
        except Exception as e:
            print(f"\\n✗ Example {i} failed: {e}")
            logger.exception(f"Example {i} error details:")

        # Add separator between examples
        if i < len(examples):
            print("\\n" + "-" * 60)

    print("\\n" + "=" * 60)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 60)


def main():
    """Main CLI entry point for trade history usage examples."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Trade History Usage Examples - Educational demonstrations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all examples
  python %(prog)s

  # Run specific example
  python %(prog)s --example 7

  # Test with custom configuration
  python %(prog)s --test-config /path/to/trading/system

  # Run in test mode (safe)
  python %(prog)s --test-mode
        """,
    )

    parser.add_argument(
        "--example", type=int, choices=range(1, 11), help="Run specific example (1-10)"
    )
    parser.add_argument(
        "--test-config", type=str, help="Test with custom configuration directory"
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode (uses /tmp directory)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

    # Set up configuration
    if args.test_config:
        test_config = TradingSystemConfig(base_dir=args.test_config)
    elif args.test_mode or not args.example:
        # Default to test mode to avoid interfering with real data
        test_config = TradingSystemConfig(base_dir="/tmp/trade_history_examples")
    else:
        # Use current directory for specific examples
        test_config = TradingSystemConfig()

    set_config(test_config)
    test_config.ensure_directories()

    print(f"Using configuration: {test_config.base_dir}")

    try:
        if args.example:
            # Run specific example
            examples = [
                example_1_basic_setup,
                example_2_custom_configuration,
                example_3_multiple_strategies,
                example_4_closed_positions,
                example_5_portfolio_analysis,
                example_6_bulk_operations,
                example_7_real_world_qcom,
                example_8_cross_platform_compatibility,
                example_9_error_handling,
                example_10_advanced_features,
            ]

            if 1 <= args.example <= len(examples):
                print(f"Running Example {args.example}...")
                examples[args.example - 1]()
                print(f"Example {args.example} completed successfully!")
            else:
                print(f"Invalid example number: {args.example}")
                return 1
        else:
            # Run all examples
            run_all_examples()

        return 0

    except Exception as e:
        print(f"Error running examples: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
