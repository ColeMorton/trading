# Changelog

All notable changes to the Trading Strategy Platform are documented in this file.

## [Unreleased]

## [0.2.0] - 2025-10-19

### Added - Database Normalization & Sweep Results API

#### Database Schema Enhancements
- **Tickers Table** (Migration 004): Normalized ticker symbols with unique constraint
  - Migrated 6 unique tickers (AAPL, AMD, BKNG, MSFT, NVDA, TSLA)
  - Foreign key relationship with `strategy_sweep_results` (CASCADE delete)
  - 4,855 records successfully migrated from string to foreign key reference

- **Strategy Types Table** (Migration 006): Normalized strategy type identifiers
  - Migrated 1 strategy type (SMA) 
  - Foreign key relationships with `strategy_sweep_results` and `sweep_best_selections`
  - CASCADE delete behavior for referential integrity

- **Database Views** (Migration 007): 19 analytical views for performance analysis
  - 4 Core operational views (best results, rankings, latest sweep)
  - 4 Performance views (risk-adjusted, consistency analysis)
  - 4 Sweep analysis views (comparisons, parameter evolution)
  - 4 Trade efficiency views (win rate, expectancy, duration)
  - 3 Metric analysis views (classifications, leaders)

#### Sweep Results API
- **New Router**: `/api/v1/sweeps/*` with 5 endpoints
  - `GET /sweeps/` - List all sweep runs with summaries
  - `GET /sweeps/latest` - Get latest sweep results
  - `GET /sweeps/{id}` - Get all results for specific sweep (paginated)
  - `GET /sweeps/{id}/best` - Get best result for sweep (most common query)
  - `GET /sweeps/{id}/best-per-ticker` - Get best result per ticker

- **Response Models**: 4 new Pydantic schemas
  - `SweepResultDetail` - Individual result with 23+ metrics
  - `SweepResultsResponse` - Paginated results response
  - `BestResultsResponse` - Best results query response
  - `SweepSummaryResponse` - Sweep summary statistics

- **Auto-persistence**: API sweeps now automatically save to database

#### Test Coverage
- **42+ Tests**: Comprehensive test suite for new API
  - 23 unit tests for router endpoints
  - 18 schema validation tests
  - 1 endpoint registration test
  - ~90% estimated coverage for new code

#### Documentation
- **7 Comprehensive Guides** (~2,000 lines total):
  - API README - Main API documentation
  - SWEEP_RESULTS_API - Complete endpoint reference
  - API_DATA_FLOW - Data flow explanation
  - INTEGRATION_GUIDE - Best practices and patterns
  - QUICK_REFERENCE - Quick syntax guide
  - TEST_COVERAGE_SUMMARY - Test documentation
  - SQL Views README - Database views guide

- **2 Working Examples**:
  - Python client with complete workflow
  - Shell script with 10 cURL examples

### Changed
- `app/database/strategy_sweep_repository.py` - Updated to handle normalized foreign keys
- `app/database/models.py` - Added Ticker and StrategyType ORM models
- `app/api/models/schemas.py` - Added sweep result response models
- `app/api/main.py` - Registered new sweeps router

### Fixed
- Data normalization eliminates string duplication
- Query performance improved with indexed foreign keys
- Complete API data flow (previously results were inaccessible via API)

---

## [0.1.5] - 2025-10-19

### Added - Best Portfolio Selection Tracking

#### Database Tables (Migration 005)
- **selection_algorithms Table**: Reference table for selection algorithms
  - 5 pre-populated algorithms with confidence score ranges
  - Tracks algorithm metadata and selection criteria

- **sweep_best_selections Table**: Tracks optimal portfolio per sweep
  - Records best result for each sweep + ticker + strategy combination
  - Stores selection algorithm, criteria, and confidence scores
  - Denormalizes winning parameters for quick access
  - Snapshots key metrics at selection time
  - Unique constraint ensures one best per combination

#### Features
- Parameter consistency algorithm implementation
- Confidence scoring system (0-100%)
- Alternative consideration tracking
- Best selection computation and persistence
- Query methods for retrieving best selections

### Changed
- `app/database/models.py` - Added SweepBestSelection ORM model
- `app/database/strategy_sweep_repository.py` - Added best selection methods

---

## [0.1.0] - 2025-10-19

### Added - Metric Types Classification System

#### Database Tables (Migration 003)
- **metric_types Table**: Reference table for metric classifications
  - 86 pre-populated metric types across 5 categories
  - Categories: return (11), risk (33), trade (20), timing (19), composite (3)
  - Unique constraint on metric names

- **strategy_sweep_result_metrics Table**: Junction table for many-to-many relationships
  - Links sweep results to multiple metric type classifications
  - Unique constraint prevents duplicate assignments
  - CASCADE delete maintains referential integrity

#### Features
- Automatic metric type parsing from comma-separated strings
- Backward compatibility with legacy string column
- Many-to-many relationship support
- Query methods for finding results by metric type

### Changed
- `app/database/models.py` - Added MetricType and StrategySweepResultMetric models
- `app/database/strategy_sweep_repository.py` - Added metric type association methods

---

## [0.0.2] - 2025-10-19 (Earlier)

### Added - Strategy Sweep Database Persistence

#### Database Tables (Migration 002)
- **strategy_sweep_results Table**: Comprehensive backtest results storage
  - 67 total columns capturing all performance metrics
  - 4 optimized indexes for common query patterns
  - Supports all strategy types (SMA, EMA, MACD)

#### Repository Layer
- `StrategySweepRepository` class for async database operations
- Batch insert capabilities (100 records per batch)
- Automatic column mapping from CSV to database schema
- Connection pooling for performance

### Features
- CLI `--database` flag to persist sweep results
- Sweep run tracking with UUID grouping
- Comprehensive metric storage (returns, risk, trade stats)
- Query methods for retrieving sweep results

---

## [0.0.1] - Initial Database Setup

### Added
- **api_keys Table** (Migration 001): API authentication
- **jobs Table** (Migration 001): Async job tracking
- Initial Alembic migration infrastructure
- PostgreSQL database configuration

---

## Migration History

| Migration | Revision | Description | Records Migrated |
|-----------|----------|-------------|------------------|
| 001 | Initial | API keys and jobs tables | N/A |
| 002 | 002 | Strategy sweep results table | 0 (new) |
| 003 | 003 | Metric types and junction table | 4,855 |
| 004 | 004 | Tickers normalization | 4,855 |
| 005 | 005 | Best selections tracking | 0 (new) |
| 006 | 006 | Strategy types normalization | 4,855 |
| 007 | 007 | Database views | N/A (views) |

**Current Revision**: 007 (head)

---

## Database Statistics (as of 2025-10-19)

- **Total Sweep Results**: 4,855
- **Unique Tickers**: 6
- **Strategy Types**: 1 (SMA)
- **Metric Types**: 86
- **Sweep Runs**: 8
- **Database Views**: 19
- **Tables**: 10

---

## Documentation

For detailed information see:
- `/docs/api/` - API documentation
- `/docs/database/` - Database schema and migration docs
- `/sql/` - SQL views and queries documentation

