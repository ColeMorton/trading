# Database Documentation

## Overview

This directory contains comprehensive documentation for the PostgreSQL database schema used in the Trading Strategy Platform.

## Current Database State

**Database**: `trading_db`
**Current Migration**: 007 (head)
**Total Tables**: 10
**Total Views**: 19
**Total Records**: 4,855 strategy sweep results

## Quick Links

- **[Schema Documentation](./SCHEMA.md)** - Complete table and column reference
- **[Migration Changelog](./CHANGELOG.md)** - Detailed migration history
- **[SQL Views Guide](./SQL_VIEWS_GUIDE.md)** - Database views and queries
- **[Integration Tests](./INTEGRATION_TEST_RESULTS.md)** - Test results

## Database Structure

### Core Tables

#### Strategy Sweep Results

**Table**: `strategy_sweep_results`
**Purpose**: Store comprehensive backtest results from parameter sweeps
**Columns**: 60+ performance metrics
**Records**: 4,855
**Key Relationships**:

- `ticker_id` → `tickers.id` (normalized ticker reference)
- `strategy_type_id` → `strategy_types.id` (normalized strategy type)
- Many-to-many with `metric_types` via junction table

#### Reference Tables (Normalization)

- `tickers` - Unique ticker symbols (6 tickers)
- `strategy_types` - Unique strategy types (1 type)
- `metric_types` - Metric classifications (86 types)
- `selection_algorithms` - Selection algorithms (5 algorithms)

#### Tracking Tables

- `sweep_best_selections` - Best portfolio per sweep+ticker+strategy
- `strategy_sweep_result_metrics` - Junction table for metric classifications
- `jobs` - API job tracking
- `api_keys` - API authentication

### Database Views (19 total)

Optimized views for common queries - see [SQL Views Guide](./SQL_VIEWS_GUIDE.md)

**Most Important Views:**

- `v_best_by_sweep_and_ticker` - Best result per ticker per sweep
- `v_best_results_per_sweep` - Best result + summary per sweep
- `v_latest_best_results` - Latest sweep results

## Common Queries

### Get Best Result for Ticker in Sweep

```sql
SELECT * FROM v_best_by_sweep_and_ticker
WHERE sweep_run_id = 'your-uuid'
  AND ticker = 'AAPL';
```

### Get Latest Sweep Summary

```sql
SELECT * FROM v_best_results_per_sweep
ORDER BY run_date DESC
LIMIT 1;
```

### Find Optimal Parameters for Ticker

```sql
SELECT fast_period, slow_period, AVG(score) as avg_score
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
WHERE t.ticker = 'AAPL'
GROUP BY fast_period, slow_period
ORDER BY avg_score DESC
LIMIT 10;
```

### List All Tickers

```sql
SELECT id, ticker, created_at
FROM tickers
ORDER BY ticker;
```

## Schema Design Principles

### Normalization

- ✅ Tickers normalized (foreign key reference)
- ✅ Strategy types normalized (foreign key reference)
- ✅ Metric types normalized (many-to-many)
- ✅ No data duplication

### Referential Integrity

- ✅ Foreign keys with CASCADE deletes
- ✅ Unique constraints prevent duplicates
- ✅ NOT NULL constraints on critical fields

### Performance

- ✅ Indexes on all foreign keys
- ✅ Composite indexes for common queries
- ✅ Database views for complex aggregations
- ✅ Query times < 100ms

### Extensibility

- ✅ Easy to add new tickers
- ✅ Easy to add new strategy types
- ✅ Easy to add new metric classifications
- ✅ Backward compatible property accessors

## Migration Management

### Running Migrations

```bash
# Check current version
alembic current

# View migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade 006
```

### Creating New Migrations

```bash
# Create new migration
alembic revision -m "description of changes"

# Edit the generated file in app/database/migrations/versions/
# Implement upgrade() and downgrade() functions

# Test the migration
alembic upgrade head
```

## Data Statistics

### Current Data (as of 2025-10-19)

```sql
SELECT
    COUNT(*) as total_results,
    COUNT(DISTINCT sweep_run_id) as sweep_runs,
    COUNT(DISTINCT ticker_id) as unique_tickers,
    COUNT(DISTINCT strategy_type_id) as strategy_types
FROM strategy_sweep_results;
```

**Results:**

- Total Results: 4,855
- Sweep Runs: 8
- Unique Tickers: 6
- Strategy Types: 1

### Top Performers

```sql
SELECT t.ticker, sr.score, sr.fast_period, sr.slow_period
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
ORDER BY sr.score DESC
LIMIT 5;
```

**Top 5:**

1. BKNG: 1.81 (72/76)
2. BKNG: 1.79 (73/77)
3. BKNG: 1.79 (73/76)
4. BKNG: 1.75 (71/76)
5. BKNG: 1.75 (69/77)

## Maintenance

### Backup

```bash
# Backup database
pg_dump trading_db > backup_$(date +%Y%m%d).sql

# Backup with compression
pg_dump trading_db | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore

```bash
# Restore from backup
psql trading_db < backup_20251019.sql
```

### Vacuum and Analyze

```sql
-- Reclaim space and update statistics
VACUUM ANALYZE strategy_sweep_results;
VACUUM ANALYZE tickers;
VACUUM ANALYZE strategy_types;
```

## Documentation Files

### In This Directory

- **README.md** (this file) - Overview and quick reference
- **CHANGELOG.md** - Detailed migration history
- **SCHEMA.md** - Complete schema documentation (renamed from STRATEGY_SWEEP_SCHEMA.md)
- **SQL_VIEWS_GUIDE.md** - SQL views and queries reference
- **METRIC_TYPES_IMPLEMENTATION.md** - Metric types feature details
- **INTEGRATION_TEST_RESULTS.md** - Database integration test results
- **BEFORE_AFTER_COMPARISON.md** - Before/after schema comparison
- **OUTPUT_IMPROVEMENTS.md** - Output and display improvements

### Related Documentation

- **SQL Views**: `./SQL_VIEWS_GUIDE.md`
- **API Integration**: `../api/README.md`
- **Migration Scripts**: `../../app/database/migrations/versions/`

## Quick Start

### 1. Connect to Database

```bash
psql postgresql://trading_user:trading_password@localhost:5432/trading_db
```

### 2. Check Current State

```sql
-- List all tables
\dt

-- List all views
\dv

-- Check migration version
SELECT * FROM alembic_version;
```

### 3. Query Recent Sweeps

```sql
SELECT * FROM v_best_results_per_sweep
ORDER BY run_date DESC
LIMIT 5;
```

### 4. Find Best Strategy

```sql
SELECT * FROM v_best_by_sweep_and_ticker
WHERE ticker = 'AAPL'
ORDER BY score DESC
LIMIT 1;
```

## Support

For detailed information:

- Schema reference: [SCHEMA.md](./SCHEMA.md)
- Migration history: [CHANGELOG.md](./CHANGELOG.md)
- SQL Views: [SQL_VIEWS_GUIDE.md](./SQL_VIEWS_GUIDE.md)
- API access: [../api/](../api/)

## Summary

The Trading Strategy Platform database provides:

- ✅ Normalized, efficient schema
- ✅ Comprehensive backtest data storage
- ✅ 19 analytical views
- ✅ Full migration history
- ✅ Production-ready performance
