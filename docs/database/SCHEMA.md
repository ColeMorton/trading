# Strategy Sweep Results Database Schema

This document describes the PostgreSQL database schema for storing strategy sweep results.

## Overview

The strategy sweep database consists of seven related tables:

### Core Tables

1. **`strategy_sweep_results`**: Stores comprehensive backtest results from parameter sweep analyses. Each row represents one strategy configuration tested during a sweep, with all performance metrics from the Extended Portfolio Schema.

2. **`tickers`**: Reference table for ticker symbols (Migration 004).

### Metric Classification Tables (Migration 003)

3. **`metric_types`**: Reference table containing standard metric type classifications (e.g., "Most Sharpe Ratio", "Median Total Return [%]").

4. **`strategy_sweep_result_metrics`**: Junction table creating a many-to-many relationship between sweep results and metric types.

### Best Selection Tables (Migration 005)

5. **`selection_algorithms`**: Reference table defining algorithms used to determine "best" portfolios with confidence ranges.

6. **`sweep_best_selections`**: Tracks which result is the "best" for each sweep_run + ticker + strategy combination, with selection metadata and confidence scores.

### Relationships

```
tickers ←──┐
           │
           ├─→ strategy_sweep_results ←──┬─→ strategy_sweep_result_metrics ─→ metric_types
           │                             │
           └─→ sweep_best_selections ────┘
```

## Table: `metric_types` (NEW in Migration 003)

Reference table for metric type classifications.

| Column        | Type         | Description                                                |
| ------------- | ------------ | ---------------------------------------------------------- |
| `id`          | SERIAL       | Primary key, auto-incremented                              |
| `name`        | VARCHAR(100) | Unique metric type name (e.g., "Most Sharpe Ratio")        |
| `category`    | VARCHAR(50)  | Category grouping (risk, return, trade, timing, composite) |
| `description` | TEXT         | Human-readable description of the metric type              |
| `created_at`  | TIMESTAMP    | When the record was created                                |

**Indexes:**

- `ix_metric_types_name` - Fast lookups by name
- `ix_metric_types_category` - Filter by category

**Pre-populated Data:**
The table is seeded with ~90 standard metric classifications including:

- Return Metrics: Most/Median/Mean Total Return [%], Annualized Return
- Risk Metrics: Most/Median/Mean Sharpe Ratio, Sortino Ratio, Calmar Ratio, Omega Ratio
- Trade Statistics: Most/Median/Mean Total Trades, Win Rate [%], Profit Factor
- Timing Metrics: Trades Per Day/Month, Signals Per Month, Trade Duration metrics
- And many more...

## Table: `strategy_sweep_result_metrics` (NEW in Migration 003)

Junction table linking sweep results to their metric type classifications.

| Column            | Type      | Description                                               |
| ----------------- | --------- | --------------------------------------------------------- |
| `id`              | SERIAL    | Primary key, auto-incremented                             |
| `sweep_result_id` | UUID      | Foreign key to strategy_sweep_results.id (CASCADE delete) |
| `metric_type_id`  | INTEGER   | Foreign key to metric_types.id                            |
| `created_at`      | TIMESTAMP | When the association was created                          |

**Constraints:**

- `uq_sweep_result_metric` - UNIQUE(sweep_result_id, metric_type_id) prevents duplicates

**Indexes:**

- `ix_sweep_result_metrics_result` - Fast lookups by result
- `ix_sweep_result_metrics_type` - Fast lookups by metric type

## Table: `selection_algorithms` (NEW in Migration 005)

Reference table for selection algorithm definitions.

| Column           | Type         | Description                                     |
| ---------------- | ------------ | ----------------------------------------------- |
| `id`             | SERIAL       | Primary key, auto-incremented                   |
| `algorithm_code` | VARCHAR(50)  | Unique algorithm code (e.g., "top_3_all_match") |
| `algorithm_name` | VARCHAR(100) | Human-readable algorithm name                   |
| `description`    | TEXT         | Description of the algorithm                    |
| `min_confidence` | NUMERIC(5,2) | Minimum confidence score (0-100)                |
| `max_confidence` | NUMERIC(5,2) | Maximum confidence score (0-100)                |

**Indexes:**

- `ix_selection_algorithms_code` - Fast lookups by code

