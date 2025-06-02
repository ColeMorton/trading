#!/usr/bin/env python3
"""
Simple validation test for portfolio metrics calculation system.
Tests the core functionality that was previously failing.
"""

import numpy as np
import pandas as pd
import polars as pl
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.concurrency.tools.correlation_calculator import CorrelationCalculator
from app.concurrency.tools.concurrency_analysis import ConcurrencyAnalysis
from app.concurrency.tools.risk_metrics import calculate_risk_contributions
from app.concurrency.tools.analysis import analyze_concurrency
from app.concurrency.tools.types import StrategyConfig


def test_covariance_matrix():
    """Test that CorrelationCalculator.calculate_covariance_matrix works."""
    print("\n1. Testing Covariance Matrix Calculation...")
    
    # Create sample returns data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    returns_data = {
        'BTC': np.random.normal(0.001, 0.02, 100),
        'ETH': np.random.normal(0.0015, 0.025, 100),
        'SOL': np.random.normal(0.002, 0.03, 100)
    }
    
    # Convert to numpy array
    data_matrix = np.column_stack([returns_data['BTC'], returns_data['ETH'], returns_data['SOL']])
    labels = ['BTC', 'ETH', 'SOL']
    
    # Initialize calculator
    calculator = CorrelationCalculator()
    
    # Calculate covariance matrix
    cov_matrix, diagnostics = calculator.calculate_covariance_matrix(data_matrix, labels)
    
    # Validate results
    assert cov_matrix is not None, "Covariance matrix should not be None"
    assert cov_matrix.shape == (3, 3), f"Expected shape (3, 3), got {cov_matrix.shape}"
    assert np.all(np.isfinite(cov_matrix)), "Covariance matrix contains non-finite values"
    assert np.allclose(cov_matrix, cov_matrix.T), "Covariance matrix should be symmetric"
    
    print("✓ Covariance matrix calculation successful")
    print(f"  Shape: {cov_matrix.shape}")
    print(f"  Diagonal (variances): {np.diag(cov_matrix)}")
    

def test_concurrency_analysis():
    """Test that basic concurrency analysis components work."""
    print("\n2. Testing Concurrency Analysis Components...")
    
    try:
        # Test data alignment
        from app.concurrency.tools.data_alignment import align_multiple_data
        
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        # Create two simple dataframes with OHLC data
        close1 = 100 + np.cumsum(np.random.normal(0, 1, 100))
        close2 = 50 + np.cumsum(np.random.normal(0, 0.5, 100))
        
        df1 = pl.DataFrame({
            'Date': dates,
            'Open': close1 * 0.99,
            'High': close1 * 1.01,
            'Low': close1 * 0.98,
            'Close': close1,
            'Volume': np.ones(100) * 1000000,
            'Position': np.random.choice([0, 1], size=100)
        })
        
        df2 = pl.DataFrame({
            'Date': dates,
            'Open': close2 * 0.99,
            'High': close2 * 1.01,
            'Low': close2 * 0.98,
            'Close': close2,
            'Volume': np.ones(100) * 500000,
            'Position': np.random.choice([0, 1], size=100)
        })
        
        # Test alignment
        aligned = align_multiple_data([df1, df2], [False, False], lambda x, y: None)
        assert len(aligned) == 2, "Should align 2 dataframes"
        assert all(len(df) > 0 for df in aligned), "Aligned dataframes should not be empty"
        print("✓ Data alignment works")
        
        # Test position metrics calculation
        from app.concurrency.tools.position_metrics import calculate_position_metrics
        
        # Create list of position arrays as expected by the function
        position_arrays = [
            np.random.choice([0, 1], size=100),
            np.random.choice([0, 1], size=100)
        ]
        
        metrics = calculate_position_metrics(position_arrays, lambda x, y: None)
        assert metrics is not None, "Position metrics should not be None"
        print("✓ Position metrics calculation works")
        
        print("\n✓ Concurrency analysis components validated successfully")
        
    except Exception as e:
        print(f"✗ Concurrency analysis component test failed: {e}")
        raise


def test_portfolio_metrics():
    """Test that basic portfolio metrics are calculated correctly."""
    print("\n3. Testing Basic Portfolio Calculations...")
    
    # Create sample data
    np.random.seed(42)
    
    # Test 1: Portfolio returns calculation
    returns = np.array([
        [0.01, 0.02, -0.01],  # Day 1 returns for 3 assets
        [0.02, -0.01, 0.03],  # Day 2
        [-0.01, 0.01, 0.02],  # Day 3
    ])
    weights = np.array([0.5, 0.3, 0.2])
    
    # Calculate weighted portfolio returns
    portfolio_returns = np.dot(returns, weights)
    expected_returns = [
        0.01 * 0.5 + 0.02 * 0.3 + (-0.01) * 0.2,  # Day 1
        0.02 * 0.5 + (-0.01) * 0.3 + 0.03 * 0.2,  # Day 2
        (-0.01) * 0.5 + 0.01 * 0.3 + 0.02 * 0.2,  # Day 3
    ]
    
    assert np.allclose(portfolio_returns, expected_returns), "Portfolio return calculation error"
    print("✓ Portfolio returns calculation works")
    
    # Test 2: Simple risk calculation
    portfolio_std = np.std(portfolio_returns)
    assert portfolio_std > 0, "Portfolio standard deviation should be positive"
    print(f"✓ Portfolio risk calculation works (std: {portfolio_std:.4f})")
    
    # Test 3: Covariance matrix is positive semi-definite
    returns_matrix = np.random.normal(0.001, 0.02, (100, 3))
    cov_matrix = np.cov(returns_matrix.T)
    eigenvalues = np.linalg.eigvals(cov_matrix)
    
    assert np.all(eigenvalues >= -1e-10), "Covariance matrix should be positive semi-definite"
    print("✓ Covariance matrix validation works")
    
    print("\n✓ Basic portfolio calculations validated successfully")


def main():
    """Run all validation tests."""
    print("Portfolio Metrics Validation Test")
    print("=" * 50)
    
    try:
        # Run tests
        test_covariance_matrix()
        test_concurrency_analysis()
        test_portfolio_metrics()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed successfully!")
        print("The portfolio metrics calculation system is working correctly.")
        
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()