#!/usr/bin/env python3
"""
Test MACD filtering specifically
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import polars as pl
from app.tools.strategy.filter_portfolios import filter_portfolios
from app.strategies.macd.config_types import DEFAULT_CONFIG
from app.tools.setup_logging import setup_logging

def test_macd_filtering():
    """Test MACD portfolio filtering specifically"""
    print("=== MACD Filtering Test ===")
    
    # Setup logging
    log, log_close, _, _ = setup_logging(
        module_name="test_filtering", 
        log_file="test_macd_filtering.log"
    )
    
    try:
        # Read the base MACD portfolios that were created
        base_file = "/Users/colemorton/Projects/trading/data/raw/portfolios/TSLA_D_MACD.csv"
        print(f"Reading base portfolios from: {base_file}")
        
        portfolios_df = pl.read_csv(base_file)
        print(f"Base portfolios shape: {portfolios_df.shape}")
        print(f"Base portfolios columns: {portfolios_df.columns}")
        
        # Show first few rows
        print("\nFirst 3 rows:")
        print(portfolios_df.head(3))
        
        # Setup config for filtering
        test_config = DEFAULT_CONFIG.copy()
        test_config["TICKER"] = "TSLA" 
        
        print(f"\nFiltering config MINIMUMS: {test_config.get('MINIMUMS', 'Not set')}")
        
        # Try filtering
        print("\nAttempting to filter portfolios...")
        filtered_portfolios = filter_portfolios(portfolios_df, test_config, log)
        
        if filtered_portfolios is not None:
            print(f"✅ Filtering successful! Shape: {filtered_portfolios.shape}")
            print(f"Filtered columns: {filtered_portfolios.columns}")
        else:
            print("❌ Filtering returned None")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        log_close()

if __name__ == "__main__":
    test_macd_filtering()