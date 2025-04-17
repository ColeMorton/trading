"""
MACD Next Strategy Package

This package contains modules for the MACD cross strategy, including:
- Portfolio analysis
- Signal generation
- Parameter sensitivity analysis
- Portfolio filtering
- Export functionality
"""

# Import key functions for easier access
import importlib
_module = importlib.import_module("app.macd_next.1_get_portfolios")
run = _module.run
run_strategies = _module.run_strategies