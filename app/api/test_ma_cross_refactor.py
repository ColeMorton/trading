"""
Test script for MA Cross refactoring.

This script tests the refactored MA Cross module to ensure it works
correctly with the API service.
"""

import asyncio
import json
from datetime import datetime

from app.api.services.ma_cross_service import MACrossService
from app.api.models.ma_cross import MACrossRequest
from app.ma_cross.core import MACrossAnalyzer, AnalysisConfig


def test_core_analyzer():
    """Test the core MA Cross analyzer directly."""
    print("\n=== Testing Core Analyzer ===")
    
    # Create analyzer
    analyzer = MACrossAnalyzer()
    
    try:
        # Test single ticker analysis
        config = AnalysisConfig(
            ticker="AAPL",
            use_sma=False,
            use_hourly=False,
            direction="Long",
            short_window=10,
            long_window=30
        )
        
        print(f"Analyzing {config.ticker} with EMA {config.short_window}/{config.long_window}")
        result = analyzer.analyze_single(config)
        
        print(f"Ticker: {result.ticker}")
        print(f"Processing time: {result.processing_time:.2f}s")
        print(f"Has current signal: {result.has_current_signal}")
        print(f"Number of signals: {len(result.signals)}")
        
        if result.error:
            print(f"Error: {result.error}")
        
        for signal in result.signals:
            print(f"  Signal: {signal.ma_type} {signal.short_window}/{signal.long_window}")
            print(f"  Date: {signal.signal_date}")
            print(f"  Type: {signal.signal_type}")
            print(f"  Current: {signal.current}")
            
    finally:
        analyzer.close()


def test_api_service():
    """Test the MA Cross API service."""
    print("\n=== Testing API Service ===")
    
    # Create service
    service = MACrossService()
    
    # Create request with specific windows (not permutations)
    request = MACrossRequest(
        ticker="AAPL",
        windows=5,  # Small window range for testing
        direction="Long",
        strategy_types=["EMA"],
        use_hourly=False
    )
    
    print(f"Request: {request.ticker} with windows up to {request.windows}")
    
    try:
        # Execute synchronous analysis
        response = service.analyze_portfolio(request)
        
        print(f"Status: {response.status}")
        print(f"Execution time: {response.execution_time:.2f}s")
        print(f"Total portfolios: {response.total_portfolios}")
        print(f"Filtered portfolios: {response.filtered_portfolios}")
        
        # Show first few results
        for i, portfolio in enumerate(response.portfolios[:5]):
            print(f"\nPortfolio {i+1}:")
            print(f"  Ticker: {portfolio.ticker}")
            print(f"  Strategy: {portfolio.strategy_type}")
            print(f"  Windows: {portfolio.short_window}/{portfolio.long_window}")
            print(f"  Has signal entry: {portfolio.has_signal_entry}")
            
    except Exception as e:
        print(f"Error: {e}")


def test_scanner_adapter():
    """Test the scanner adapter with a portfolio file."""
    print("\n=== Testing Scanner Adapter ===")
    
    from app.ma_cross.scanner_adapter import ScannerAdapter
    
    adapter = ScannerAdapter()
    
    try:
        config = {
            "PORTFOLIO": "DAILY.csv",
            "USE_HOURLY": False,
            "DIRECTION": "Long",
            "REFRESH": True
        }
        
        # Check if portfolio file exists
        import os
        portfolio_path = f"./csv/strategies/{config['PORTFOLIO']}"
        
        if not os.path.exists(portfolio_path):
            print(f"Portfolio file not found: {portfolio_path}")
            print("Creating a simple test portfolio...")
            
            # Create test portfolio
            import polars as pl
            test_portfolio = pl.DataFrame({
                "Ticker": ["AAPL", "MSFT", "GOOGL"],
                "Short Window": [10, 12, 15],
                "Long Window": [30, 35, 40],
                "Use SMA": [False, False, True]
            })
            
            os.makedirs("./csv/strategies", exist_ok=True)
            test_portfolio.write_csv(portfolio_path)
        
        print(f"Processing portfolio: {config['PORTFOLIO']}")
        result = adapter.process_portfolio_file(portfolio_path, config)
        
        print(f"Analysis date: {result.analysis_date}")
        print(f"Total tickers: {len(result.tickers)}")
        print(f"Signals found: {result.signal_count}")
        
        for ticker_result in result.tickers_with_signals:
            print(f"\n{ticker_result.ticker}:")
            for signal in ticker_result.current_signals:
                print(f"  {signal.ma_type} {signal.short_window}/{signal.long_window}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        adapter.close()


def main():
    """Run all tests."""
    print("MA Cross Refactoring Test Suite")
    print("==============================")
    
    # Test core functionality
    test_core_analyzer()
    
    # Test API service
    test_api_service()
    
    # Test scanner adapter
    test_scanner_adapter()
    
    print("\n=== Tests Complete ===")


if __name__ == "__main__":
    main()