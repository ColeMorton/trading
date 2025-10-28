"""
Concurrency Analysis wrapper for integration testing.

This module provides a simple interface for running concurrency analysis
with configurable calculation fixes.
"""

from typing import Any

import polars as pl

from app.concurrency.tools.analysis import analyze_concurrency
from app.concurrency.tools.strategy_processor import process_strategies
from app.tools.portfolio import StrategyConfig


class ConcurrencyAnalysis:
    """Wrapper class for concurrency analysis with configurable fixes."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize with configuration.

        Args:
            config: Configuration dictionary with fix flags
        """
        self.config = config or {}
        self.log = self._setup_logging()

    def _setup_logging(self):
        """Set up logging function."""

        def log_func(message: str, level: str = "info"):
            print(f"[{level.upper()}] {message}")

        return log_func

    def analyze(
        self, data_list: list[pl.DataFrame], config_list: list[StrategyConfig],
    ) -> dict[str, Any]:
        """Run concurrency analysis on provided data.

        Args:
            data_list: List of dataframes with price and position data
            config_list: List of strategy configurations

        Returns:
            Dictionary with analysis statistics
        """
        # Pass configuration to analysis functions
        stats, _ = analyze_concurrency(data_list, config_list, self.log)
        return stats

    def run(self) -> dict[str, Any]:
        """Run analysis using portfolio from config.

        Returns:
            Dictionary with analysis statistics
        """
        if "PORTFOLIO" not in self.config:
            msg = "PORTFOLIO must be specified in config"
            raise ValueError(msg)

        # Load portfolio
        from app.tools.portfolio import load_portfolio
        from app.tools.portfolio.paths import resolve_portfolio_file_path

        portfolio_path = resolve_portfolio_file_path(
            self.config["PORTFOLIO"], self.config.get("BASE_DIR", ""),
        )

        strategies = load_portfolio(str(portfolio_path))

        # Process strategies
        data_list, aligned_data = process_strategies(strategies, self.log, self.config)

        # Convert strategies to config list
        config_list = []
        for strategy in strategies:
            config = StrategyConfig(
                ticker=strategy.get("TICKER", ""),
                timeframe=strategy.get("TIMEFRAME", "D"),
                strategy=strategy.get("STRATEGY", ""),
                ma_fast=strategy.get("MA_FAST", 0),
                ma_slow=strategy.get("MA_SLOW", 0),
                allocation=strategy.get("ALLOCATION", 1.0),
                stop_loss=strategy.get("STOP_LOSS", 0.02),
            )
            config_list.append(config)

        # Run analysis
        stats, _ = analyze_concurrency(aligned_data, config_list, self.log)

        return stats
