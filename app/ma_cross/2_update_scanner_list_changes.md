# Changes Required for Scanner List Update Module

## Overview
Create a new focused function in strategy_execution.py that leverages the existing tools to maintain consistent schema and behavior with 1_get_portfolios.py.

## Implementation Details

### 1. New Function in strategy_execution.py
```python
def execute_single_strategy(
    ticker: str,
    config: Config,
    log: callable
) -> Optional[Dict]:
    """Execute a single strategy with specified parameters.
    
    This function tests a specific MA strategy (SMA or EMA) with exact window
    parameters, using the same workflow as execute_strategy but without
    parameter searching or filtering.
    
    Args:
        ticker: The ticker symbol
        config: Configuration containing:
            - USE_SMA: bool (True for SMA, False for EMA)
            - SHORT_WINDOW: int (Fast MA period)
            - LONG_WINDOW: int (Slow MA period)
            - Other standard config parameters
        log: Logging function
        
    Returns:
        Optional[Dict]: Strategy performance metrics if successful, None otherwise
    """
    try:
        # Get data and generate signals
        data = process_current_signals(ticker, config, log)
        if data is None or len(data) == 0:
            return None
            
        # Run backtest using app/ma_cross/tools/backtest_strategy.py
        portfolio = backtest_strategy(data, config, log)
        if portfolio is None:
            return None
            
        # Get raw stats from vectorbt
        stats = portfolio.stats()
        
        # Convert stats using app/tools/stats_converter.py
        converted_stats = convert_stats(stats, log, config)
        
        # Add strategy identification fields
        converted_stats.update({
            "Ticker": ticker,
            "Use SMA": config.get("USE_SMA", False),
            "SMA_FAST": config["SHORT_WINDOW"] if config.get("USE_SMA", False) else None,
            "SMA_SLOW": config["LONG_WINDOW"] if config.get("USE_SMA", False) else None,
            "EMA_FAST": config["SHORT_WINDOW"] if not config.get("USE_SMA", False) else None,
            "EMA_SLOW": config["LONG_WINDOW"] if not config.get("USE_SMA", False) else None
        })
        
        return converted_stats
            
    except Exception as e:
        log(f"Failed to execute strategy: {str(e)}", "error")
        return None
```

### 2. Update 2_get_scanner_list.py
```python
def run(config: Config = CONFIG) -> bool:
    """Run scanner list update process."""
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='2_get_scanner_list.log'
    )
    
    try:
        # Initialize configuration
        config = get_config(config)
        
        # Read scanner list
        scanner_path = os.path.join("app", "ma_cross", "scanner_lists", config["SCANNER_LIST"])
        df = pl.read_csv(scanner_path)
        log(f"Loaded scanner list: {config['SCANNER_LIST']}")
        
        # Process each row
        results = []
        for row in df.iter_rows(named=True):
            ticker = row["TICKER"]
            log(f"Processing {ticker}")
            
            # Check for SMA strategy
            if not pl.Series([row["SMA_FAST"], row["SMA_SLOW"]]).is_null().any():
                sma_config = {
                    **config,
                    "TICKER": ticker,
                    "USE_SMA": True,
                    "SHORT_WINDOW": int(row["SMA_FAST"]),
                    "LONG_WINDOW": int(row["SMA_SLOW"])
                }
                sma_result = execute_single_strategy(ticker, sma_config, log)
                if sma_result:
                    results.append(sma_result)
                    
            # Check for EMA strategy
            if not pl.Series([row["EMA_FAST"], row["EMA_SLOW"]]).is_null().any():
                ema_config = {
                    **config,
                    "TICKER": ticker,
                    "USE_SMA": False,
                    "SHORT_WINDOW": int(row["EMA_FAST"]),
                    "LONG_WINDOW": int(row["EMA_SLOW"])
                }
                ema_result = execute_single_strategy(ticker, ema_config, log)
                if ema_result:
                    results.append(ema_result)
            
        # Export results using app/ma_cross/tools/export_portfolios.py
        if len(results) > 0:
            df, success = export_portfolios(
                portfolios=results,
                config=config,
                export_type="portfolios_best",  # Use portfolios_best type for consistent schema
                log=log
            )
            if success:
                log("Scanner list update completed successfully")
                log_close()
                return True
            else:
                raise Exception("Failed to export results")
        else:
            raise Exception("No valid results to export")
            
    except Exception as e:
        log(f"Scanner list update failed: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    run()
```

## Key Points

1. Maintains consistency with existing tools:
   - Uses ma_cross/tools/backtest_strategy.py for vectorbt backtesting
   - Uses tools/stats_converter.py for metric formatting
   - Uses ma_cross/tools/export_portfolios.py for export formatting

2. Follows same workflow as 1_get_portfolios.py:
   - Process signals
   - Run backtest
   - Convert stats
   - Export results

3. Ensures consistent schema:
   - Uses portfolios_best export type for proper column ordering
   - Maintains same metric calculations and formatting

## Testing Steps

1. Test with DAILY_test.csv input
2. Verify window combinations are tested exactly as specified
3. Compare output schema with existing portfolios_best exports
4. Validate all metrics are included and formatted correctly
5. Check error handling