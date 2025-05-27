"""
Simple test for MA Cross refactoring.

Tests just the core functionality without full permutations.
"""

import sys
from app.ma_cross.core import MACrossAnalyzer, AnalysisConfig


def main():
    """Test core analyzer with specific windows."""
    print("Testing MA Cross Core Analyzer")
    print("=" * 30)
    
    # Create analyzer
    analyzer = MACrossAnalyzer()
    
    try:
        # Test with specific windows (not permutations)
        config = AnalysisConfig(
            ticker="AAPL",
            use_sma=False,
            use_hourly=False,
            direction="Long",
            short_window=10,  # Specific short window
            long_window=30    # Specific long window
        )
        
        print(f"\nAnalyzing {config.ticker} with EMA {config.short_window}/{config.long_window}")
        result = analyzer.analyze_single(config)
        
        print(f"Analysis completed in {result.processing_time:.2f}s")
        
        if result.error:
            print(f"Error: {result.error}")
            return 1
        
        print(f"Has current signal: {result.has_current_signal}")
        print(f"Number of signals: {len(result.signals)}")
        
        for signal in result.signals:
            print(f"\nSignal detected:")
            print(f"  Type: {signal.ma_type}")
            print(f"  Windows: {signal.short_window}/{signal.long_window}")
            print(f"  Date: {signal.signal_date}")
            print(f"  Signal: {signal.signal_type}")
            print(f"  Current: {signal.current}")
        
        # Test result conversion
        result_dict = result.to_dict()
        print(f"\nResult as dict: {list(result_dict.keys())}")
        
        return 0
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        analyzer.close()


if __name__ == "__main__":
    sys.exit(main())