**Pre-populated Data:**
The table is seeded with 5 standard selection algorithms:

- `top_3_all_match`: All top 3 results have same parameters (100% confidence)
- `top_5_3_of_5`: 3 out of top 5 match (60-80% confidence)
- `top_8_5_of_8`: 5 out of top 8 match (62.5-75% confidence)
- `top_2_both_match`: Both top 2 match (100% confidence)
- `highest_score_fallback`: No pattern, highest score wins (0-50% confidence)

## Table: `sweep_best_selections` (NEW in Migration 005)

Tracks the "best" portfolio selection for each sweep_run + ticker + strategy combination.

| Column                    | Type          | Description                                               |
| ------------------------- | ------------- | --------------------------------------------------------- |
| `id`                      | SERIAL        | Primary key, auto-incremented                             |
| `sweep_run_id`            | UUID          | Foreign key to sweep run                                  |
| `ticker_id`               | INTEGER       | Foreign key to tickers.id                                 |
| `strategy_type`           | VARCHAR(50)   | Strategy type (SMA, EMA, MACD, ATR)                       |
| `best_result_id`          | UUID          | Foreign key to strategy_sweep_results.id (CASCADE delete) |
| `selection_algorithm`     | VARCHAR(50)   | Algorithm used for selection                              |
| `selection_criteria`      | VARCHAR(100)  | Specific criteria matched (e.g., "top_3_all_match")       |
| `confidence_score`        | NUMERIC(5,2)  | Confidence in selection (0-100)                           |
| `alternatives_considered` | INTEGER       | Number of alternatives analyzed                           |
| `winning_fast_period`     | INTEGER       | Fast period of selected result                            |
| `winning_slow_period`     | INTEGER       | Slow period of selected result                            |
| `winning_signal_period`   | INTEGER       | Signal period (for MACD)                                  |
| `result_score`            | NUMERIC(20,8) | Snapshot of result score                                  |
| `result_sharpe_ratio`     | NUMERIC(20,8) | Snapshot of Sharpe ratio                                  |
| `result_total_return_pct` | NUMERIC(10,4) | Snapshot of total return %                                |
| `result_win_rate_pct`     | NUMERIC(10,4) | Snapshot of win rate %                                    |
| `created_at`              | TIMESTAMP     | When selection was computed                               |

**Constraints:**

- `uq_best_selection_per_sweep_ticker_strategy` - UNIQUE(sweep_run_id, ticker_id, strategy_type)

**Indexes:**

- `ix_sweep_best_selections_sweep_run_id` - Filter by sweep run
- `ix_sweep_best_selections_best_result_id` - Link to result
- `ix_sweep_best_selections_ticker_id` - Filter by ticker
- `idx_best_selections_composite` - Composite index for fast lookups

## Table: `strategy_sweep_results`

### Primary Key and Metadata

| Column         | Type      | Description                                             |
| -------------- | --------- | ------------------------------------------------------- |
| `id`           | UUID      | Primary key, auto-generated                             |
| `sweep_run_id` | UUID      | Groups all results from the same sweep execution        |
| `created_at`   | TIMESTAMP | When the record was created                             |
| `sweep_config` | JSONB     | Full sweep configuration (tickers, parameters, filters) |

### Core Strategy Parameters

| Column          | Type        | Description                            |
| --------------- | ----------- | -------------------------------------- |
| `ticker`        | VARCHAR(50) | Asset symbol (e.g., "AAPL", "BTC-USD") |
| `strategy_type` | VARCHAR(50) | Strategy type (SMA, EMA, MACD, ATR)    |
| `fast_period`   | INTEGER     | Fast moving average period             |
| `slow_period`   | INTEGER     | Slow moving average period             |
| `signal_period` | INTEGER     | Signal period (MACD only)              |

### Signal Information

| Column               | Type        | Description        |
| -------------------- | ----------- | ------------------ |
| `signal_entry`       | VARCHAR(50) | Entry signal type  |
| `signal_exit`        | VARCHAR(50) | Exit signal type   |
| `signal_unconfirmed` | VARCHAR(50) | Unconfirmed signal |

### Trade Statistics

