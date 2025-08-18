#!/usr/bin/env python3
"""
Demo Script: Unified Strategy Framework

This script demonstrates the unified strategy framework capabilities
and shows how to use the new infrastructure.
"""

import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.tools.strategy.factory import StrategyFactory
from app.tools.strategy.migration_helper import validate_unified_parameters
from app.tools.strategy.strategy_adapter import StrategyAdapter


def demo_strategy_factory():
    """Demonstrate StrategyFactory capabilities."""
    print("=== Strategy Factory Demo ===")

    factory = StrategyFactory()

    # Show available strategies
    print(f"Available strategies: {factory.get_available_strategies()}")
    print()

    # Create unified strategies
    print("Creating unified strategies:")

    sma_strategy = factory.create_strategy("UNIFIED_SMA")
    print(
        f"✓ SMA Strategy: {sma_strategy.__class__.__name__} (type: {sma_strategy.get_strategy_type()})"
    )

    ema_strategy = factory.create_strategy("UNIFIED_EMA")
    print(
        f"✓ EMA Strategy: {ema_strategy.__class__.__name__} (type: {ema_strategy.get_strategy_type()})"
    )

    macd_strategy = factory.create_strategy("UNIFIED_MACD")
    print(
        f"✓ MACD Strategy: {macd_strategy.__class__.__name__} (type: {macd_strategy.get_strategy_type()})"
    )

    # Test aliases
    print("\nTesting aliases:")
    alias_sma = factory.create_strategy("MA_CROSS_SMA")
    print(f"✓ MA_CROSS_SMA alias: {alias_sma.__class__.__name__}")

    # Test backward compatibility
    print("\nTesting backward compatibility:")
    legacy_sma = factory.create_strategy("SMA")
    print(f"✓ Legacy SMA: {legacy_sma.__class__.__name__}")
    print()


def demo_parameter_validation():
    """Demonstrate parameter validation capabilities."""
    print("=== Parameter Validation Demo ===")

    adapter = StrategyAdapter()

    # Valid SMA configuration
    sma_config = {"FAST_PERIOD": 10, "SLOW_PERIOD": 50, "DIRECTION": "Long"}

    print("Validating SMA configuration:")
    print(f"Config: {sma_config}")
    is_valid = adapter.validate_strategy_parameters("SMA", sma_config)
    print(f"Valid: {is_valid}")

    # Get parameter ranges
    ranges = adapter.get_strategy_parameter_ranges("SMA")
    print(f"Parameter ranges: {ranges}")
    print()

    # Invalid configuration (windows reversed)
    invalid_config = {"FAST_PERIOD": 50, "SLOW_PERIOD": 10, "DIRECTION": "Long"}

    print("Validating invalid configuration:")
    print(f"Config: {invalid_config}")
    validation_result = validate_unified_parameters("SMA", invalid_config)
    print(f"Valid: {validation_result['is_valid']}")
    print(f"Errors: {validation_result['errors']}")
    print(f"Suggestions: {validation_result['suggestions']}")
    print()


def demo_strategy_interfaces():
    """Demonstrate strategy interface compliance."""
    print("=== Strategy Interface Demo ===")

    factory = StrategyFactory()

    strategies_to_test = ["UNIFIED_SMA", "UNIFIED_EMA", "UNIFIED_MACD"]

    for strategy_type in strategies_to_test:
        print(f"\nTesting {strategy_type}:")
        strategy = factory.create_strategy(strategy_type)

        # Test interface compliance
        from app.core.interfaces.strategy import StrategyInterface
        from app.tools.strategy.base import BaseStrategy

        print(f"  ✓ Extends BaseStrategy: {isinstance(strategy, BaseStrategy)}")
        print(
            f"  ✓ Implements StrategyInterface: {isinstance(strategy, StrategyInterface)}"
        )

        # Test parameter ranges
        ranges = strategy.get_parameter_ranges()
        print(f"  ✓ Parameter ranges available: {len(ranges)} parameters")

        # Test parameter validation
        test_config = {"FAST_PERIOD": 10, "SLOW_PERIOD": 50}

        if strategy_type == "UNIFIED_MACD":
            test_config["SIGNAL_PERIOD"] = 9

        is_valid = strategy.validate_parameters(test_config)
        print(f"  ✓ Parameter validation works: {is_valid}")


def demo_migration_capabilities():
    """Demonstrate migration helper capabilities."""
    print("=== Migration Helper Demo ===")

    # Test parameter validation with detailed feedback
    print("Testing MACD configuration validation:")

    macd_config = {
        "FAST_PERIOD": 12,
        "SLOW_PERIOD": 26,
        "SIGNAL_PERIOD": 9,
        "DIRECTION": "Long",
    }

    validation_result = validate_unified_parameters("MACD", macd_config)
    print(f"Configuration: {macd_config}")
    print(f"Valid: {validation_result['is_valid']}")
    print(
        f"Parameter ranges available: {len(validation_result['parameter_ranges'])} parameters"
    )

    # Test incomplete configuration
    print("\nTesting incomplete MACD configuration:")
    incomplete_config = {
        "FAST_PERIOD": 12,
        "SLOW_PERIOD": 26
        # Missing SIGNAL_PERIOD
    }

    validation_result = validate_unified_parameters("MACD", incomplete_config)
    print(f"Configuration: {incomplete_config}")
    print(f"Valid: {validation_result['is_valid']}")
    print(f"Errors: {validation_result['errors']}")
    print(f"Suggestions: {validation_result['suggestions']}")
    print()


def main():
    """Run all demos."""
    print("Unified Strategy Framework Demo")
    print("=" * 50)
    print()

    try:
        demo_strategy_factory()
        demo_parameter_validation()
        demo_strategy_interfaces()
        demo_migration_capabilities()

        print("=" * 50)
        print("✅ All demos completed successfully!")
        print()
        print("Key Features Demonstrated:")
        print("- Strategy Factory with unified and legacy support")
        print("- Comprehensive parameter validation")
        print("- Interface compliance across all strategies")
        print("- Migration utilities for gradual transition")
        print("- Backward compatibility maintenance")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
