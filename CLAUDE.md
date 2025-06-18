# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup

```bash
poetry install  # Install dependencies
```

### API Server

```bash
# Default server (http://127.0.0.1:8000)
python -m app.api.run

# Custom options
python -m app.api.run --host 0.0.0.0 --port 8080 --reload

# Test API endpoints
python app/api/test_api.py
```

### Strategy Execution

```bash
# Run MA Cross strategy analysis
python app/ma_cross/1_get_portfolios.py

# Run MACD strategy analysis
python app/strategies/macd/1_get_portfolios.py

# Update and aggregate portfolio results
python app/strategies/update_portfolios.py

# Run concurrency analysis with trade history export
python app/concurrency/review.py
```

## Architecture Overview

### Core Components

- **FastAPI REST API** (`/app/api/`): RESTful endpoints with routers for scripts, data, strategy analysis, CSV viewer, and trading dashboard
- **Modular Strategy Analysis Service** (`/app/api/services/`, `/app/tools/services/`): Decomposed service architecture with:
  - **StrategyExecutionEngine**: Strategy validation and execution logic
  - **PortfolioProcessingService**: Portfolio data processing and conversion
  - **ResultAggregationService**: Result formatting and task management
  - **ServiceCoordinator**: Orchestrates all services while maintaining interface compatibility
- **MA Cross Strategy** (`/app/ma_cross/`): Moving average crossover implementation with core abstraction layer for programmatic and CLI usage
- **MACD Strategy** (`/app/strategies/macd/`): MACD crossover strategy with comprehensive parameter analysis and multi-ticker support
- **Portfolio Management** (`/app/strategies/`): Portfolio aggregation, filtering, and performance metrics calculation
- **Trading Tools** (`/app/tools/`): Comprehensive utilities for backtesting, signal processing, metrics calculation, and data management
- **Performance Optimization** (`/app/tools/processing/`): Intelligent caching, parallel processing, and batch optimization for improved performance

### Data Flow

1. Market data acquisition via yfinance → CSV storage (`/csv/price_data/`)
2. Strategy analysis → Portfolio CSVs (`/csv/portfolios/`)
3. Portfolio aggregation/filtering → Best portfolios (`/csv/portfolios_best/`, `/csv/portfolios_filtered/`)
4. API access → Real-time strategy execution and data retrieval

### Key Technologies

- **Poetry** for dependency management
- **Polars** for high-performance data processing
- **VectorBT** for backtesting
- **Pydantic** for type-safe request/response handling

### Notable Features

- Synthetic ticker support (e.g., STRK_MSTR pair analysis)
- Allocation management with position sizing
- Comprehensive risk management through stop-loss calculations
- 20+ performance metrics per strategy
- Schema evolution support (base and extended portfolio schemas)
- **Trade History Export**: Comprehensive trade data export (trades, orders, positions) to JSON format
  - **IMPORTANT**: Only available through `app/concurrency/review.py` to prevent generating thousands of files from parameter sweep strategies
  - Exports to `./json/trade_history/` with filenames like `BTC-USD_D_SMA_20_50.json`
- **Standardized CSV Exports**: All strategies export to consistent directory structure
  - Base portfolios: `/csv/portfolios/` (e.g., `NFLX_D_MACD.csv`, `AAPL_D_SMA.csv`)
  - Filtered portfolios: `/csv/portfolios_filtered/`
  - Best portfolios: `/csv/portfolios_best/`
  - Strategy type included in filename for easy identification

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/api/test_strategy_analysis_service.py
pytest tests/test_strategy_factory.py
pytest app/strategies/macd/test_multi_ticker.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app
```

### Test Structure

- **Unit Tests**: `/tests/` - Core functionality testing with mocking
- **Integration Tests**: `/tests/api/` - Service layer and API endpoint testing
- **Strategy Tests**: `/app/strategies/*/test_*.py` - Strategy-specific validation
- **End-to-End Tests**: Full workflow validation with real data

### Key Test Features

- **Modular Service Testing**: Independent testing of `StrategyExecutionEngine`, `PortfolioProcessingService`, `ResultAggregationService`
- **Mock-Heavy Approach**: Extensive mocking for isolated unit testing
- **Async Testing**: Full support for async operations with proper fixtures
- **Interface Compatibility**: Validation that modular architecture maintains API contracts
- **Performance Testing**: Validation of optimization improvements and regression detection

## important-instruction-reminders

ALWAYS prefer editing an existing file to creating a new one.
Strictly adhere to DRY, SOLID, KISS and YAGNI principles!
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
NEVER proactively create documentation files (\*.md) or README files. Only create documentation files if explicitly requested by the User.
