"""
Results Export Service

Handles result export and transformation for MA Cross analysis.
This service is responsible for converting, formatting, and exporting portfolio results.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import polars as pl

from app.api.models.ma_cross import PortfolioMetrics
from app.core.interfaces import LoggingInterface


class ResultsExportService:
    """Service for exporting and transforming analysis results."""

    def __init__(self, logger: LoggingInterface):
        """
        Initialize the results export service.

        Args:
            logger: Logging interface
        """
        self.logger = logger

    def convert_to_portfolio_metrics(
        self,
        portfolio_dicts: List[Dict[str, Any]],
    ) -> List[PortfolioMetrics]:
        """
        Convert portfolio dictionaries to PortfolioMetrics objects.

        Args:
            portfolio_dicts: List of portfolio dictionaries

        Returns:
            List of PortfolioMetrics objects
        """
        metrics_list = []

        for portfolio in portfolio_dicts:
            try:
                # Extract strategy type (handle enum prefix)
                strategy_type = str(portfolio.get("Strategy Type", ""))
                if strategy_type.startswith("StrategyTypeEnum."):
                    strategy_type = strategy_type.replace("StrategyTypeEnum.", "")

                # Determine window fields based on strategy type
                if strategy_type == "SMA":
                    short_window = portfolio.get("SMA_FAST") or portfolio.get(
                        "Short Window", 0
                    )
                    long_window = portfolio.get("SMA_SLOW") or portfolio.get(
                        "Long Window", 0
                    )
                elif strategy_type == "EMA":
                    short_window = portfolio.get("EMA_FAST") or portfolio.get(
                        "Short Window", 0
                    )
                    long_window = portfolio.get("EMA_SLOW") or portfolio.get(
                        "Long Window", 0
                    )
                else:
                    short_window = portfolio.get("Short Window", 0)
                    long_window = portfolio.get("Long Window", 0)

                # Convert win rate from percentage to decimal if needed
                win_rate = portfolio.get("Win Rate [%]", 0)
                if win_rate > 1:  # Assume it's a percentage
                    win_rate = win_rate / 100

                # Calculate winning/losing trades
                total_trades = portfolio.get("Total Trades", 0)
                winning_trades = int(total_trades * win_rate) if total_trades > 0 else 0
                losing_trades = total_trades - winning_trades

                # Create PortfolioMetrics object
                metrics = PortfolioMetrics(
                    ticker=portfolio.get("Ticker", ""),
                    strategy_type=strategy_type,
                    short_window=int(short_window) if short_window else 0,
                    long_window=int(long_window) if long_window else 0,
                    signal_window=int(portfolio.get("Signal Window", 0)),
                    direction=portfolio.get("Direction", "Long"),
                    timeframe=portfolio.get("Timeframe", "D"),
                    total_return=float(portfolio.get("Total Return [%]", 0)),
                    annual_return=float(portfolio.get("Ann. Return [%]", 0)),
                    sharpe_ratio=float(portfolio.get("Sharpe Ratio", 0)),
                    sortino_ratio=float(portfolio.get("Sortino Ratio", 0)),
                    max_drawdown=float(portfolio.get("Max Drawdown [%]", 0)),
                    total_trades=total_trades,
                    winning_trades=winning_trades,
                    losing_trades=losing_trades,
                    win_rate=win_rate,
                    profit_factor=float(portfolio.get("Profit Factor", 0)),
                    expectancy=float(portfolio.get("Expectancy", 0)),
                    expectancy_per_trade=float(
                        portfolio.get(
                            "Expectancy Per Trade", portfolio.get("Expectancy", 0)
                        )
                    ),
                    score=float(portfolio.get("Score", 0)),
                    beats_bnh=float(portfolio.get("Beats BNH [%]", 0)),
                    has_open_trade=bool(portfolio.get("Total Open Trades", 0) > 0),
                    has_signal_entry=bool(portfolio.get("Signal Entry", False)),
                    metric_type=portfolio.get("Metric Type"),
                )

                metrics_list.append(metrics)

            except Exception as e:
                self.logger.log(
                    f"Error converting portfolio to metrics: {str(e)}", "error"
                )
                continue

        return metrics_list

    def export_to_csv(
        self,
        portfolios: List[Dict[str, Any]],
        base_path: str,
        filename_prefix: str,
    ) -> Optional[str]:
        """
        Export portfolios to CSV file.

        Args:
            portfolios: List of portfolio dictionaries
            base_path: Base directory path for export
            filename_prefix: Prefix for the filename

        Returns:
            Path to exported file or None if export failed
        """
        if not portfolios:
            self.logger.log("No portfolios to export", "warning")
            return None

        try:
            # Create directory if it doesn't exist
            export_dir = Path(base_path) / "csv" / "portfolios_best"
            export_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"{filename_prefix}_{timestamp}.csv"
            filepath = export_dir / filename

            # Convert to DataFrame and export
            df = pl.DataFrame(portfolios)
            df.write_csv(filepath)

            self.logger.log(
                f"Exported {len(portfolios)} portfolios to {filepath}", "info"
            )
            return str(filepath)

        except Exception as e:
            self.logger.log(f"Error exporting to CSV: {str(e)}", "error")
            return None

    def export_to_json(
        self,
        portfolios: List[Dict[str, Any]],
        base_path: str,
        filename_prefix: str,
    ) -> Optional[str]:
        """
        Export portfolios to JSON file.

        Args:
            portfolios: List of portfolio dictionaries
            base_path: Base directory path for export
            filename_prefix: Prefix for the filename

        Returns:
            Path to exported file or None if export failed
        """
        if not portfolios:
            self.logger.log("No portfolios to export", "warning")
            return None

        try:
            # Create directory if it doesn't exist
            export_dir = Path(base_path) / "json" / "portfolios"
            export_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"{filename_prefix}_{timestamp}.json"
            filepath = export_dir / filename

            # Export to JSON with pretty formatting
            with open(filepath, "w") as f:
                json.dump(portfolios, f, indent=2)

            self.logger.log(
                f"Exported {len(portfolios)} portfolios to {filepath}", "info"
            )
            return str(filepath)

        except Exception as e:
            self.logger.log(f"Error exporting to JSON: {str(e)}", "error")
            return None

    def create_summary_report(
        self,
        portfolios: List[Dict[str, Any]],
        execution_time: float,
    ) -> Dict[str, Any]:
        """
        Create a summary report of the analysis results.

        Args:
            portfolios: List of portfolio dictionaries
            execution_time: Total execution time in seconds

        Returns:
            Summary report dictionary
        """
        if not portfolios:
            return {
                "total_portfolios": 0,
                "execution_time": execution_time,
                "summary": "No portfolios generated",
            }

        df = pl.DataFrame(portfolios)

        # Calculate summary statistics
        summary = {
            "total_portfolios": len(portfolios),
            "execution_time": round(execution_time, 2),
            "unique_tickers": df["Ticker"].n_unique() if "Ticker" in df.columns else 0,
            "strategy_distribution": {},
            "performance_summary": {},
            "best_performers": {},
        }

        # Strategy distribution
        if "Strategy Type" in df.columns:
            strategy_counts = df.group_by("Strategy Type").agg(pl.len()).to_dicts()
            summary["strategy_distribution"] = {
                row["Strategy Type"]: row["len"] for row in strategy_counts
            }

        # Performance summary
        metrics_to_summarize = [
            ("Total Return [%]", "total_return"),
            ("Sharpe Ratio", "sharpe_ratio"),
            ("Win Rate [%]", "win_rate"),
            ("Score", "score"),
        ]

        for col_name, metric_name in metrics_to_summarize:
            if col_name in df.columns:
                summary["performance_summary"][metric_name] = {
                    "mean": round(df[col_name].mean(), 2),
                    "median": round(df[col_name].median(), 2),
                    "max": round(df[col_name].max(), 2),
                    "min": round(df[col_name].min(), 2),
                }

        # Best performers by key metrics
        if "Total Return [%]" in df.columns:
            best_return = (
                df.sort("Total Return [%]", descending=True).head(1).to_dicts()[0]
            )
            summary["best_performers"]["total_return"] = {
                "ticker": best_return.get("Ticker"),
                "value": best_return.get("Total Return [%]"),
                "strategy": best_return.get("Strategy Type"),
            }

        if "Sharpe Ratio" in df.columns:
            best_sharpe = df.sort("Sharpe Ratio", descending=True).head(1).to_dicts()[0]
            summary["best_performers"]["sharpe_ratio"] = {
                "ticker": best_sharpe.get("Ticker"),
                "value": best_sharpe.get("Sharpe Ratio"),
                "strategy": best_sharpe.get("Strategy Type"),
            }

        return summary

    def format_for_api_response(
        self,
        portfolios: List[PortfolioMetrics],
        request_params: Dict[str, Any],
        execution_time: float,
        export_paths: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Format results for API response.

        Args:
            portfolios: List of PortfolioMetrics objects
            request_params: Original request parameters
            execution_time: Execution time in seconds
            export_paths: Optional dictionary of export file paths

        Returns:
            Formatted response dictionary
        """
        # Convert PortfolioMetrics to dicts for JSON serialization
        portfolio_dicts = [p.dict() for p in portfolios]

        response = {
            "status": "success",
            "request_id": request_params.get("request_id", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "ticker": request_params.get("ticker"),
            "strategy_types": request_params.get("strategy_types", []),
            "portfolios": portfolio_dicts,
            "total_portfolios_analyzed": request_params.get(
                "total_analyzed", len(portfolios)
            ),
            "total_portfolios_filtered": len(portfolios),
            "execution_time": round(execution_time, 3),
        }

        if export_paths:
            response["portfolio_exports"] = export_paths

        return response

    def aggregate_results_by_ticker(
        self,
        portfolios: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Aggregate portfolio results by ticker.

        Args:
            portfolios: List of portfolio dictionaries

        Returns:
            Dictionary with aggregated results per ticker
        """
        ticker_results = {}

        for portfolio in portfolios:
            ticker = portfolio.get("Ticker") or portfolio.get("ticker")
            if not ticker:
                continue

            if ticker not in ticker_results:
                ticker_results[ticker] = {
                    "portfolio_count": 0,
                    "strategies": set(),
                    "best_return": float("-inf"),
                    "best_sharpe": float("-inf"),
                    "best_portfolio": None,
                }

            # Update aggregates
            ticker_results[ticker]["portfolio_count"] += 1
            ticker_results[ticker]["strategies"].add(portfolio.get("Strategy Type", ""))

            # Track best performers
            total_return = portfolio.get("Total Return [%]", float("-inf"))
            if total_return > ticker_results[ticker]["best_return"]:
                ticker_results[ticker]["best_return"] = total_return
                ticker_results[ticker]["best_portfolio"] = portfolio

            sharpe_ratio = portfolio.get("Sharpe Ratio", float("-inf"))
            if sharpe_ratio > ticker_results[ticker]["best_sharpe"]:
                ticker_results[ticker]["best_sharpe"] = sharpe_ratio

        # Convert sets to lists for JSON serialization
        for ticker in ticker_results:
            ticker_results[ticker]["strategies"] = list(
                ticker_results[ticker]["strategies"]
            )

        return ticker_results
