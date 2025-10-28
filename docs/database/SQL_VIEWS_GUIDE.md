# SQL Views and Queries

This directory contains SQL views and parameterized queries for analyzing trading strategy backtest results.

## Directory Structure

```
sql/
├── views/                              # Database view definitions
│   ├── 01_core_operational_views.sql  # ⭐ PRIORITY: Best results per sweep
│   ├── 02_performance_views.sql       # Performance rankings and analysis
│   ├── 03_sweep_analysis_views.sql    # Sweep run comparisons
│   ├── 04_trade_efficiency_views.sql  # Trade frequency and efficiency
│   └── 05_metric_analysis_views.sql   # Metric type analysis
│
├── queries/                            # Parameterized SQL queries
│   ├── analysis/                       # Analysis queries
│   │   ├── best_for_sweep_and_ticker.sql  # ⭐ Most common query
│   │   ├── best_overall_for_sweep.sql
│   │   ├── top_n_by_metric.sql
│   │   ├── parameter_heatmap_data.sql
│   │   └── risk_reward_scatter.sql
│   ├── comparison/                     # Comparison queries
│   │   └── ticker_comparison.sql
│   ├── optimization/                   # Optimization queries
│   │   ├── optimal_parameters_by_ticker.sql
│   │   └── robust_strategies.sql
│   └── reports/                        # Report queries
│       └── executive_summary.sql
│
└── README.md                           # This file
```

## Core Operational Views

These views answer the most common questions:

### `v_best_by_sweep_and_ticker`⭐ MOST IMPORTANT

**Purpose:** Find the best result for each ticker within each sweep run.

**Query Example:**

```sql
SELECT * FROM v_best_by_sweep_and_ticker
WHERE sweep_run_id = 'your-sweep-run-uuid'
  AND ticker = 'AAPL';
```

### `v_best_results_per_sweep` ⭐ HIGH PRIORITY

**Purpose:** Overall best result and summary stats for each sweep run.

**Query Example:**

```sql
SELECT * FROM v_best_results_per_sweep
ORDER BY run_date DESC
LIMIT 1;  -- Latest sweep
```

### `v_latest_best_results` ⭐ HIGH PRIORITY

**Purpose:** All results from the most recent sweep run with rankings.

**Query Example:**

```sql
SELECT * FROM v_latest_best_results
WHERE rank_for_ticker = 1  -- Best per ticker
ORDER BY score DESC;
```

## Performance Views

### `v_top_performers_by_ticker`

Top 20 performing strategies for each ticker across all sweep runs.

### `v_risk_adjusted_rankings`

Strategies ranked by composite risk-adjusted performance (Sharpe, Sortino, Calmar, Drawdown, Score).

### `v_parameter_performance_summary`

Aggregated performance statistics for each parameter combination across all tickers.

### `v_consistency_analysis`

Strategies ranked by performance consistency across multiple tickers.

## Sweep Analysis Views

### `v_sweep_run_summary`

Comprehensive summary statistics for each sweep run including best performer and distribution metrics.

### `v_sweep_comparison`

Compare sweep runs over time showing score changes and trends.

### `v_parameter_evolution`

Track how optimal parameter values change across successive sweep runs.

### `v_sweep_coverage`

Analyze parameter space coverage and test distribution for each sweep run.

## Trade Efficiency Views

### `v_trade_efficiency_analysis`

Analyze trading efficiency metrics including trades per month, score per trade, frequency categorization.

### `v_win_rate_analysis`

Detailed win rate analysis with categorization, win/loss ratios, and trade quality metrics.

### `v_trade_duration_analysis`

Analyze trade holding periods and their relationship to performance metrics.

### `v_expectancy_analysis`

Deep analysis of expectancy metrics including per-trade, per-month, and annualized expectations.

## Metric Analysis Views

### `v_strategies_by_metric_type`

Strategies grouped by their assigned metric type classifications.

### `v_metric_type_summary`

Summary statistics showing how many strategies have been assigned each metric type.

### `v_metric_leaders_by_category`

The single best performing strategy for each metric type classification.

## Common Usage Patterns

### Find Best Strategy for a Specific Sweep and Ticker

```sql
-- Use the dedicated query file
\i sql/queries/analysis/best_for_sweep_and_ticker.sql

-- Or use the view directly
SELECT * FROM v_best_by_sweep_and_ticker
WHERE sweep_run_id = 'your-uuid'
  AND ticker = 'AAPL';
```

### Get Latest Sweep Results

```sql
SELECT * FROM v_latest_best_results
ORDER BY score DESC
LIMIT 10;
```

### Compare All Tickers

```sql
\i sql/queries/comparison/ticker_comparison.sql
```

### Find Robust Strategies

```sql
\i sql/queries/optimization/robust_strategies.sql
```

### Generate Heatmap Data

```sql
\i sql/queries/analysis/parameter_heatmap_data.sql
```

## Running Queries

### Using psql

```bash
# Connect to database
psql postgresql://trading_user:trading_password@localhost:5432/trading_db

# Run a query file
\i sql/queries/analysis/best_for_sweep_and_ticker.sql

# Or query views directly
SELECT * FROM v_best_by_sweep_and_ticker LIMIT 10;
```

### Using Python

```python
import asyncpg

async def get_best_for_sweep(sweep_run_id: str, ticker: str):
    conn = await asyncpg.connect('postgresql://trading_user:...')
    result = await conn.fetchrow("""
        SELECT * FROM v_best_by_sweep_and_ticker
        WHERE sweep_run_id = $1 AND ticker = $2
    """, sweep_run_id, ticker)
    await conn.close()
    return result
```

## View Dependencies

Views are created in order:

1. Core Operational Views (depend only on base tables)
2. Performance Views (depend only on base tables)
3. Sweep Analysis Views (depend only on base tables)
4. Trade Efficiency Views (depend only on base tables)
5. Metric Analysis Views (depend on junction tables)

## Maintenance

### Recreating Views

If schema changes require view updates:

```bash
# Drop all views
psql -d trading_db -c "DROP VIEW IF EXISTS v_best_by_sweep_and_ticker CASCADE;"
# ... drop others ...

# Recreate from migration
alembic upgrade head
```

### Performance Optimization

For large datasets, consider:

- Creating materialized views for expensive queries
- Adding indexes on frequently filtered columns
- Using partitioning for the results table by sweep_run_id

## Notes

- All views include proper JOINs to `tickers` and `strategy_types` for denormalization
- Column names follow the convention from `strategy_sweep_results` table
- UUID parameters should be passed as strings in PostgreSQL
- Percentile calculations use `PERCENTILE_CONT` for continuous distributions
