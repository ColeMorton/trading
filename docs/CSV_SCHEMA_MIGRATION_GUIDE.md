# CSV Schema Migration Guide

_External Consumer Migration Documentation_

## Overview

This guide provides comprehensive information for external systems and users consuming CSV exports from the Sensylate Trading Strategy Platform. The platform has migrated to a standardized 59-column canonical schema to ensure data consistency and reliability.

## What Changed

### Before: Multiple Schema Variants

- **14-Column API Schema**: Simplified export with basic metrics
- **58-Column Base Schema**: Raw portfolio analysis without metric type classification
- **59-Column Extended Schema**: Complete schema with metric type (inconsistent implementation)

### After: Unified 59-Column Canonical Schema

- **Single Source of Truth**: All CSV exports now use the same 59-column schema
- **Complete Data Coverage**: All risk metrics, trade analysis, and performance indicators included
- **Consistent Column Naming**: Standardized column names across all export paths

## Schema Specification

### Complete 59-Column Schema

```csv
Ticker,Allocation [%],Strategy Type,Short Window,Long Window,Signal Window,Stop Loss [%],Signal Entry,Signal Exit,Total Open Trades,Total Trades,Metric Type,Score,Win Rate [%],Profit Factor,Expectancy per Trade,Sortino Ratio,Beats BNH [%],Avg Trade Duration,Trades Per Day,Trades per Month,Signals per Month,Expectancy per Month,Start,End,Period,Start Value,End Value,Total Return [%],Benchmark Return [%],Max Gross Exposure [%],Total Fees Paid,Max Drawdown [%],Max Drawdown Duration,Total Closed Trades,Open Trade PnL,Best Trade [%],Worst Trade [%],Avg Winning Trade [%],Avg Losing Trade [%],Avg Winning Trade Duration,Avg Losing Trade Duration,Expectancy,Sharpe Ratio,Calmar Ratio,Omega Ratio,Skew,Kurtosis,Tail Ratio,Common Sense Ratio,Value at Risk,Daily Returns,Annual Returns,Cumulative Returns,Annualized Return,Annualized Volatility,Signal Count,Position Count,Total Period
```

### Column Categories

#### Core Strategy Configuration (Columns 1-12)

| Column            | Type       | Description                      | Example              |
| ----------------- | ---------- | -------------------------------- | -------------------- |
| Ticker            | String     | Asset symbol                     | BTC-USD              |
| Allocation [%]    | Float/Null | Portfolio allocation percentage  | 25.5                 |
| Strategy Type     | String     | Strategy implementation          | EMA, SMA, MACD       |
| Short Window      | Integer    | Short-term moving average period | 20                   |
| Long Window       | Integer    | Long-term moving average period  | 50                   |
| Signal Window     | Integer    | Signal confirmation period       | 0                    |
| Stop Loss [%]     | Float/Null | Stop loss percentage             | -5.0                 |
| Signal Entry      | Boolean    | Current entry signal status      | true                 |
| Signal Exit       | Boolean    | Current exit signal status       | false                |
| Total Open Trades | Integer    | Currently open positions         | 1                    |
| Total Trades      | Integer    | Total completed trades           | 45                   |
| Metric Type       | String     | Performance classification       | High Performance EMA |

#### Performance Metrics (Columns 13-22)

| Column               | Type   | Description                     |
| -------------------- | ------ | ------------------------------- |
| Score                | Float  | Composite performance score     |
| Win Rate [%]         | Float  | Percentage of winning trades    |
| Profit Factor        | Float  | Gross profit / gross loss ratio |
| Expectancy per Trade | Float  | Expected return per trade       |
| Sortino Ratio        | Float  | Risk-adjusted return metric     |
| Beats BNH [%]        | Float  | Outperformance vs buy-and-hold  |
| Avg Trade Duration   | String | Average trade holding period    |
| Trades Per Day       | Float  | Trading frequency               |
| Trades per Month     | Float  | Monthly trading activity        |
| Signals per Month    | Float  | Signal generation frequency     |

#### Portfolio Values & Returns (Columns 23-31)

| Column                 | Type    | Description                 |
| ---------------------- | ------- | --------------------------- |
| Expectancy per Month   | Float   | Monthly expected return     |
| Start                  | Integer | Backtest start index        |
| End                    | Integer | Backtest end index          |
| Period                 | String  | Total backtest duration     |
| Start Value            | Float   | Initial portfolio value     |
| End Value              | Float   | Final portfolio value       |
| Total Return [%]       | Float   | Total return percentage     |
| Benchmark Return [%]   | Float   | Benchmark comparison return |
| Max Gross Exposure [%] | Float   | Maximum portfolio exposure  |

#### Risk & Drawdown Analysis (Columns 32-39)