| Column              | Type          | Description                 |
| ------------------- | ------------- | --------------------------- |
| `total_open_trades` | INTEGER       | Currently open positions    |
| `total_trades`      | INTEGER       | Total trades executed       |
| `score`             | NUMERIC(20,8) | Composite performance score |

### Performance Metrics

| Column                 | Type          | Description                                   |
| ---------------------- | ------------- | --------------------------------------------- |
| `win_rate_pct`         | NUMERIC(10,4) | Percentage of profitable trades               |
| `profit_factor`        | NUMERIC(20,8) | Ratio of gross profit to gross loss           |
| `expectancy_per_trade` | NUMERIC(20,8) | Expected profit per trade                     |
| `sortino_ratio`        | NUMERIC(20,8) | Risk-adjusted return using downside deviation |
| `beats_bnh_pct`        | NUMERIC(10,4) | Performance vs buy-and-hold                   |

### Timing Metrics

| Column                 | Type          | Description                                     |
| ---------------------- | ------------- | ----------------------------------------------- |
| `avg_trade_duration`   | VARCHAR(50)   | Average holding period (e.g., "5 days 3:30:00") |
| `trades_per_day`       | NUMERIC(20,8) | Average trades per trading day                  |
| `trades_per_month`     | NUMERIC(20,8) | Average trades per month                        |
| `signals_per_month`    | NUMERIC(20,8) | Average signals per month                       |
| `expectancy_per_month` | NUMERIC(20,8) | Expected profit per month                       |

### Portfolio Values

| Column                   | Type          | Description                 |
| ------------------------ | ------------- | --------------------------- |
| `start_value`            | NUMERIC(20,2) | Initial portfolio value     |
| `end_value`              | NUMERIC(20,2) | Final portfolio value       |
| `total_return_pct`       | NUMERIC(10,4) | Total return percentage     |
| `benchmark_return_pct`   | NUMERIC(10,4) | Benchmark comparison return |
| `max_gross_exposure_pct` | NUMERIC(10,4) | Maximum gross exposure      |

### Risk Metrics

| Column                  | Type          | Description                      |
| ----------------------- | ------------- | -------------------------------- |
| `max_drawdown_pct`      | NUMERIC(10,4) | Maximum drawdown percentage      |
| `sharpe_ratio`          | NUMERIC(20,8) | Risk-adjusted return ratio       |
| `calmar_ratio`          | NUMERIC(20,8) | Return to maximum drawdown ratio |
| `skew`                  | NUMERIC(20,8) | Distribution skewness of returns |
| `kurtosis`              | NUMERIC(20,8) | Distribution kurtosis of returns |
| `value_at_risk`         | NUMERIC(20,8) | Value at Risk (VaR) measure      |
| `annualized_volatility` | NUMERIC(20,8) | Annualized volatility measure    |

### Trade Analysis

| Column                  | Type          | Description                      |
| ----------------------- | ------------- | -------------------------------- |
| `best_trade_pct`        | NUMERIC(10,4) | Largest winning trade percentage |
| `worst_trade_pct`       | NUMERIC(10,4) | Largest losing trade percentage  |
| `avg_winning_trade_pct` | NUMERIC(10,4) | Average winning trade percentage |
| `avg_losing_trade_pct`  | NUMERIC(10,4) | Average losing trade percentage  |

### Extended Schema Fields

| Column                     | Type          | Description                     |
| -------------------------- | ------------- | ------------------------------- |
| `allocation_pct`           | NUMERIC(10,4) | Portfolio allocation percentage |
| `stop_loss_pct`            | NUMERIC(10,4) | Stop loss threshold percentage  |
| `last_position_open_date`  | VARCHAR(50)   | Last position open date         |
| `last_position_close_date` | VARCHAR(50)   | Last position close date        |

## Indexes

The table includes the following indexes for efficient querying:

- `ix_strategy_sweep_sweep_run_id` - Group all results from same sweep
- `ix_strategy_sweep_ticker` - Filter by ticker symbol
- `ix_strategy_sweep_created_at` - Time-based queries
- `ix_strategy_sweep_ticker_strategy` - Composite index for ticker+strategy queries

## Usage

### Running Strategy Sweep with Database Persistence

