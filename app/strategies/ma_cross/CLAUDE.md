# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Strictly adhere to DRY, SOLID, KISS and YAGNI principles!

# important-instruction-reminders

Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (\*.md) or README files. Only create documentation files if explicitly requested by the User.

## Commands

### Development Environment

```bash
# Install dependencies (requires Poetry)
poetry install

# Activate virtual environment
poetry shell

# Run a specific script
python <script_name.py>
```

### Common Workflows

```bash
# 1. Generate and analyze portfolios
python 1_get_portfolios.py

# 2. Run market scanner
python 1_scanner.py

# 3. Review performance with heatmaps
python 2_review_heatmaps.py

# 4. Analyze stop loss strategies
python 3_review_stop_loss.py
python 4_review_protective_stop_loss.py

# 5. Review slippage impact
python 5_review_slippage.py

# Interactive analysis
jupyter notebook 5_review.ipynb
```

## Architecture Overview

### Core Strategy System

The app implements Moving Average (MA) crossover strategies with comprehensive backtesting:

1. **Signal Generation**: MA crossovers (SMA/EMA) trigger buy/sell signals when fast MA crosses above/below slow MA
2. **Portfolio Management**: Processes multiple tickers with parameter sweeps to find optimal window combinations
3. **Performance Analysis**: Evaluates strategies using win rate, profit factor, Sharpe ratio, and custom metrics
4. **Risk Management**: Implements stop loss, protective stop loss, and slippage analysis

### Key Architectural Patterns

1. **Numbered Script Workflow**: Scripts prefixed 1-5 represent sequential analysis stages
2. **Modular Tools**: `tools/` directory contains reusable components organized by function
3. **Type Safety**: Uses TypedDict definitions in `config_types.py` for configuration management
4. **Data Pipeline**: Price data → Signal generation → Portfolio analysis → Filtering → Visualization

### Important Implementation Details

- **Vectorized Backtesting**: Uses vectorbt for efficient backtesting across parameter combinations
- **Synthetic Pairs**: Supports creating synthetic trading pairs from multiple tickers
- **Parameter Sensitivity**: Analyzes performance across different MA window sizes
- **Portfolio Filtering**: Applies criteria like minimum trades, win rate thresholds
- **Multi-timeframe**: Supports both daily and hourly data analysis
- **Configuration**: Strategy configs include ticker lists, MA types, window ranges, filters

### Data Flow

1. Ticker lists (JSON) → Price data fetching (yfinance)
2. Price data → Signal generation (MA crossovers)
3. Signals → Portfolio backtesting (vectorbt)
4. Results → Filtering and analysis
5. Analysis → Visualization and export
