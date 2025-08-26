#!/usr/bin/env python3
"""
Basic ATR Test Runner
Simple test to validate ATR strategy components
"""

import sys
import os
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd

# Test basic ATR components
def test_atr_imports():
    """Test that ATR modules can be imported."""
    print("Testing ATR imports...")
    
    try:
        from app.strategies.atr.tools.strategy_execution import calculate_atr, generate_signals, analyze_params
        print("✓ Successfully imported strategy_execution functions")
        
        from app.strategies.atr.tools.signal_utils import is_signal_current, is_exit_signal_current
        print("✓ Successfully imported signal_utils functions")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_atr_calculation():
    """Test basic ATR calculation."""
    print("\nTesting ATR calculation...")
    
    try:
        from app.strategies.atr.tools.strategy_execution import calculate_atr
        
        # Create simple test data
        dates = pd.date_range('2020-01-01', periods=50, freq='D')
        prices = [100 + i + np.random.normal(0, 2) for i in range(50)]
        
        data = pd.DataFrame({
            'Date': dates,
            'Open': prices,
            'High': [p + abs(np.random.normal(0, 1)) for p in prices],
            'Low': [p - abs(np.random.normal(0, 1)) for p in prices],
            'Close': prices,
            'Volume': [100000] * 50
        }).set_index('Date')
        
        # Calculate ATR
        atr_series = calculate_atr(data, 14)
        
        # Verify results
        assert len(atr_series) == len(data)
        assert (atr_series.dropna() > 0).all()
        
        print("✓ ATR calculation working correctly")
        return True
        
    except Exception as e:
        print(f"✗ ATR calculation error: {e}")
        return False

def test_signal_generation():
    """Test basic signal generation."""
    print("Testing signal generation...")
    
    try:
        from app.strategies.atr.tools.strategy_execution import generate_signals
        
        # Create test data
        dates = pd.date_range('2020-01-01', periods=50, freq='D')
        prices = [100 + i*0.5 + np.random.normal(0, 1) for i in range(50)]  # Trending up
        
        data = pd.DataFrame({
            'Date': dates,
            'Open': prices,
            'High': [p + abs(np.random.normal(0, 0.5)) for p in prices],
            'Low': [p - abs(np.random.normal(0, 0.5)) for p in prices],
            'Close': prices,
            'Volume': [100000] * 50
        }).set_index('Date')
        
        # Generate signals (test default Long direction)
        signals_df = generate_signals(data, 10, 2.0)
        
        # Verify results
        assert 'Signal' in signals_df.columns
        assert 'ATR_Trailing_Stop' in signals_df.columns
        assert 'ATR' in signals_df.columns
        assert 'Position' in signals_df.columns
        
        # Check signal values are valid (0=exit, 1=long entry/hold, -1=short entry/hold)
        signals = signals_df['Signal'].dropna().unique()
        assert all(s in [-1, 0, 1] for s in signals)
        
        print("✓ Signal generation working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Signal generation error: {e}")
        return False

def test_analyze_params():
    """Test parameter analysis function."""
    print("Testing parameter analysis...")
    
    try:
        from app.strategies.atr.tools.strategy_execution import analyze_params
        
        # Create test data
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        base_price = 100
        returns = np.random.normal(0.001, 0.02, 100)
        prices = base_price * np.exp(np.cumsum(returns))
        
        data = pd.DataFrame({
            'Date': dates,
            'Open': prices,
            'High': prices * 1.01,
            'Low': prices * 0.99,
            'Close': prices,
            'Volume': [100000] * 100
        }).set_index('Date')
        
        # Mock logger
        def mock_log(msg, level="info"):
            pass
        
        # Analyze parameters (test with config)
        config = {"DIRECTION": "Long"}
        result = analyze_params(data, 14, 2.0, 'TEST', mock_log, config)
        
        # Verify results
        assert isinstance(result, dict)
        assert result['Ticker'] == 'TEST'
        assert result['Strategy Type'] == 'ATR'
        assert result['Fast Period'] == 14
        assert result['Slow Period'] == 20  # 2.0 * 10
        
        print("✓ Parameter analysis working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Parameter analysis error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run basic ATR tests."""
    print("=" * 60)
    print("Basic ATR Strategy Tests")
    print("=" * 60)
    
    tests = [
        test_atr_imports,
        test_atr_calculation,
        test_signal_generation,
        test_analyze_params
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print(f"Passed: {sum(results)}/{len(results)}")
    print(f"Success Rate: {sum(results)/len(results)*100:.1f}%")
    
    if all(results):
        print("\n🎉 All basic tests passed!")
        return True
    else:
        print("\n❌ Some tests failed")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)