```bash
# Basic sweep with database persistence
trading-cli strategy sweep --ticker AAPL --database

# Multi-ticker sweep with DB persistence
trading-cli strategy sweep --ticker AAPL,MSFT,GOOGL --strategy SMA EMA --database

# Using short flag
trading-cli strategy sweep --ticker BTC-USD --db
```

### Query Examples

#### Get all results from a specific sweep run

```sql
SELECT
    ticker,
    strategy_type,
    fast_period,
    slow_period,
    total_trades,
    win_rate_pct,
    total_return_pct,
    max_drawdown_pct,
    sharpe_ratio
FROM strategy_sweep_results
WHERE sweep_run_id = 'your-sweep-run-id-here'
ORDER BY score DESC;
```

#### Find best performing strategies per ticker

```sql
WITH ranked_strategies AS (
    SELECT
        ticker,
        strategy_type,
        fast_period,
        slow_period,
        score,
        win_rate_pct,
        total_return_pct,
        max_drawdown_pct,
        ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY score DESC) as rank
    FROM strategy_sweep_results
    WHERE sweep_run_id = 'your-sweep-run-id-here'
)
SELECT *
FROM ranked_strategies
WHERE rank = 1;
```

#### Compare strategy performance across tickers

```sql
SELECT
    ticker,
    strategy_type,
    COUNT(*) as configurations_tested,
    AVG(win_rate_pct) as avg_win_rate,
    AVG(total_return_pct) as avg_return,
    MAX(score) as best_score,
    MIN(max_drawdown_pct) as min_drawdown
FROM strategy_sweep_results
WHERE sweep_run_id = 'your-sweep-run-id-here'
GROUP BY ticker, strategy_type
ORDER BY best_score DESC;
```

#### Find recent sweep runs

```sql
SELECT
    sweep_run_id,
    MIN(created_at) as sweep_start,
    COUNT(*) as result_count,
    COUNT(DISTINCT ticker) as ticker_count,
    COUNT(DISTINCT strategy_type) as strategy_count,
    sweep_config->>'tickers' as tickers
FROM strategy_sweep_results
GROUP BY sweep_run_id, sweep_config
ORDER BY sweep_start DESC
LIMIT 10;
```

#### Analyze parameter sensitivity

```sql
SELECT
    ticker,
    fast_period,
    slow_period,
    AVG(total_return_pct) as avg_return,
    AVG(sharpe_ratio) as avg_sharpe,
    COUNT(*) as sample_size
FROM strategy_sweep_results
WHERE
    sweep_run_id = 'your-sweep-run-id-here'
    AND strategy_type = 'SMA'
    AND total_trades >= 20
GROUP BY ticker, fast_period, slow_period
HAVING COUNT(*) > 0
ORDER BY avg_sharpe DESC;
```

### Query Examples with Metric Types (NEW)

#### Get all available metric types

```sql
SELECT id, name, category, description
FROM metric_types
ORDER BY category, name;
```

#### Find all results classified as "Most Sharpe Ratio"

```sql
SELECT
    sr.ticker,
    sr.strategy_type,
    sr.fast_period,
    sr.slow_period,
    sr.score,
    sr.sharpe_ratio,
    sr.total_return_pct,
    mt.name as metric_classification
FROM strategy_sweep_results sr
JOIN strategy_sweep_result_metrics srm ON sr.id = srm.sweep_result_id
JOIN metric_types mt ON srm.metric_type_id = mt.id
WHERE mt.name = 'Most Sharpe Ratio'
  AND sr.sweep_run_id = 'your-sweep-run-id'
ORDER BY sr.score DESC;
```

#### Get sweep results with all their metric types (aggregated)

```sql
SELECT
    sr.id,
    sr.ticker,
    sr.strategy_type,
    sr.fast_period,
    sr.slow_period,
    sr.score,
    sr.sharpe_ratio,
    sr.total_return_pct,
    STRING_AGG(mt.name, ', ' ORDER BY mt.name) as metric_types,
    COUNT(mt.id) as metric_count
FROM strategy_sweep_results sr
LEFT JOIN strategy_sweep_result_metrics srm ON sr.id = srm.sweep_result_id
LEFT JOIN metric_types mt ON srm.metric_type_id = mt.id
WHERE sr.sweep_run_id = 'your-sweep-run-id'
GROUP BY sr.id
ORDER BY sr.score DESC;
```

#### Find results with multiple metric classifications

