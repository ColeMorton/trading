# CSV Schemas in Trading System

This document outlines the CSV schemas used by the following files:

- `app/concurrency/review.py`
- `app/ma_cross/1_get_portfolios.py`
- `app/strategies/update_portfolios.py`

## 1. Strategy Portfolio CSV Schema

This is the primary CSV schema used across all three files, with columns for strategy parameters and performance metrics.

**Header Fields:**

```
Ticker,Strategy Type,Short Window,Long Window,Signal Window,Signal Entry,Signal Exit,Total Open Trades,Total Trades,Score,Win Rate [%],Profit Factor,Expectancy per Trade,Sortino Ratio,Beats BNH [%],Avg Trade Duration,Trades Per Day,Trades per Month,Signals per Month,Expectancy per Month,Start,End,Period,Start Value,End Value,Total Return [%],Benchmark Return [%],Max Gross Exposure [%],Total Fees Paid,Max Drawdown [%],Max Drawdown Duration,Total Closed Trades,Open Trade PnL,Best Trade [%],Worst Trade [%],Avg Winning Trade [%],Avg Losing Trade [%],Avg Winning Trade Duration,Avg Losing Trade Duration,Expectancy,Sharpe Ratio,Calmar Ratio,Omega Ratio,Skew,Kurtosis,Tail Ratio,Common Sense Ratio,Value at Risk,Daily Returns,Annual Returns,Cumulative Returns,Annualized Return,Annualized Volatility,Signal Count,Position Count,Total Period
```

**Used By:**

- `app/concurrency/review.py`: Loads portfolio files like "trades_20250520.csv"
- `app/ma_cross/1_get_portfolios.py`: Processes and exports strategy portfolios
- `app/strategies/update_portfolios.py`: Updates portfolios with new strategy results

## 2. Extended Strategy Portfolio CSV Schema

An extended version of the Strategy Portfolio schema that includes allocation percentages, stop loss values, and position tracking dates.

**Header Fields:**

```
Ticker,Allocation [%],Strategy Type,Short Window,Long Window,Signal Window,Stop Loss [%],Signal Entry,Signal Exit,Total Open Trades,Total Trades,Score,Win Rate [%],Profit Factor,Expectancy per Trade,Sortino Ratio,Beats BNH [%],...,Last Position Open Date,Last Position Close Date
```

**Key Differences from Base Schema:**

- Addition of `Allocation [%]` column (59th column) - specifies allocation percentage for the strategy
- Addition of `Stop Loss [%]` column (60th column) - specifies stop loss percentage for the strategy
- Addition of `Last Position Open Date` column (61st column) - date when the last position was opened (YYYY-MM-DD format)
- Addition of `Last Position Close Date` column (62nd column) - date when the last position was closed (YYYY-MM-DD format)

**Used By:**

- `trades_20250520.csv` and other portfolio files using the extended schema
- All three main modules now fully support this extended schema

**Implementation Details:**

- The system now fully supports the extended schema through dedicated utility modules:
  - `app/tools/portfolio/schema_detection.py`: Detects schema version and normalizes data
  - `app/tools/portfolio/allocation.py`: Handles allocation percentages
  - `app/tools/portfolio/stop_loss.py`: Handles stop loss values

## 3. Synthetic Ticker CSV Schema

A specialized version of the portfolio schema that handles synthetic tickers (pairs of assets).

**Key Fields:**

- Same as Strategy Portfolio schema
- Special handling for tickers with underscores (e.g., "BTC_MSTR")
- Additional fields: `TICKER_1`, `TICKER_2` for the component tickers

**Used By:**

- All three files have code to detect and process synthetic tickers
- Examples: "BTC_MSTR_d_20250409.csv", "STRK_MSTR_H_EMA.csv"

## 4. Scanner List CSV Schema

Used for listing tickers to be analyzed.

**Header Fields:**
Likely a simple list of ticker symbols, similar to the JSON ticker lists but in CSV format.

