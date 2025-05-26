# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

```bash
# Install dependencies (using uv package manager)
uv pip install -r pyproject.toml

# Run development server
python main.py
# or
python app.py

# Run production server
gunicorn app:app
```

## Architecture Overview

This is a Flask-based web application for trading strategy sensitivity analysis using Clean Architecture principles:

- **Interfaces** (`interfaces/`) define contracts for services and adapters
- **Services** (`services/`) contain business logic implementations  
- **Adapters** (`adapters/`) integrate external analysis tools (MA Cross)
- **Models** (`models.py`) define the `PortfolioAnalysis` data model
- **Data Processing** (`data_processor.py`) handles CSV parsing and validation
- **Custom Exceptions** (`exceptions/`) for domain-specific error handling

The application follows a session-based architecture where portfolios are stored in Flask sessions. The frontend uses vanilla JavaScript with DataTables for interactive analysis.

## Key Implementation Details

- **MA Cross Integration**: The `ma_cross_adapter.py` wraps an external analysis module
- **Portfolio Builder**: Supports weighted allocations across multiple strategies
- **Parameter Sensitivity**: Analyzes SMA/EMA strategies with configurable parameters
- **Data Format**: Expects CSV files with Date, Symbol, Close columns
- **Session Management**: Uses Flask sessions with `SESSION_SECRET` environment variable