```sql
SELECT
    sr.ticker,
    sr.strategy_type,
    sr.score,
    STRING_AGG(mt.name, ', ' ORDER BY mt.name) as classifications,
    COUNT(mt.id) as classification_count
FROM strategy_sweep_results sr
JOIN strategy_sweep_result_metrics srm ON sr.id = srm.sweep_result_id
JOIN metric_types mt ON srm.metric_type_id = mt.id
WHERE sr.sweep_run_id = 'your-sweep-run-id'
GROUP BY sr.id, sr.ticker, sr.strategy_type, sr.score
HAVING COUNT(mt.id) > 1
ORDER BY classification_count DESC, sr.score DESC;
```

#### Find most common metric type classifications

```sql
SELECT
    mt.name,
    mt.category,
    COUNT(srm.id) as usage_count,
    COUNT(DISTINCT sr.ticker) as unique_tickers,
    AVG(sr.score) as avg_score
FROM metric_types mt
JOIN strategy_sweep_result_metrics srm ON mt.id = srm.metric_type_id
JOIN strategy_sweep_results sr ON srm.sweep_result_id = sr.id
GROUP BY mt.id, mt.name, mt.category
ORDER BY usage_count DESC
LIMIT 20;
```

#### Find top performers across multiple metrics

```sql
-- Results classified with 3+ metric types indicate multi-metric excellence
SELECT
    sr.ticker,
    sr.strategy_type,
    sr.fast_period,
    sr.slow_period,
    sr.score,
    sr.sharpe_ratio,
    sr.total_return_pct,
    sr.win_rate_pct,
    COUNT(mt.id) as metric_count,
    STRING_AGG(mt.name, ', ' ORDER BY mt.name) as classifications
FROM strategy_sweep_results sr
JOIN strategy_sweep_result_metrics srm ON sr.id = srm.sweep_result_id
JOIN metric_types mt ON srm.metric_type_id = mt.id
WHERE sr.sweep_run_id = 'your-sweep-run-id'
GROUP BY sr.id
HAVING COUNT(mt.id) >= 3
ORDER BY metric_count DESC, sr.score DESC;
```

#### Analyze metric type distribution by category

```sql
SELECT
    mt.category,
    COUNT(DISTINCT mt.id) as unique_metrics,
    COUNT(srm.id) as total_assignments,
    ROUND(COUNT(srm.id)::numeric / NULLIF(COUNT(DISTINCT mt.id), 0), 2) as avg_usage_per_metric
FROM metric_types mt
LEFT JOIN strategy_sweep_result_metrics srm ON mt.id = srm.metric_type_id
GROUP BY mt.category
ORDER BY total_assignments DESC;
```

### Query Examples with Best Selections (NEW in Migration 005)

#### Get all best selections for a sweep

```sql
SELECT
    t.ticker,
    bs.strategy_type,
    bs.selection_criteria,
    bs.confidence_score,
    bs.winning_fast_period,
    bs.winning_slow_period,
    sr.score as current_score,
    sr.sharpe_ratio,
    sr.total_return_pct,
    STRING_AGG(mt.name, ', ' ORDER BY mt.name) as metric_types
FROM sweep_best_selections bs
JOIN tickers t ON bs.ticker_id = t.id
JOIN strategy_sweep_results sr ON bs.best_result_id = sr.id
LEFT JOIN strategy_sweep_result_metrics srm ON sr.id = srm.sweep_result_id
LEFT JOIN metric_types mt ON srm.metric_type_id = mt.id
WHERE bs.sweep_run_id = 'your-sweep-run-id'
GROUP BY bs.id, t.ticker, bs.strategy_type, bs.selection_criteria,
         bs.confidence_score, bs.winning_fast_period, bs.winning_slow_period,
         sr.score, sr.sharpe_ratio, sr.total_return_pct
ORDER BY bs.confidence_score DESC, sr.score DESC;
```

#### Compare best vs all results with indicator

