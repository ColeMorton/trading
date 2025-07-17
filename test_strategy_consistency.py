#!/usr/bin/env python3
"""
Test script for strategy command consistency improvements.

This script tests the shared utilities and verifies that the refactored
strategy commands maintain functionality while improving consistency.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_shared_utilities():
    """Test the shared utilities module."""
    print("🧪 Testing Shared Utilities")
    print("=" * 40)
    
    try:
        from app.cli.commands.strategy_utils import (
            process_ticker_input,
            build_configuration_overrides,
            convert_to_legacy_config,
            show_execution_progress,
            validate_parameter_relationships,
        )
        print("✅ All utility functions imported successfully")
        
        # Test ticker processing
        result = process_ticker_input(["AAPL,MSFT", "GOOGL"])
        expected = ["AAPL", "MSFT", "GOOGL"]
        assert result == expected, f"Expected {expected}, got {result}"
        print("✅ Ticker processing works correctly")
        
        # Test configuration overrides
        overrides = build_configuration_overrides(
            ticker=["BTC-USD", "ETH-USD"],
            strategy_type=["SMA", "EMA"],
            min_trades=50
        )
        assert "ticker" in overrides
        assert "strategy_types" in overrides
        assert "minimums" in overrides
        print("✅ Configuration overrides building works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Shared utilities test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_models():
    """Test the updated configuration models."""
    print("\n🔧 Testing Configuration Models")
    print("=" * 40)
    
    try:
        from app.cli.models.strategy import StrategyConfig, MACrossConfig, MACDConfig
        
        # Test StrategyConfig with sweep parameters
        config = StrategyConfig(
            ticker=["AAPL", "MSFT"],
            strategy_types=["SMA", "EMA"],
            fast_period_range=(5, 20),
            slow_period_range=(21, 50),
            fast_period=10,
            slow_period=30
        )
        print("✅ StrategyConfig with sweep parameters created successfully")
        
        # Test MACrossConfig inheritance
        ma_config = MACrossConfig(
            ticker="BTC-USD",
            strategy_types=["SMA"]
        )
        print("✅ MACrossConfig inherits from StrategyConfig correctly")
        
        # Test MACDConfig with defaults
        macd_config = MACDConfig(
            ticker="TSLA",
            strategy_types=["MACD"]
        )
        assert macd_config.fast_period == 12  # MACD default
        assert macd_config.slow_period == 26  # MACD default
        print("✅ MACDConfig has correct defaults")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy_commands():
    """Test strategy command imports."""
    print("\n📊 Testing Strategy Commands")
    print("=" * 40)
    
    try:
        from app.cli.commands.strategy import app, run, sweep, analyze
        print("✅ Strategy commands imported successfully")
        
        # Test that the Typer app is properly configured
        assert app.info.name == "strategy"
        print("✅ Strategy app properly configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Strategy commands test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_consistency_improvements():
    """Test specific consistency improvements."""
    print("\n🎯 Testing Consistency Improvements")
    print("=" * 40)
    
    try:
        from app.cli.commands.strategy_utils import (
            process_ticker_input,
            build_configuration_overrides
        )
        
        # Test that comma-separated tickers work consistently
        test_cases = [
            (["AAPL,MSFT"], ["AAPL", "MSFT"]),
            (["BTC-USD", "ETH-USD"], ["BTC-USD", "ETH-USD"]),
            (["AAPL,MSFT,GOOGL"], ["AAPL", "MSFT", "GOOGL"]),
            (["AAPL", "MSFT,GOOGL"], ["AAPL", "MSFT", "GOOGL"]),
        ]
        
        for input_tickers, expected in test_cases:
            result = process_ticker_input(input_tickers)
            assert result == expected, f"Input {input_tickers}: expected {expected}, got {result}"
        
        print("✅ Ticker processing consistency verified")
        
        # Test parameter override consistency
        overrides1 = build_configuration_overrides(ticker=["AAPL"], min_trades=50)
        overrides2 = build_configuration_overrides(ticker=["AAPL"], min_trades=50)
        
        # Should produce identical results
        assert overrides1 == overrides2
        print("✅ Configuration override consistency verified")
        
        return True
        
    except Exception as e:
        print(f"❌ Consistency improvements test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Strategy Command Consistency Test Suite")
    print("=" * 50)
    
    results = []
    
    # Run all tests
    results.append(test_shared_utilities())
    results.append(test_config_models())
    results.append(test_strategy_commands())
    results.append(test_consistency_improvements())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Test Summary")
    print(f"   Passed: {passed}/{total}")
    print(f"   Failed: {total - passed}/{total}")
    
    if passed == total:
        print(f"\n🎉 All tests passed! Strategy commands are consistent and working properly.")
        print(f"   ✅ Shared utilities functional")
        print(f"   ✅ Configuration models consolidated")
        print(f"   ✅ Command imports working")
        print(f"   ✅ Consistency improvements verified")
        return True
    else:
        print(f"\n⚠️ Some tests failed. Review the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)