| Column                | Type    | Description                  |
| --------------------- | ------- | ---------------------------- |
| Total Fees Paid       | Float   | Trading costs                |
| Max Drawdown [%]      | Float   | Maximum portfolio decline    |
| Max Drawdown Duration | String  | Longest drawdown period      |
| Total Closed Trades   | Integer | Completed trade count        |
| Open Trade PnL        | Float   | Unrealized profit/loss       |
| Best Trade [%]        | Float   | Best single trade return     |
| Worst Trade [%]       | Float   | Worst single trade return    |
| Avg Winning Trade [%] | Float   | Average winning trade return |

#### Advanced Trade Analysis (Columns 40-45)

| Column                     | Type   | Description                    |
| -------------------------- | ------ | ------------------------------ |
| Avg Losing Trade [%]       | Float  | Average losing trade return    |
| Avg Winning Trade Duration | String | Average winning trade duration |
| Avg Losing Trade Duration  | String | Average losing trade duration  |
| Expectancy                 | Float  | Mathematical expectancy        |
| Sharpe Ratio               | Float  | Risk-adjusted return           |
| Calmar Ratio               | Float  | Return vs maximum drawdown     |

#### Risk Metrics (Columns 46-55) - **CRITICAL FOR ANALYSIS**

| Column                | Type  | Description                        |
| --------------------- | ----- | ---------------------------------- |
| Omega Ratio           | Float | Probability-weighted ratio         |
| Skew                  | Float | Return distribution asymmetry      |
| Kurtosis              | Float | Return distribution tail thickness |
| Tail Ratio            | Float | Tail risk measurement              |
| Common Sense Ratio    | Float | Risk-adjusted metric               |
| Value at Risk         | Float | Potential loss estimate            |
| Daily Returns         | Float | Average daily return               |
| Annual Returns        | Float | Annualized return                  |
| Cumulative Returns    | Float | Total cumulative return            |
| Annualized Volatility | Float | Annual volatility measure          |

#### Signal & Position Metrics (Columns 56-59)

| Column         | Type    | Description             |
| -------------- | ------- | ----------------------- |
| Signal Count   | Integer | Total signals generated |
| Position Count | Integer | Total positions taken   |
| Total Period   | Float   | Analysis period length  |

## Migration Steps for External Consumers

### Step 1: Update Column Expectations

**If you were using the 14-column API schema:**

```python
# OLD: 14 columns
old_columns = [
    "Ticker", "Strategy Type", "Short Window", "Long Window",
    "Total Trades", "Win Rate [%]", "Total Return [%]",
    "Sharpe Ratio", "Max Drawdown [%]", "Expectancy (per trade)",
    "Profit Factor", "Sortino Ratio", "Beats BNH [%]", "Score"
]

# NEW: 59 columns (all columns from canonical schema)
# Your code should now expect all 59 columns
```

**Column Name Changes:**

- `Expectancy (per trade)` → `Expectancy per Trade`

### Step 2: Handle Additional Columns

**Risk Metrics Now Available:**

```python
# These columns are now available in all exports
risk_metrics = [
    "Skew", "Kurtosis", "Tail Ratio", "Common Sense Ratio",
    "Value at Risk", "Daily Returns", "Annual Returns",
    "Cumulative Returns", "Annualized Return", "Annualized Volatility"
]

# Example: Enhanced risk analysis
def enhanced_risk_analysis(portfolio_data):
    for row in portfolio_data:
        sharpe = float(row["Sharpe Ratio"])
        skew = float(row["Skew"]) if row["Skew"] else 0
        kurtosis = float(row["Kurtosis"]) if row["Kurtosis"] else 3

        # Now you can perform advanced risk analysis
        risk_score = calculate_risk_score(sharpe, skew, kurtosis)
```

### Step 3: Update File Processing Logic

**Before:**

```python
def process_portfolio_csv(file_path):
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        # Expected 14 or 58 columns
        for row in reader:
            ticker = row["Ticker"]
            returns = float(row["Total Return [%]"])
            # Limited analysis possible
```

**After:**

```python
def process_portfolio_csv(file_path):
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        # Always expect 59 columns
        headers = reader.fieldnames
        assert len(headers) == 59, f"Expected 59 columns, got {len(headers)}"

        for row in reader:
            ticker = row["Ticker"]
            returns = float(row["Total Return [%]"])
            allocation = float(row["Allocation [%]"]) if row["Allocation [%]"] else None

            # Enhanced analysis with risk metrics
            var = float(row["Value at Risk"]) if row["Value at Risk"] else 0
            skew = float(row["Skew"]) if row["Skew"] else 0

            # Comprehensive portfolio analysis now possible
```

### Step 4: Handle Null Values

**Important:** Some columns may contain null values, especially:

- `Allocation [%]` - May be null if no allocation specified
- `Stop Loss [%]` - May be null if no stop loss configured
- Risk metrics - May be null if insufficient data for calculation

