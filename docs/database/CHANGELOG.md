# Database Changelog

Detailed chronological history of all database schema changes and migrations.

## Current State (Migration 007)

**Date**: 2025-10-19  
**Revision**: 007 (head)  
**Total Tables**: 10  
**Total Views**: 19  
**Total Records**: 4,855 sweep results  

---

## Migration 007: Database Views (2025-10-19)

### Purpose
Create analytical views for efficient querying of strategy sweep results.

### Changes
Created 19 database views across 5 categories:

**Core Operational Views (4):**
- `v_best_by_sweep_and_ticker` - Best result per ticker per sweep
- `v_best_results_per_sweep` - Overall best + summary per sweep
- `v_latest_best_results` - Latest sweep results with rankings
- `v_top_10_overall` - Top 10 all-time best results

**Performance Views (4):**
- `v_top_performers_by_ticker` - Top 20 per ticker across all sweeps
- `v_risk_adjusted_rankings` - Composite risk-adjusted performance
- `v_parameter_performance_summary` - Stats by parameter combination
- `v_consistency_analysis` - Performance consistency across tickers

**Sweep Analysis Views (4):**
- `v_sweep_run_summary` - Comprehensive sweep statistics
- `v_sweep_comparison` - Compare sweeps over time
- `v_parameter_evolution` - Track optimal parameter changes
- `v_sweep_coverage` - Parameter space coverage analysis

**Trade Efficiency Views (4):**
- `v_trade_efficiency_analysis` - Frequency vs performance
- `v_win_rate_analysis` - Win rate categorization and analysis
- `v_trade_duration_analysis` - Holding period relationships
- `v_expectancy_analysis` - Expectancy metrics deep dive

**Metric Analysis Views (3):**
- `v_strategies_by_metric_type` - Strategies grouped by classifications
- `v_metric_type_summary` - Metric type assignment statistics
- `v_metric_leaders_by_category` - Best strategy per metric type

### Impact
- Query performance: Sub-100ms for most views
- Simplified complex queries
- Foundation for API endpoints

### Files
- SQL: `sql/views/*.sql`
- Migration: `app/database/migrations/versions/007_create_views.py`

---

## Migration 006: Strategy Types Normalization (2025-10-19)

### Purpose
Normalize `strategy_type` field by creating a reference table.

### Changes
1. **Created `strategy_types` table**:
   - `id` (PK), `strategy_type` (unique), `description`, `created_at`
   - 1 strategy type migrated: SMA

2. **Updated `strategy_sweep_results` table**:
   - Replaced `strategy_type` VARCHAR column with `strategy_type_id` FK
   - Added foreign key constraint (CASCADE delete)
   - Updated composite index: `ix_strategy_sweep_ticker_id_strategy_type_id`

3. **Updated `sweep_best_selections` table**:
   - Replaced `strategy_type` VARCHAR column with `strategy_type_id` FK
   - Added foreign key constraint (CASCADE delete)
   - Updated unique constraint: `uq_best_selection_per_sweep_ticker_strategy_type_id`
   - Updated composite index: `idx_best_selections_composite`

### Data Migration
- **Records Migrated**: 4,855 in `strategy_sweep_results`
- **Records Migrated**: 0 in `sweep_best_selections` (new table)
- **Strategy Types**: 1 unique type extracted and normalized
- **Result**: 100% success, no data loss

### Impact
- Referential integrity for strategy types
- Easier to add new strategy types
- Consistent strategy type values
- Backward compatibility via property decorators

### Files
- Migration: `app/database/migrations/versions/006_create_strategy_types_table.py`
- Models: `app/database/models.py` (added StrategyType model)
- Repository: `app/database/strategy_sweep_repository.py` (updated queries)

---

## Migration 005: Best Selections Tracking (2025-10-19)

### Purpose
Track the "best" portfolio selection for each sweep run + ticker + strategy combination.

### Changes
1. **Created `selection_algorithms` table**:
   - Reference table for selection algorithms
   - 5 pre-populated algorithms: parameter_consistency, highest_score, highest_sharpe, etc.
   - Confidence score ranges and descriptions

2. **Created `sweep_best_selections` table**:
   - Primary identifiers: `sweep_run_id`, `ticker_id`, `strategy_type` (composite unique)
   - Selection metadata: algorithm, criteria, confidence score
   - Winning parameters: fast_period, slow_period, signal_period (denormalized)
   - Result snapshot: score, sharpe_ratio, total_return_pct, win_rate_pct
   - Foreign key to `strategy_sweep_results.id` (CASCADE delete)
   - Composite index for fast lookups

### Features
- Parameter consistency algorithm (default)
- Confidence scoring (0-100%)
- Alternatives tracking
- Result snapshot at selection time
- Audit trail with timestamps

### Impact
- Enables systematic best portfolio selection
- Tracks decision-making metadata
- Supports multiple selection algorithms
- Foundation for automated portfolio optimization

### Files
- Migration: `app/database/migrations/versions/005_create_best_selections_table.py`
- Models: `app/database/models.py` (added SweepBestSelection model)
- Repository: `app/database/strategy_sweep_repository.py` (added selection methods)

