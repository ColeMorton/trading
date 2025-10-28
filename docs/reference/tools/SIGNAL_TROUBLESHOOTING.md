# Signal Processing Troubleshooting Guide

This document provides comprehensive troubleshooting guidance for the signal processing pipeline, helping to identify and resolve common issues that may arise during signal generation, filtering, quality assessment, and conversion to trades.

## Table of Contents

1. [Diagnostic Approach](#diagnostic-approach)
2. [Signal Generation Issues](#signal-generation-issues)
3. [Signal Filtering Issues](#signal-filtering-issues)
4. [Signal Quality Issues](#signal-quality-issues)
5. [Horizon Analysis Issues](#horizon-analysis-issues)
6. [Signal-to-Trade Conversion Issues](#signal-to-trade-conversion-issues)
7. [Performance Issues](#performance-issues)
8. [Configuration Issues](#configuration-issues)
9. [Logging and Debugging](#logging-and-debugging)

## Diagnostic Approach

When troubleshooting signal processing issues, follow this systematic approach:

1. **Identify the Symptom**: Clearly define what's not working as expected
2. **Isolate the Stage**: Determine which stage of the signal lifecycle is affected
3. **Check Logs**: Review logs for errors, warnings, or unusual patterns
4. **Verify Configuration**: Ensure configuration parameters are valid
5. **Test Components**: Test individual components in isolation
6. **Analyze Data Flow**: Trace data through the pipeline to find where issues occur
7. **Apply Fix**: Implement the solution and verify it resolves the issue
8. **Document**: Document the issue and solution for future reference

## Signal Generation Issues

### No Signals Generated

**Symptoms**:

- Zero signals in output
- Empty signal DataFrame
- "No signals found" log messages

**Possible Causes**:

1. **Strategy parameters too restrictive**
2. **Incorrect market data**
3. **Data preprocessing issues**
4. **Logic errors in signal generation code**

**Diagnostic Steps**:

1. **Verify market data**:

   ```python
   # Check for missing or invalid data
   print(f"Data shape: {data.shape}")
   print(f"Missing values: {data.isna().sum()}")
   print(f"Data range: {data['Date'].min()} to {data['Date'].max()}")
   ```

2. **Check strategy parameters**:

   ```python
   # Log strategy parameters
   logger.info("Strategy parameters", {
       "fast_period": fast_period,
       "slow_period": slow_period,
       "threshold": threshold
   })
   ```

3. **Verify indicator calculation**:

   ```python
   # Check if indicators are calculated correctly
   print(f"Indicator stats: {data['indicator'].describe()}")
   ```

4. **Test with relaxed parameters**:
   ```python
   # Try with more relaxed parameters
   relaxed_signals = generate_signals(data, fast_period=5, slow_period=20, threshold=0.5)
   print(f"Signals with relaxed parameters: {relaxed_signals['Signal'].abs().sum()}")
   ```

**Solutions**:

1. **Adjust strategy parameters** to be less restrictive
2. **Fix data quality issues** by cleaning and validating market data
3. **Debug indicator calculation** to ensure correct values
4. **Review signal generation logic** for errors or edge cases

### Too Many Signals

**Symptoms**:

- Excessive number of signals
- Signals occurring too frequently
- Poor signal quality due to noise

**Possible Causes**:

1. **Strategy parameters too loose**
2. **Noisy market data**
3. **Insufficient filtering**
4. **Duplicate signal generation**

**Diagnostic Steps**:

1. **Count signals by time period**:

   ```python
   # Count signals by month
   monthly_signals = data[data['Signal'] != 0].groupby(pd.Grouper(key='Date', freq='M')).size()
   print(f"Monthly signal counts:\n{monthly_signals}")
   ```

2. **Check for duplicates**:

   ```python
   # Check for consecutive signals
   consecutive_signals = 0
   for i in range(1, len(data)):
       if data['Signal'].iloc[i] != 0 and data['Signal'].iloc[i-1] != 0:
           consecutive_signals += 1
   print(f"Consecutive signals: {consecutive_signals}")
   ```

3. **Analyze signal distribution**:
   ```python
   # Analyze signal distribution
   signal_values = data[data['Signal'] != 0]['Signal'].value_counts()
   print(f"Signal distribution:\n{signal_values}")
   ```

**Solutions**:

1. **Adjust strategy parameters** to be more restrictive
2. **Add or strengthen filters** to reduce noise
3. **Implement signal consolidation** to combine nearby signals
4. **Add cooldown periods** to prevent excessive trading

## Signal Filtering Issues

### Excessive Signal Rejection

**Symptoms**:

- Too many signals rejected by filters
- Very few signals remaining after filtering
- High rejection rates in filter statistics

**Possible Causes**:

1. **Filter thresholds too strict**
2. **Incompatible filter combinations**
3. **Data quality issues affecting filter criteria**
4. **Incorrect filter configuration**

**Diagnostic Steps**:

1. **Analyze filter statistics**:

   ```python
   # Get detailed filter statistics
   _, stats = filter_signals(data, config, log)

   # Analyze rejection reasons
   for filter_stat in stats["filter_stats"]:
       print(f"Filter: {filter_stat['filter_name']}")
       print(f"  Pass rate: {filter_stat['pass_rate']:.2f}")
       print(f"  Rejection reasons: {filter_stat['rejection_reasons']}")
   ```

2. **Test filters individually**:

   ```python
   # Create a custom pipeline with only one filter
   from app.tools.signal_filtering import SignalFilterPipeline, RSIFilter

   pipeline = SignalFilterPipeline(log)
   pipeline.add_filter(RSIFilter(log))

   # Apply single filter
   filtered_data = pipeline.apply_filters(data, config)
   filter_stats = pipeline.get_pipeline_stats()
   print(f"RSI filter only stats: {filter_stats}")
   ```

3. **Check filter configuration**:
   ```python
   # Print filter configuration
   print("Filter configuration:")
   for key, value in config.items():
       if key.startswith(('USE_', 'RSI_', 'MIN_', 'MAX_')):
           print(f"  {key}: {value}")
   ```

**Solutions**:

1. **Adjust filter thresholds** to be less restrictive
2. **Remove or modify problematic filters**
3. **Apply filters selectively** based on market conditions
4. **Fix data quality issues** affecting filter criteria

### Insufficient Filtering

**Symptoms**:

- Too many low-quality signals passing through filters
- Low rejection rates in filter statistics
- Poor performance of filtered signals

**Possible Causes**:

1. **Filter thresholds too loose**
2. **Missing important filters**
3. **Filters not applied correctly**
4. **Incorrect filter configuration**

**Diagnostic Steps**:

1. **Analyze signal quality before and after filtering**:

   ```python
   from app.tools.metrics_calculation import calculate_signal_quality_metrics

   # Calculate metrics before filtering
   pre_metrics = calculate_signal_quality_metrics(data, returns_df, "pre_filter")

   # Apply filters
   filtered_data, _ = filter_signals(data, config, log)

   # Calculate metrics after filtering
   post_metrics = calculate_signal_quality_metrics(filtered_data, returns_df, "post_filter")

   # Compare
   print(f"Pre-filter quality score: {pre_metrics['signal_quality_score']:.2f}")
   print(f"Post-filter quality score: {post_metrics['signal_quality_score']:.2f}")
   ```

2. **Check filter effectiveness**:
   ```python
   # Check if filters are actually being applied
   for filter_name in ['RSI', 'Volume', 'Volatility']:
       use_key = f"USE_{filter_name.upper()}_FILTER" if filter_name != 'RSI' else "USE_RSI"
       is_enabled = config.get(use_key, False)
       print(f"{filter_name} filter enabled: {is_enabled}")
   ```

**Solutions**:

1. **Adjust filter thresholds** to be more restrictive
2. **Add additional filters** for specific issues
3. **Create custom filters** for strategy-specific requirements
4. **Implement adaptive filtering** based on market conditions

## Signal Quality Issues

### Low Signal Quality Scores

**Symptoms**:

- Low signal quality scores
- Poor performance metrics
- Low win rates or profit factors

**Possible Causes**:

1. **Strategy not effective in current market conditions**
2. **Insufficient filtering of low-quality signals**
3. **Issues with quality metric calculation**
4. **Incorrect quality score weights**

**Diagnostic Steps**:

1. **Analyze individual quality metrics**:

   ```python
   # Calculate detailed metrics
   metrics = calculate_signal_quality_metrics(signals_df, returns_df, "analysis")

   # Print key metrics
   print(f"Win rate: {metrics['win_rate']:.2f}")
   print(f"Profit factor: {metrics['profit_factor']:.2f}")
   print(f"Risk-reward ratio: {metrics['risk_reward_ratio']:.2f}")
   print(f"Expectancy per trade: {metrics['expectancy_per_trade']:.4f}")
   ```

2. **Check quality score calculation**:

   ```python
   # Manually calculate quality score
   win_rate = metrics['win_rate']
   profit_factor = min(metrics['profit_factor'], 5.0) / 5.0
   risk_reward = metrics['avg_return'] / max(abs(metrics['avg_loss']), 0.001)
   positive_return = 1.0 if metrics['avg_return'] > 0 else 0.0

   manual_score = 10.0 * (
       0.4 * win_rate +
       0.3 * profit_factor +
       0.2 * risk_reward +
       0.1 * positive_return
   )

   print(f"Calculated score: {metrics['signal_quality_score']:.2f}")
   print(f"Manual score: {manual_score:.2f}")
   ```

3. **Segment analysis by time period**:

   ```python
   # Add date column if not present
   if 'Date' not in signals_df.columns:
       signals_df['Date'] = pd.date_range(start='2020-01-01', periods=len(signals_df))

   # Split into time periods
   periods = {}
   for year in range(2020, 2023):
       mask = (signals_df['Date'] >= f'{year}-01-01') & (signals_df['Date'] < f'{year+1}-01-01')
       period_signals = signals_df[mask].copy()
       period_returns = returns_df[mask].copy()

       if len(period_signals) > 0:
           periods[year] = calculate_signal_quality_metrics(period_signals, period_returns, f"year_{year}")

   # Compare periods
   for year, metrics in periods.items():
       print(f"Year {year}:")
       print(f"  Quality score: {metrics['signal_quality_score']:.2f}")
       print(f"  Win rate: {metrics['win_rate']:.2f}")
       print(f"  Profit factor: {metrics['profit_factor']:.2f}")
   ```

**Solutions**:

1. **Improve signal filtering** to remove low-quality signals
2. **Adjust strategy parameters** to adapt to current market conditions
3. **Implement market regime detection** to apply different strategies
4. **Review and adjust quality score weights** if needed

## Horizon Analysis Issues

### Incorrect Horizon Selection

**Symptoms**:

- Suboptimal horizon selection
- Inconsistent best horizon results
- Poor performance at selected horizon

**Possible Causes**:

1. **Forward-looking bias in horizon calculation**
2. **Insufficient data for reliable horizon metrics**
3. **Inappropriate horizon selection criteria**
4. **Calculation errors in horizon metrics**

**Diagnostic Steps**:

1. **Analyze all horizon metrics**:

   ```python
   from app.tools.horizon_calculation import calculate_horizon_metrics

   # Calculate horizon metrics
   horizon_metrics = calculate_horizon_metrics(signals, returns)

   # Print metrics for each horizon
   for horizon, metrics in horizon_metrics.items():
       print(f"Horizon {horizon}:")
       print(f"  Avg return: {metrics['avg_return']:.4f}")
       print(f"  Win rate: {metrics['win_rate']:.2f}")
       print(f"  Sharpe: {metrics['sharpe']:.2f}")
       print(f"  Sample size: {metrics['sample_size']}")
   ```

2. **Check horizon selection logic**:

   ```python
   from app.tools.horizon_calculation import find_best_horizon

   # Get configuration
   config = {
       "SHARPE_WEIGHT": 0.6,
       "WIN_RATE_WEIGHT": 0.3,
       "SAMPLE_SIZE_WEIGHT": 0.1,
       "SAMPLE_SIZE_FACTOR": 100,
       "MIN_SAMPLE_SIZE": 20
   }

   # Find best horizon
   best_horizon = find_best_horizon(horizon_metrics, config)
   print(f"Best horizon: {best_horizon}")

   # Manually calculate scores
   for horizon, metrics in horizon_metrics.items():
       sharpe = metrics.get("sharpe", 0)
       win_rate = metrics.get("win_rate", 0)
       sample_size = metrics.get("sample_size", 0)

       if sample_size < config["MIN_SAMPLE_SIZE"]:
           print(f"Horizon {horizon}: Insufficient sample size")
           continue

       sample_size_norm = min(1.0, sample_size / config["SAMPLE_SIZE_FACTOR"])
       score = (
           config["SHARPE_WEIGHT"] * sharpe +
           config["WIN_RATE_WEIGHT"] * win_rate +
           config["SAMPLE_SIZE_WEIGHT"] * sample_size_norm
       )

       print(f"Horizon {horizon}: Score = {score:.4f}")
   ```

**Solutions**:

1. **Fix forward-looking bias** in horizon calculation
2. **Increase minimum sample size** for more reliable metrics
3. **Adjust horizon selection weights** based on strategy goals
4. **Implement cross-validation** for horizon selection

### Slow Horizon Calculation

**Symptoms**:

- Horizon calculation takes too long
- Performance bottlenecks in horizon analysis
- Timeouts or memory issues with large datasets

**Possible Causes**:

1. **Inefficient calculation algorithm**
2. **Redundant calculations**
3. **Memory management issues**
4. **Lack of caching for repeated calculations**

**Diagnostic Steps**:

1. **Profile calculation time**:

   ```python
   import time

   # Measure calculation time
   start_time = time.time()
   horizon_metrics = calculate_horizon_metrics(signals, returns)
   end_time = time.time()

   print(f"Calculation time: {end_time - start_time:.4f} seconds")
   ```

2. **Test with and without caching**:

   ```python
   # Test with caching enabled
   start_time = time.time()
   horizon_metrics1 = calculate_horizon_metrics(signals, returns, use_cache=True)
   cache_time = time.time() - start_time

   # Test with caching disabled
   start_time = time.time()
   horizon_metrics2 = calculate_horizon_metrics(signals, returns, use_cache=False)
   no_cache_time = time.time() - start_time

   print(f"With cache: {cache_time:.4f} seconds")
   print(f"Without cache: {no_cache_time:.4f} seconds")
   print(f"Speedup: {no_cache_time / cache_time:.2f}x")
   ```

**Solutions**:

1. **Use the optimized horizon calculation module** with caching
2. **Limit the number of horizons** to calculate
3. **Implement batch processing** for large datasets
4. **Use vectorized operations** instead of loops where possible

## Logging and Debugging

### Effective Logging

**Best Practices**:

1. **Use structured logging**:

   ```python
   from app.tools.structured_logging import get_logger

   # Create logger
   logger = get_logger("signal_processing")

   # Log with context
   logger.info("Processing signals", {
       "strategy": "ma_cross",
       "symbols": 100,
       "time_period": "2020-2022"
   })
   ```

2. **Log at appropriate levels**:

   ```python
   # Debug: Detailed information for debugging
   logger.debug("Calculating indicator with parameters", {"window": 20, "alpha": 0.5})

   # Info: General information about program execution
   logger.info("Processing completed successfully")

   # Warning: Potential issues that don't prevent execution
   logger.warning("Using default parameter value", {"param": "threshold", "value": 0.5})

   # Error: Errors that prevent normal execution
   logger.error("Failed to load data file", {"file": "data.csv"})

   # Critical: Critical errors requiring immediate attention
   logger.critical("Database connection failed", {"server": "main", "attempts": 3})
   ```

3. **Log method execution**:

   ```python
   from app.tools.structured_logging import log_method

   @log_method()
   def calculate_metrics(data, config):
       # Function implementation
       return result
   ```

### Debugging Techniques

1. **Trace data flow**:

   ```python
   # Log data shape at each stage
   logger.debug("Input data", {"shape": data.shape, "columns": list(data.columns)})

   # After preprocessing
   logger.debug("After preprocessing", {"shape": processed_data.shape, "nulls": processed_data.isna().sum().to_dict()})

   # After signal generation
   logger.debug("After signal generation", {"signal_count": (signals['Signal'] != 0).sum()})
   ```

2. **Use context managers for timing**:

   ```python
   from contextlib import contextmanager
   import time

   @contextmanager
   def timing(name):
       start = time.time()
       yield
       end = time.time()
       logger.debug(f"Timing: {name}", {"duration": f"{end - start:.4f}s"})

   # Usage
   with timing("signal_generation"):
       signals = generate_signals(data)
   ```

3. **Implement validation checks**:

   ```python
   def validate_signals(signals_df):
       """Validate signal data for common issues."""
       issues = []

       # Check for missing values
       if signals_df.isna().any().any():
           issues.append("Contains missing values")

       # Check for invalid signal values
       valid_values = [-1, 0, 1]
       invalid_signals = signals_df[~signals_df['Signal'].isin(valid_values)]
       if len(invalid_signals) > 0:
           issues.append(f"Contains invalid signal values: {invalid_signals['Signal'].unique()}")

       # Check for consecutive signals
       consecutive = 0
       for i in range(1, len(signals_df)):
           if signals_df['Signal'].iloc[i] != 0 and signals_df['Signal'].iloc[i-1] != 0:
               consecutive += 1
       if consecutive > 0:
           issues.append(f"Contains {consecutive} consecutive signals")

       return issues

   # Usage
   issues = validate_signals(signals_df)
   if issues:
       logger.warning("Signal validation issues", {"issues": issues})
   ```

### Configuration Validation

1. **Validate configuration before use**:

   ```python
   from app.tools.config_management import get_config_manager

   # Get configuration manager
   manager = get_config_manager()

   try:
       # Validate configuration
       manager.set_config("signal_filter", filter_config)
       logger.info("Configuration validated successfully")
   except Exception as e:
       logger.error("Configuration validation failed", {"error": str(e)})
   ```

2. **Log configuration at startup**:

   ```python
   # Log configuration at startup
   logger.info("Starting with configuration", {
       "filter_config": filter_config,
       "metrics_config": metrics_config,
       "horizon_config": horizon_config
   })
   ```

3. **Create configuration presets for testing**:

   ```python
   from app.tools.config_management import register_preset

   # Register test configuration preset
   register_preset(
       "test_preset",
       "signal_filter",
       {
           "USE_RSI": True,
           "RSI_THRESHOLD": 50,
           "DIRECTION": "Long"
       },
       "Configuration for testing"
   )
   ```