```sql
SELECT
    t.ticker,
    sr.strategy_type,
    sr.fast_period,
    sr.slow_period,
    sr.score,
    sr.sharpe_ratio,
    sr.total_return_pct,
    CASE
        WHEN bs.best_result_id IS NOT NULL THEN '⭐ BEST'
        ELSE ''
    END as best_indicator,
    bs.selection_criteria,
    bs.confidence_score
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
LEFT JOIN sweep_best_selections bs
    ON sr.id = bs.best_result_id
    AND sr.sweep_run_id = bs.sweep_run_id
WHERE sr.sweep_run_id = 'your-sweep-run-id'
ORDER BY t.ticker, sr.strategy_type, sr.score DESC;
```

#### Get best result for specific ticker and strategy

```sql
SELECT
    t.ticker,
    bs.strategy_type,
    bs.winning_fast_period,
    bs.winning_slow_period,
    bs.selection_criteria,
    bs.confidence_score,
    sr.*
FROM sweep_best_selections bs
JOIN tickers t ON bs.ticker_id = t.id
JOIN strategy_sweep_results sr ON bs.best_result_id = sr.id
WHERE bs.sweep_run_id = 'your-sweep-run-id'
  AND t.ticker = 'BTC-USD'
  AND bs.strategy_type = 'SMA';
```

#### Analyze selection algorithm effectiveness

```sql
-- See which algorithms are most commonly used
SELECT
    bs.selection_criteria,
    COUNT(*) as usage_count,
    AVG(bs.confidence_score) as avg_confidence,
    AVG(bs.result_score) as avg_result_score,
    AVG(bs.alternatives_considered) as avg_alternatives
FROM sweep_best_selections bs
GROUP BY bs.selection_criteria
ORDER BY usage_count DESC;
```

#### Find high-confidence best selections

```sql
-- Get best selections with 100% confidence (perfect parameter match)
SELECT
    t.ticker,
    bs.strategy_type,
    bs.selection_criteria,
    bs.winning_fast_period,
    bs.winning_slow_period,
    bs.result_score,
    bs.result_sharpe_ratio,
    bs.result_total_return_pct
FROM sweep_best_selections bs
JOIN tickers t ON bs.ticker_id = t.id
WHERE bs.confidence_score = 100.00
  AND bs.sweep_run_id = 'your-sweep-run-id'
ORDER BY bs.result_score DESC;
```

#### Track best selections over time for a ticker

```sql
-- See how "best" selections evolved across multiple sweeps
SELECT
    bs.sweep_run_id,
    bs.created_at,
    bs.winning_fast_period,
    bs.winning_slow_period,
    bs.selection_criteria,
    bs.confidence_score,
    bs.result_score
FROM sweep_best_selections bs
JOIN tickers t ON bs.ticker_id = t.id
WHERE t.ticker = 'BTC-USD'
  AND bs.strategy_type = 'SMA'
ORDER BY bs.created_at DESC
LIMIT 10;
```

## Performance Considerations

### Batch Inserts

The repository uses batch inserts (100 records per batch) to optimize database performance when saving large sweep results.

### Index Usage

The composite index on `(ticker, strategy_type)` enables efficient filtering for specific ticker-strategy combinations, which is the most common query pattern.

### JSONB Configuration Storage

The `sweep_config` column uses PostgreSQL's JSONB type for flexible storage of sweep parameters. This enables:

- Efficient storage without schema changes
- Query capabilities using JSONB operators
- Full reproducibility of sweep runs

### Data Retention

Consider implementing a data retention policy for old sweep results:

```sql
-- Delete sweep results older than 90 days
DELETE FROM strategy_sweep_results
WHERE created_at < NOW() - INTERVAL '90 days';
```

## Migration

To apply the schema:

```bash
# Run Alembic migration
alembic upgrade head

# To rollback
alembic downgrade -1
```

## Troubleshooting

### Database Connection Issues

If database persistence fails, the system will gracefully degrade and continue saving results to CSV files. Check:

1. PostgreSQL service is running
2. Database connection settings in `.env`
3. Database user has INSERT permissions

### Performance Issues

For large sweeps (1000+ results):

1. Batch size is optimized at 100 records
2. Consider running sweeps during off-peak hours
3. Monitor transaction log size and checkpoint frequency

## Integration with CSV Exports

Database persistence is **complementary** to CSV exports:

- **CSV files**: Complete portfolio details, equity curves, signal history
- **Database**: Structured querying, analysis, historical comparison

Both are created when using the `--database` flag. CSV files remain the primary source of truth for detailed analysis.
