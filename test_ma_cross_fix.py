"""Test MA Cross analysis after fixing the column name issue."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ma_cross.core.analyzer import MAStrategyAnalyzer

def test_ma_cross_analysis():
    """Test MA Cross analysis with NVDA."""
    
    # Test configuration
    params = {
        'ticker': 'NVDA',
        'windows': 89,
        'direction': 'Long',
        'strategy_types': ['SMA', 'EMA'],
        'use_hourly': False,
        'use_years': False,
        'years': 15.0,
        'use_synthetic': False,
        'ticker_1': None,
        'ticker_2': None,
        'refresh': False,  # Use existing data
        'minimums': {
            'trades': 54,
            'win_rate': 0.44,
            'expectancy_per_trade': 1.0,
            'profit_factor': 1.0,
            'score': None,
            'sortino_ratio': 0.4,
            'beats_bnh': None
        },
        'sort_by': 'Score',
        'sort_asc': False,
        'use_gbm': False,
        'use_current': True,
        'use_scanner': False,
        'async_execution': False
    }
    
    print("Testing MA Cross analysis with configuration:")
    print(f"Ticker: {params['ticker']}")
    print(f"Strategy Types: {params['strategy_types']}")
    print(f"Use Current: {params['use_current']}")
    print(f"Refresh: {params['refresh']}")
    print()
    
    # Create analyzer and run analysis
    analyzer = MAStrategyAnalyzer()
    
    try:
        print("Running MA Cross analysis...")
        result = analyzer.analyze_portfolio_sync(params)
        
        print(f"\nAnalysis completed successfully!")
        print(f"Total portfolios analyzed: {result['total_portfolios']}")
        print(f"SMA portfolios: {result.get('sma_portfolios', 0)}")
        print(f"EMA portfolios: {result.get('ema_portfolios', 0)}")
        print(f"Found portfolio files: {len(result['portfolio_files'])}")
        print(f"Found filtered files: {len(result['filtered_files'])}")
        
        if result['portfolio_files']:
            print("\nPortfolio files:")
            for file in result['portfolio_files']:
                print(f"  - {file}")
                
        if result['filtered_files']:
            print("\nFiltered portfolio files:")
            for file in result['filtered_files']:
                print(f"  - {file}")
        
        # Check if current signals were found
        if result.get('current_signals'):
            print(f"\nCurrent signals found: {result['current_signals']}")
        else:
            print("\nNo current signals found")
            
        return True
        
    except Exception as e:
        print(f"\nError during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== MA Cross Analysis Test ===\n")
    success = test_ma_cross_analysis()
    print(f"\n{'✅ Test passed' if success else '❌ Test failed'}")