---

## Migration 004: Tickers Normalization (2025-10-19)

### Purpose
Normalize ticker symbols by creating a dedicated reference table.

### Changes
1. **Created `tickers` table**:
   - `id` (PK), `ticker` (unique), `created_at`
   - 6 tickers migrated from `strategy_sweep_results`

2. **Updated `strategy_sweep_results` table**:
   - Replaced `ticker` VARCHAR(50) column with `ticker_id` INTEGER FK
   - Added foreign key constraint: `fk_strategy_sweep_results_ticker_id`
   - ON DELETE CASCADE behavior
   - Updated indexes: `ix_strategy_sweep_ticker_id_strategy`

### Data Migration
- **Unique Tickers Extracted**: 6 (AAPL, AMD, BKNG, MSFT, NVDA, TSLA)
- **Records Updated**: 4,855
- **Result**: 100% success, no data loss

### Impact
- Data normalization (ticker stored once)
- Referential integrity enforced
- Query efficiency improved
- Foundation for ticker metadata (future)

### Files
- Migration: `app/database/migrations/versions/004_create_tickers_table.py`
- Models: `app/database/models.py` (added Ticker model)
- Repository: `app/database/strategy_sweep_repository.py` (updated insert/query methods)

---

## Migration 003: Metric Types Classification (2025-10-19)

### Purpose
Replace comma-separated `metric_type` string with normalized many-to-many relationship.

### Changes
1. **Created `metric_types` table**:
   - 86 pre-populated metric classifications
   - 5 categories: return (11), risk (33), trade (20), timing (19), composite (3)
   - Examples: "Most Sharpe Ratio", "Median Win Rate [%]", etc.

2. **Created `strategy_sweep_result_metrics` junction table**:
   - Many-to-many relationship between results and metric types
   - Unique constraint: `uq_sweep_result_metric`
   - Foreign keys with CASCADE delete

3. **Updated `strategy_sweep_results` table**:
   - Added `metric_type` VARCHAR(500) column for backward compatibility
   - Preserved existing string-based classifications

### Features
- Parse comma-separated metric strings
- Assign multiple classifications to single result
- Query results by metric type
- Group by category

### Impact
- Queryable metric classifications
- Supports multiple metrics per result
- Enables advanced filtering
- Foundation for metric-based analytics

### Files
- Migration: `app/database/migrations/versions/003_create_metric_types_table.py`
- Models: `app/database/models.py` (added MetricType, StrategySweepResultMetric)
- Repository: `app/database/strategy_sweep_repository.py` (added metric methods)

---

## Migration 002: Strategy Sweep Results (2025-10-19)

### Purpose
Create main table for storing comprehensive strategy backtest results.

### Changes
Created `strategy_sweep_results` table with:
- **67 total columns**: All Extended Portfolio Schema fields + metadata
- **Primary key**: UUID with auto-generation
- **Metadata**: sweep_run_id (grouping), created_at, sweep_config (JSONB)
- **Core parameters**: ticker, strategy_type, fast/slow/signal periods
- **Performance metrics**: score, sharpe_ratio, win_rate, returns, drawdowns
- **Trade statistics**: total trades, win/loss analysis, durations
- **Risk metrics**: volatility, value at risk, skew, kurtosis
- **4 Indexes**: sweep_run_id, ticker, created_at, composite

### Features
- Async batch insert (100 records/batch)
- Automatic column mapping from CSV
- Type conversion (Decimal precision)
- Query by sweep_run_id
- Summary statistics methods

### Impact
- Persistent storage for all sweep results
- Queryable backtest data
- Foundation for analytics
- Enables API access

### Files
- Migration: `app/database/migrations/versions/002_create_strategy_sweep_table.py`
- Models: `app/database/models.py` (added StrategySweepResult)
- Repository: `app/database/strategy_sweep_repository.py` (created)

---

## Migration 001: API Infrastructure (Initial)

### Purpose
Set up API authentication and job tracking infrastructure.

### Changes
1. **Created `api_keys` table**:
   - API key management
   - Scope-based permissions
   - Active status tracking

2. **Created `jobs` table**:
   - Async job tracking
   - Progress monitoring
   - Result storage
   - Error handling

### Features
- API key authentication
- Job queuing system
- Progress tracking
- Result retrieval

### Impact
- Foundation for API functionality
- Async operation support
- Security infrastructure

---

## Database Evolution Summary

### Tables Added
1. `api_keys` - API authentication
2. `jobs` - Job tracking
3. `strategy_sweep_results` - Main results table
4. `metric_types` - Metric classifications
5. `strategy_sweep_result_metrics` - Junction table
6. `selection_algorithms` - Selection algorithm reference
7. `sweep_best_selections` - Best portfolio tracking
8. `tickers` - Normalized ticker symbols
9. `strategy_types` - Normalized strategy types
10. `alembic_version` - Migration tracking

### Views Added
- 19 analytical views (migration 007)

### Total Schema Evolution
- Migrations: 7
- Tables: 10
- Views: 19
- Indexes: 20+
- Foreign Keys: 8
- Unique Constraints: 7

