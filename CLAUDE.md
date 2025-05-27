# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Strictly adhere to DRY, SOLID, KISS and YAGNI principles!

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

# Update and aggregate portfolio results
python app/strategies/update_portfolios.py
```

## Architecture Overview

### Core Components
- **FastAPI REST API** (`/app/api/`): RESTful endpoints with routers for scripts, data, MA Cross analysis, CSV viewer, and trading dashboard
- **MA Cross Strategy** (`/app/ma_cross/`): Moving average crossover implementation with core abstraction layer for programmatic and CLI usage
- **Portfolio Management** (`/app/strategies/`): Portfolio aggregation, filtering, and performance metrics calculation
- **Trading Tools** (`/app/tools/`): Comprehensive utilities for backtesting, signal processing, metrics calculation, and data management

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

## important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
