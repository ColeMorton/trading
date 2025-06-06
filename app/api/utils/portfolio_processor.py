"""
Portfolio Processing Utilities

This module provides common portfolio processing functionality shared across
different strategy implementations.
"""

import time
from typing import Any, Dict, List

from app.api.models.strategy_analysis import PortfolioMetrics


class PortfolioProcessor:
    """Utility class for common portfolio processing operations."""

    @staticmethod
    def convert_portfolios_to_metrics(
        portfolio_dicts: List[Dict], log
    ) -> List[PortfolioMetrics]:
        """Convert portfolio dictionaries to PortfolioMetrics objects efficiently.

        Args:
            portfolio_dicts: List of portfolio dictionaries
            log: Logging function

        Returns:
            List of PortfolioMetrics objects
        """
        portfolio_metrics = []

        for portfolio in portfolio_dicts:
            try:
                # Clean up strategy type if it has enum prefix
                strategy_type_value = portfolio.get(
                    "Strategy Type", portfolio.get("MA Type", "")
                )
                if (
                    isinstance(strategy_type_value, str)
                    and "StrategyTypeEnum." in strategy_type_value
                ):
                    strategy_type_value = strategy_type_value.replace(
                        "StrategyTypeEnum.", ""
                    )

                # Determine window column names based on strategy type
                if strategy_type_value == "SMA":
                    short_window = portfolio.get(
                        "SMA_FAST", portfolio.get("Short Window", 0)
                    )
                    long_window = portfolio.get(
                        "SMA_SLOW", portfolio.get("Long Window", 0)
                    )
                elif strategy_type_value == "EMA":
                    short_window = portfolio.get(
                        "EMA_FAST", portfolio.get("Short Window", 0)
                    )
                    long_window = portfolio.get(
                        "EMA_SLOW", portfolio.get("Long Window", 0)
                    )
                elif strategy_type_value == "MACD":
                    # For MACD, use different window mapping
                    short_window = portfolio.get("Short Window", 0)
                    long_window = portfolio.get("Long Window", 0)
                    # Note: MACD also has signal_window but PortfolioMetrics doesn't have that field yet
                else:
                    # Default case
                    short_window = portfolio.get("Short Window", 0)
                    long_window = portfolio.get("Long Window", 0)

                # Convert to int, handling None values
                short_window = int(short_window) if short_window is not None else 0
                long_window = int(long_window) if long_window is not None else 0

                # Calculate winning/losing trades from total trades and win rate
                total_trades = int(portfolio.get("Total Trades", 0))
                win_rate_pct = float(portfolio.get("Win Rate [%]", 0.0))
                winning_trades = int(total_trades * win_rate_pct / 100)
                losing_trades = total_trades - winning_trades

                # Convert string values to appropriate types
                total_open_trades = portfolio.get("Total Open Trades", 0)
                if isinstance(total_open_trades, str):
                    total_open_trades = (
                        int(total_open_trades) if total_open_trades.isdigit() else 0
                    )

                signal_entry = portfolio.get("Signal Entry", False)
                if isinstance(signal_entry, str):
                    signal_entry_bool = signal_entry.lower() == "true"
                else:
                    signal_entry_bool = bool(signal_entry)

                # Handle missing fields by providing defaults based on analysis
                avg_trade_duration = portfolio.get("Avg Trade Duration")
                if not avg_trade_duration:
                    # Try alternative field names or provide a default based on the data we have
                    avg_trade_duration = portfolio.get("Average Trade Duration")

                metric_type = portfolio.get("Metric Type")
                if not metric_type:
                    # Fallback for portfolios missing metric type (this should rarely happen now)
                    if float(portfolio.get("Score", 0.0)) > 1.0:
                        metric_type = (
                            "Most Total Return [%]"  # Use proper metric type format
                        )
                    else:
                        metric_type = "Most Total Return [%]"  # Default to most common metric type

                metrics = PortfolioMetrics(
                    ticker=portfolio.get("Ticker", ""),
                    strategy_type=strategy_type_value,
                    short_window=short_window,
                    long_window=long_window,
                    total_return=float(portfolio.get("Total Return [%]", 0.0)),
                    annual_return=float(
                        portfolio.get(
                            "Ann. Return [%]",
                            portfolio.get("Annual Returns", 0.0) * 100,
                        )
                    ),
                    sharpe_ratio=float(portfolio.get("Sharpe Ratio", 0.0)),
                    sortino_ratio=float(portfolio.get("Sortino Ratio", 0.0)),
                    max_drawdown=float(portfolio.get("Max Drawdown [%]", 0.0)),
                    total_trades=total_trades,
                    winning_trades=winning_trades,
                    losing_trades=losing_trades,
                    win_rate=win_rate_pct / 100.0,  # Convert percentage to decimal
                    profit_factor=float(portfolio.get("Profit Factor", 0.0)),
                    expectancy=float(portfolio.get("Expectancy", 0.0)),
                    expectancy_per_trade=float(
                        portfolio.get("Expectancy per Trade", 0.0)
                    ),
                    score=float(portfolio.get("Score", 0.0)),
                    beats_bnh=float(portfolio.get("Beats BNH [%]", 0.0)),
                    has_open_trade=bool(total_open_trades > 0),
                    has_signal_entry=signal_entry_bool,
                    metric_type=metric_type,
                    avg_trade_duration=avg_trade_duration,
                )
                portfolio_metrics.append(metrics)

            except (ValueError, TypeError, KeyError) as e:
                log(f"Error converting portfolio to metrics: {str(e)}", "error")
                continue

        return portfolio_metrics

    @staticmethod
    def export_and_deduplicate_portfolios(
        all_portfolio_dicts: List[Dict], config: Dict[str, Any], log
    ) -> List[Dict]:
        """Export portfolios and apply deduplication logic.

        Args:
            all_portfolio_dicts: Raw portfolio dictionaries
            config: Strategy configuration
            log: Logging function

        Returns:
            Deduplicated portfolio dictionaries
        """
        try:
            from app.tools.portfolio.collection import (
                deduplicate_and_aggregate_portfolios,
                export_best_portfolios,
            )

            log("Exporting best portfolios...")

            # IMPORTANT: Use the original portfolio dictionaries (all_portfolio_dicts) for export
            # to ensure all 59 columns are preserved in the CSV export.
            # Do NOT use the reduced PortfolioMetrics objects which only have 14 fields.
            export_best_portfolios(all_portfolio_dicts, config, log)
            log(
                f"Successfully exported {len(all_portfolio_dicts)} best portfolios with full canonical schema"
            )

            # Apply deduplication logic for frontend results
            desired_metric_types = config.get(
                "DESIRED_METRIC_TYPES",
                [
                    # Total Return [%] variants
                    "Most Total Return [%]",
                    "Mean Total Return [%]",
                    "Median Total Return [%]",
                    # Total Trades variants
                    "Most Total Trades",
                    "Mean Total Trades",
                    "Median Total Trades",
                    # Avg Winning Trade [%] variants
                    "Most Avg Winning Trade [%]",
                    "Mean Avg Winning Trade [%]",
                    "Median Avg Winning Trade [%]",
                    # Sharpe Ratio variants
                    "Most Sharpe Ratio",
                    "Mean Sharpe Ratio",
                    "Median Sharpe Ratio",
                    # Omega Ratio variants
                    "Most Omega Ratio",
                    "Mean Omega Ratio",
                    "Median Omega Ratio",
                    # Sortino Ratio variants
                    "Most Sortino Ratio",
                    "Mean Sortino Ratio",
                    "Median Sortino Ratio",
                    # Win Rate [%] variants
                    "Most Win Rate [%]",
                    "Mean Win Rate [%]",
                    "Median Win Rate [%]",
                    # Score variants
                    "Most Score",
                    "Mean Score",
                    "Median Score",
                    # Profit Factor variants
                    "Most Profit Factor",
                    "Mean Profit Factor",
                    "Median Profit Factor",
                    # Expectancy per Trade variants
                    "Most Expectancy per Trade",
                    "Mean Expectancy per Trade",
                    "Median Expectancy per Trade",
                    # Beats BNH [%] variants
                    "Most Beats BNH [%]",
                    "Mean Beats BNH [%]",
                    "Median Beats BNH [%]",
                ],
            )

            # Apply deduplication to the original portfolio dictionaries
            deduplicated_dicts = deduplicate_and_aggregate_portfolios(
                all_portfolio_dicts, log, desired_metric_types
            )

            log(
                f"Frontend will display {len(deduplicated_dicts)} deduplicated portfolios"
            )

            return deduplicated_dicts

        except Exception as e:
            log(f"Failed to export best portfolios: {str(e)}", "error")
            return []

    @staticmethod
    def collect_export_paths(
        config: Dict[str, Any], strategy_types: List[str], log
    ) -> Dict[str, List[str]]:
        """
        Collect paths of exported portfolio CSV files.

        Args:
            config: Strategy configuration
            strategy_types: List of strategy types analyzed
            log: Logging function

        Returns:
            Dictionary with export paths organized by type
        """
        import glob

        export_paths = {"portfolios": [], "portfolios_filtered": []}

        try:
            # Get ticker list
            tickers = []
            if isinstance(config.get("TICKER"), str):
                tickers = [config["TICKER"]]
            elif isinstance(config.get("TICKER"), list):
                tickers = config["TICKER"]

            # Construct expected file paths for each ticker and strategy type
            for ticker in tickers:
                # Format ticker for filename (replace special characters)
                ticker_formatted = ticker.replace("-", "-").replace("/", "_")

                for strategy_type in strategy_types:
                    # Check for portfolio files
                    portfolio_pattern = (
                        f"csv/portfolios/{ticker_formatted}_*_{strategy_type}.csv"
                    )
                    portfolio_files = glob.glob(portfolio_pattern)
                    export_paths["portfolios"].extend(portfolio_files)

                    # Check for filtered portfolio files
                    filtered_pattern = f"csv/portfolios_filtered/{ticker_formatted}_*_{strategy_type}.csv"
                    filtered_files = glob.glob(filtered_pattern)
                    export_paths["portfolios_filtered"].extend(filtered_files)

            # Remove duplicates and sort
            export_paths["portfolios"] = sorted(list(set(export_paths["portfolios"])))
            export_paths["portfolios_filtered"] = sorted(
                list(set(export_paths["portfolios_filtered"]))
            )

            log(
                f"Found {len(export_paths['portfolios'])} portfolio files and {len(export_paths['portfolios_filtered'])} filtered files"
            )

        except Exception as e:
            log(f"Error collecting export paths: {str(e)}", "error")

        return export_paths