```python
def safe_float_conversion(value, default=0.0):
    """Safely convert string to float, handling null values."""
    if value is None or value == "" or value == "None":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

# Usage
allocation = safe_float_conversion(row["Allocation [%]"], None)
stop_loss = safe_float_conversion(row["Stop Loss [%]"], None)
```

## Data Quality Improvements

### Enhanced Reliability

- **Consistent Column Order**: All files now have identical column ordering
- **Complete Data Coverage**: No missing metrics across different export paths
- **Validated Exports**: All CSV files are validated before export

### New Capabilities Enabled

- **Advanced Risk Analysis**: Access to skew, kurtosis, VaR, and tail metrics
- **Cross-Strategy Comparison**: Consistent schema enables easy aggregation
- **Time-Series Analysis**: Enhanced duration and frequency metrics
- **Portfolio Optimization**: Allocation and exposure data now available

## Backward Compatibility

### API Responses

- **PortfolioMetrics Model**: API JSON responses maintain the same 14-field structure
- **No Breaking Changes**: Existing API consumers are not affected
- **CSV Export Enhanced**: Only CSV exports have been expanded to 59 columns

### Legacy File Support

- **Automatic Migration**: Legacy CSV files are automatically converted to canonical schema when processed
- **Schema Detection**: System automatically detects and migrates older schema versions

## Validation and Testing

### CSV File Validation

```python
from app.tools.portfolio.canonical_schema import CANONICAL_COLUMN_NAMES, CANONICAL_COLUMN_COUNT

def validate_csv_schema(file_path):
    """Validate that a CSV file conforms to canonical schema."""
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)

        if len(headers) != CANONICAL_COLUMN_COUNT:
            raise ValueError(f"Expected {CANONICAL_COLUMN_COUNT} columns, got {len(headers)}")

        if headers != CANONICAL_COLUMN_NAMES:
            raise ValueError("Column names or order doesn't match canonical schema")

        return True
```

### Integration Testing

```python
def test_csv_integration():
    """Test that your integration handles the new schema correctly."""
    # Use the provided sample data for testing
    sample_file = "sample_canonical_portfolio.csv"

    # Your processing function should handle all 59 columns
    result = your_processing_function(sample_file)

    # Verify that you can access new risk metrics
    assert "Skew" in result
    assert "Value at Risk" in result
```

## Performance Considerations

### File Size Impact

- **Larger Files**: CSV files are now approximately 4x larger (14→59 columns)
- **Processing Time**: Expect 10-20% increase in parsing time
- **Storage**: Plan for increased storage requirements

### Optimization Recommendations

```python
# Use pandas for efficient processing of large files
import pandas as pd

def efficient_csv_processing(file_path):
    """Efficiently process large CSV files with 59 columns."""
    # Read only required columns if you don't need all data
    required_columns = ["Ticker", "Total Return [%]", "Sharpe Ratio", "Skew"]

    df = pd.read_csv(file_path, usecols=required_columns)
    return df

# For streaming large files
def stream_csv_processing(file_path):
    """Stream process large CSV files."""
    chunk_size = 1000
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        # Process chunk
        yield process_chunk(chunk)
```

## Support and Migration Assistance

### Sample Data

The platform provides sample CSV files with the new schema:

- `sample_canonical_portfolio.csv` - Reference implementation
- `sample_risk_metrics.csv` - Focus on risk metric usage

### Migration Tools

- **Schema Validator**: Use `app.tools.portfolio.schema_validation` for validation
- **CSV Scanner**: Use `tests.tools.csv_directory_scanner` for bulk validation

### Common Migration Issues

#### Issue 1: Column Count Mismatch

```python
# Error: Expected 14 columns, got 59
# Solution: Update your column expectations
assert len(headers) == 59  # Not 14
```

#### Issue 2: Missing Column Access

```python
# Error: KeyError: 'Expectancy (per trade)'
# Solution: Use new column name
expectancy = row["Expectancy per Trade"]  # Not "Expectancy (per trade)"
```

#### Issue 3: Null Value Handling

```python
# Error: ValueError: could not convert string to float: 'None'
# Solution: Handle null values
value = float(row["Allocation [%]"]) if row["Allocation [%]"] else None
```

## Contact and Support

For migration assistance or questions:

- **Technical Documentation**: `/docs/USER_MANUAL.md`
- **Schema Reference**: `/app/tools/portfolio/canonical_schema.py`
- **Validation Tools**: `/tests/tools/csv_directory_scanner.py`

## Change Log

### v2.0.0 - CSV Schema Standardization

- **Added**: 45 new columns for comprehensive analysis
- **Changed**: Column name `Expectancy (per trade)` → `Expectancy per Trade`
- **Enhanced**: All CSV exports now use 59-column canonical schema
- **Maintained**: API JSON response backward compatibility

---

_This migration guide ensures smooth transition to the enhanced CSV schema while maintaining data integrity and expanding analysis capabilities._
