# Trade History Export Usage Guide

## Overview

Trade history export functionality provides comprehensive trade data extraction from VectorBT portfolios, including trades, orders, positions, and analytics. The data is exported to JSON format for easy analysis.

## Important Usage Restriction

**Trade history export is ONLY available through `app/concurrency/review.py`** to prevent generating thousands of files from parameter sweep strategies.

### Why This Restriction Exists

The MA Cross strategy (`app/strategies/ma_cross/1_get_portfolios.py`) runs parameter sweeps with ~3,828 window combinations per strategy type. If trade history export were enabled, this would generate thousands of JSON files (one per combination), which would:

- Consume excessive disk space
- Create file management issues
- Slow down strategy execution
- Provide little analytical value for parameter optimization

## How to Use Trade History Export

### 1. Through Concurrency Review (Recommended)

```bash
python app/concurrency/review.py
```

This automatically enables trade history export for the strategies being analyzed.

### 2. Export Format

Trade history is exported to:

- **Location**: `./json/trade_history/`
- **Format**: Single JSON file per strategy
- **Naming**: `{TICKER}_{TIMEFRAME}_{STRATEGY}_{PARAMS}.json`

Examples:

- `BTC-USD_D_SMA_20_50.json`
- `ETH-USD_H_EMA_12_26_SHORT.json`
- `MSTR_D_MACD_12_26_9_SL_0.0500.json`

### 3. JSON Structure

Each exported file contains:

```json
{
  "metadata": {
    "export_timestamp": "2025-01-01T12:00:00",
    "strategy_config": {...},
    "portfolio_summary": {...}
  },
  "trades": [...],
  "orders": [...],
  "positions": [...],
  "analytics": {...}
}
```

## Strategy-Specific Behavior

### MA Cross Strategy

- **Trade history export**: **DISABLED**
- **Safeguards**: Config key `EXPORT_TRADE_HISTORY` is automatically removed
- **Warning**: Users are directed to use `app/concurrency/review.py`

### Monte Carlo Strategy

- **Trade history export**: **DISABLED**
- **Safeguards**: Config key `EXPORT_TRADE_HISTORY` is automatically removed

### Other Strategies

- Trade history export is available when called through `app/concurrency/review.py`
- Direct backtest calls respect the `EXPORT_TRADE_HISTORY` config setting

## Testing

Comprehensive test coverage includes:

- Unit tests for core export functionality
- Integration tests with backtest system
- Performance tests with large datasets
- Safeguard tests to verify blocking behavior

Run tests:

```bash
python -m pytest tests/tools/test_trade_history_*.py -v
```

## Technical Details

### Implementation

- Core functionality: `app/tools/trade_history_exporter.py`
- Integration: `app/tools/backtest_strategy.py`
- Safeguards: Strategy entry point files

### Data Enrichment

- Trade duration and performance categorization
- Rolling statistics and cumulative metrics
- Entry/exit timestamps and price information
- Comprehensive portfolio analytics
