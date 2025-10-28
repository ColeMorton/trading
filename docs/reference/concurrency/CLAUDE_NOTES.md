# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Trading Strategy Concurrency Analysis Module** that analyzes how multiple trading strategies work together, evaluates overlap, risk concentration, and finds optimal strategy combinations.

## Common Development Commands

```bash
# Install dependencies
poetry install

# Run the concurrency analysis
poetry run python review.py

# Run with custom configuration
PORTFOLIO="crypto_d_20250303.json" poetry run python review.py
```

## Architecture

The module follows a clean architecture with these key components:

1. **Entry Point**: `review.py` - Main execution entry with configuration handling
2. **Core Analysis**: `tools/analysis.py` - Analyzes concurrent positions between strategies
3. **Optimization**: `tools/permutation.py` - Finds optimal strategy combinations
4. **Visualization**: `tools/visualization.py` - Generates concurrency charts
5. **Report Generation**: `tools/report/` - Creates detailed JSON reports

### Key Concepts

- **Concurrency**: When multiple strategies hold positions simultaneously
- **Efficiency Score**: Combines structural metrics (independence, diversification) with performance metrics
- **Permutation Analysis**: Tests all possible combinations of strategies to find optimal subsets

### Configuration

Configuration is handled through environment variables and defaults in `config_defaults.py`:

- `PORTFOLIO`: Portfolio file (JSON or CSV format)
- `VISUALIZATION`: Enable/disable chart generation
- `REPORT_INCLUDES`: Control report content (ticker metrics, strategies, relationships, allocation)

### Data Flow

1. Portfolio loaded from JSON/CSV → 2. Strategies processed → 3. Concurrency analyzed → 4. Metrics calculated → 5. Report generated

## Code Patterns

- Uses context managers for resource management (see `portfolio_context` usage)
- Error handling with custom exceptions in `app.tools.exceptions`
- Logging configured via `logging_context`
- Type hints throughout for clarity
- Configuration validation via `validate_config()`