**Used By:**

- Referenced in `app/ma_cross/1_get_portfolios.py` as "SCANNER_LIST": 'DAILY.csv'

## 5. CSV File Naming Conventions

The CSV files follow specific naming patterns that encode important metadata:

- **Timeframe indicators:**

  - Daily: `*_d_*.csv` or `*_D_*.csv` (e.g., "crypto_d_20250508.csv")
  - Hourly: `*_h_*.csv` or `*_H_*.csv` (e.g., "crypto_h.csv")

- **Date indicators:**

  - Files with dates in format `*_YYYYMMDD.csv` (e.g., "portfolio_d_20250510.csv")

- **Strategy type indicators:**

  - `*_EMA.csv` for Exponential Moving Average strategies
  - `*_SMA.csv` for Simple Moving Average strategies

- **Special purpose indicators:**
  - `DAILY*.csv` for daily timeframe collections
  - `*_best*.csv` for filtered best strategies

## CSV Schema Handling in Code

The three files handle these CSV schemas through several key functions:

1. **In app/concurrency/review.py:**

   - Uses `portfolio_context()` to load portfolio files
   - Handles synthetic tickers via `detect_synthetic_ticker()` and `process_synthetic_ticker()`
   - Configuration option `CSV_USE_HOURLY` controls timeframe for CSV file strategies

2. **In app/ma_cross/1_get_portfolios.py:**

   - Uses `execute_strategy()` to generate strategy results
   - Uses `filter_portfolios()` to filter based on criteria
   - Uses `export_best_portfolios()` to save filtered results
   - Configuration option `USE_HOURLY` controls timeframe

3. **In app/strategies/update_portfolios.py:**
   - Uses `load_portfolio_with_logging()` to load portfolio files
   - Uses `process_ticker_portfolios()` to process each ticker
   - Uses `export_summary_results()` to save results
   - Configuration option `USE_HOURLY` controls timeframe

These CSV schemas form the backbone of the trading system's data flow, storing both configuration parameters and analysis results for various trading strategies across different timeframes and assets.

## Project Structure and CSV File Organization

The trading system organizes CSV files in a structured directory hierarchy:

```
/csv/
  /strategies/           # Raw strategy results (e.g., trades_20250520.csv)
  /portfolios_filtered/  # Filtered strategy results by ticker and strategy type
  /portfolios_best/      # Best performing strategies organized by date
    /YYYYMMDD/           # Date-based subdirectories
  /ma_cross/             # Moving average cross strategy specific results
  /mean_reversion/       # Mean reversion strategy specific results
  /monte_carlo/          # Monte Carlo simulation results
```

## Data Flow and Integration

The CSV files participate in a data flow pipeline:

1. **Strategy Generation** → CSV files in `/strategies/` directory

   - Created by `app/ma_cross/1_get_portfolios.py` and similar strategy generators

2. **Filtering and Analysis** → CSV files in `/portfolios_filtered/` directory

   - Processed by `app/strategies/update_portfolios.py`

3. **Concurrency Analysis** → JSON results in `/json/concurrency/` directory

   - Analyzed by `app/concurrency/review.py`

4. **Portfolio Optimization** → Best portfolios in `/portfolios_best/` directory
   - Final output used for trading decisions

## Key Field Descriptions

Some of the most important fields in the CSV schemas:

| Field                    | Description                                                       |
| ------------------------ | ----------------------------------------------------------------- |
| Ticker                   | Asset symbol (e.g., "BTC-USD", "AAPL")                            |
| Allocation [%]           | Percentage of portfolio allocated to this strategy (0-100%)       |
| Strategy Type            | Trading strategy type (e.g., "SMA", "EMA")                        |
| Short Window             | Short-term moving average period                                  |
| Long Window              | Long-term moving average period                                   |
| Signal Window            | Additional parameter for signal generation                        |
| Stop Loss [%]            | Percentage-based stop loss level (0-100%)                         |
| Last Position Open Date  | Date when the last position was opened (YYYY-MM-DD format)        |
| Last Position Close Date | Date when the last position was closed (YYYY-MM-DD format)        |
| Score                    | Composite performance score                                       |
| Win Rate [%]             | Percentage of winning trades                                      |
| Profit Factor            | Ratio of gross profits to gross losses                            |
| Expectancy per Trade     | Expected profit per trade                                         |
| Sortino Ratio            | Risk-adjusted return metric focusing on downside risk             |
| Beats BNH [%]            | Performance compared to buy-and-hold strategy                     |
| Max Drawdown [%]         | Maximum observed loss from peak to trough                         |
| Stop Level               | Calculated price level for stop loss (derived from Stop Loss [%]) |

## Schema Evolution and Implementation

The trading system's CSV schemas have evolved to support more sophisticated portfolio management:

1. **Completed Implementation**: The system now fully supports the Extended Schema with Allocation [%], Stop Loss [%], Last Position Open Date, and Last Position Close Date columns through dedicated utility modules:

   - `app/tools/portfolio/schema_detection.py`: Automatically detects schema version (Base or Extended)
   - `app/tools/portfolio/allocation.py`: Validates, normalizes, and processes allocation percentages
   - `app/tools/portfolio/stop_loss.py`: Validates, normalizes, and processes stop loss values

2. **Key Functionality**:

   - **Allocation Management**:

     - Validation of allocation values (0-100%)
     - Distribution of allocations to ensure sum equals 100%
     - Position size calculation based on account value

   - **Stop Loss Management**:
     - Validation of stop loss values (0-100%)
     - Calculation of stop loss price levels based on entry prices
     - Application of stop loss rules to trading strategies
     - Support for both candle-close and intracandle stop loss triggers

3. **Backward Compatibility**: The system maintains full backward compatibility with the Base Schema while providing enhanced functionality for the Extended Schema.

4. **Special Cases Handling**:
   - **Case 1**: When Allocation [%] column exists but no values: maintains the column with empty values
   - **Case 2**: When Allocation [%] column doesn't exist: adds it with empty fields
   - **Case 3**: When some rows have Allocation [%] values and others don't: assigns equal values to empty ones
   - **Case 4**: Always exports using the Extended Schema format for consistency

## Common Usage Patterns

Typical workflows involving these CSV files:

1. **Strategy Backtesting**:

   ```
   Generate strategies → Filter by performance metrics → Export best performers
   ```

2. **Portfolio Construction with Allocation and Stop Loss**:

   ```
   Load filtered strategies → Set allocation percentages → Configure stop loss levels → Analyze concurrency → Export portfolio
   ```

3. **Risk Management**:

   ```
   Calculate position sizes based on allocations → Apply stop loss rules → Monitor risk metrics
   ```

4. **Performance Monitoring**:
   ```
   Compare current signals with historical performance → Track metrics over time → Adjust allocations and stop losses
   ```

## Integration with Trading System Modules

The Extended Schema is integrated with the main modules of the trading system:

1. **In app/concurrency/review.py:**

   - Detects schema version automatically
   - Processes allocation data for portfolio-level risk analysis
   - Applies stop loss rules to strategies based on price data
   - Supports both candle-close and intracandle stop loss triggers

2. **In app/ma_cross/1_get_portfolios.py:**

   - Validates and normalizes allocation and stop loss values
   - Calculates stop loss levels based on entry prices
   - Provides summary statistics for allocations and stop losses

3. **In app/strategies/update_portfolios.py:**

   - Preserves allocation and stop loss values during portfolio updates
   - Validates and normalizes stop loss values for each strategy
   - Provides detailed stop loss summary statistics

4. **In app/tools/strategy/export_portfolios.py:**
   - Always exports using the Extended Schema format for consistency
   - Handles special cases for allocation and stop loss values
   - Ensures proper column ordering in exported CSV files
