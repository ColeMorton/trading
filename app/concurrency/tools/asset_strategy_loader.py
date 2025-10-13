#!/usr/bin/env python3
"""
Asset Strategy Loader for Portfolio Construction

Auto-discovers and loads strategy files for a given asset from the portfolio metrics directory.
Applies intelligent filtering based on Score threshold and converts to concurrency format.
"""

import logging
from glob import glob
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from app.tools.exceptions import DataLoadError

logger = logging.getLogger(__name__)


# Positive Metrics Priority (is_positive = True)
# These represent GOOD performance - we want strategies with these metrics
# Ordered by preference: Sharpe (risk-adjusted) > Total Return (absolute)
POSITIVE_METRICS_PRIORITY = [
    # Risk-Adjusted Performance (preferred)
    "Most Sharpe Ratio",
    "Mean Sharpe Ratio",
    "Median Sharpe Ratio",
    "Most Sortino Ratio",
    "Mean Sortino Ratio",
    "Median Sortino Ratio",
    "Most Calmar Ratio",
    "Mean Calmar Ratio",
    "Median Calmar Ratio",
    "Most Omega Ratio",
    "Mean Omega Ratio",
    "Median Omega Ratio",
    # Absolute Returns
    "Most Total Return [%]",
    "Median Total Return [%]",
    "Mean Total Return [%]",
    # Trade Quality
    "Most Expectancy",
    "Mean Expectancy",
    "Median Expectancy",
    "Most Profit Factor",
    "Mean Profit Factor",
    "Median Profit Factor",
    # Win Rate
    "Most Win Rate [%]",
    "Mean Win Rate [%]",
    "Median Win Rate [%]",
    # Best Trades
    "Most Best Trade [%]",
    "Mean Best Trade [%]",
    "Median Best Trade [%]",
    # Worst Trades (higher/less negative is better)
    "Most Worst Trade [%]",
    "Mean Worst Trade [%]",
    "Median Worst Trade [%]",
    # Winning Trades
    "Most Avg Winning Trade [%]",
    "Mean Avg Winning Trade [%]",
    "Median Avg Winning Trade [%]",
    # Risk Metrics (least is best - inverted)
    "Least Max Drawdown [%]",
    "Least Max Drawdown Duration",
    "Least Avg Losing Trade [%]",
    "Least Total Fees Paid",
    # Duration Metrics
    "Least Avg Winning Trade Duration",
    "Least Avg Losing Trade Duration",
    # Trade Count
    "Most Total Trades",
]


class AssetStrategyLoader:
    """Loads and filters strategy data for portfolio construction."""

    def __init__(self, data_dir: str = "data/raw/portfolios_metrics"):
        """Initialize the loader with data directory path."""
        self.data_dir = Path(data_dir)

    def load_strategies_for_asset(
        self, asset: str, min_score: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Load all strategy files for a given asset and apply filtering.

        Args:
            asset: Asset symbol (e.g., 'MSFT', 'NVDA', 'BTC-USD')
            min_score: Minimum Score threshold for strategy inclusion

        Returns:
            List of strategy dictionaries ready for concurrency analysis

        Raises:
            DataLoadError: If no valid strategies found or data issues
        """
        logger.info(f"Loading strategies for asset: {asset}")

        # Auto-discover strategy files
        strategy_files = self._discover_strategy_files(asset)

        if not strategy_files:
            raise DataLoadError(f"No strategy files found for asset: {asset}")

        logger.info(f"Found {len(strategy_files)} strategy files for {asset}")

        # Load and filter strategies
        all_strategies = []

        for file_path in strategy_files:
            try:
                strategies = self._load_and_filter_file(file_path, min_score)
                all_strategies.extend(strategies)
                logger.info(
                    f"Loaded {len(strategies)} strategies from {file_path.name}"
                )
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")
                continue

        if not all_strategies:
            raise DataLoadError(
                f"No strategies meet filtering criteria (Score >= {min_score}) for asset: {asset}"
            )

        logger.info(f"Total strategies loaded for {asset}: {len(all_strategies)}")
        return all_strategies

    def _discover_strategy_files(self, asset: str) -> List[Path]:
        """Auto-discover strategy files matching the asset pattern."""
        pattern = str(self.data_dir / f"{asset}_D_*.csv")
        file_paths = glob(pattern)

        return [Path(path) for path in sorted(file_paths)]

    def _load_and_filter_file(
        self, file_path: Path, min_score: float
    ) -> List[Dict[str, Any]]:
        """Load CSV file and convert to strategy dictionaries with filtering."""
        df = pd.read_csv(file_path)

        # Deduplicate: Multiple rows exist per strategy with different "Metric Type" values
        # Select row with highest Score for each unique strategy combination
        if "Metric Type" in df.columns:
            # Group by unique strategy parameters
            group_cols = ["Ticker", "Strategy Type", "Fast Period", "Slow Period"]

            # Add Signal Period to grouping for MACD strategies
            if "Signal Period" in df.columns:
                # Check if this is a MACD file by examining strategy type
                if df["Strategy Type"].iloc[0] == "MACD":
                    group_cols.append("Signal Period")

            # For each unique strategy, select the row with highest Score
            filtered_rows = []
            for group_key, group in df.groupby(group_cols):
                # Sort by Score descending and take first row (highest score)
                best_row = group.nlargest(1, "Score").iloc[0]
                filtered_rows.append(best_row)

                logger.debug(
                    f"Selected best row for {group_key}: Score={best_row['Score']:.3f}"
                )

            if filtered_rows:
                df = pd.DataFrame(filtered_rows)
            else:
                logger.warning(
                    f"No strategies found after deduplication in {file_path.name}"
                )
                return []

        # Apply Score filtering
        filtered_df = df[df["Score"] >= min_score].copy()

        if filtered_df.empty:
            logger.warning(
                f"No strategies meet Score >= {min_score} in {file_path.name}"
            )
            return []

        # Convert to strategy dictionaries
        strategies = []

        for _, row in filtered_df.iterrows():
            try:
                strategy = self._convert_to_strategy_dict(row, file_path)
                strategies.append(strategy)
            except Exception as e:
                logger.warning(
                    f"Failed to convert strategy {row.get('Strategy_ID', 'unknown')}: {e}"
                )
                continue

        return strategies

    def _convert_to_strategy_dict(
        self, row: pd.Series, source_file: Path
    ) -> Dict[str, Any]:
        """Convert CSV row to strategy dictionary."""

        # Extract strategy identifier
        strategy_id = self._extract_strategy_id(row, source_file)

        # Create simple strategy dictionary
        strategy_data = {
            "strategy_id": strategy_id,
            "ticker": self._extract_ticker(row, source_file),
            "strategy_type": row.get("Strategy Type", "SMA"),
            "fast_period": int(row.get("Fast Period", 0)),
            "slow_period": int(row.get("Slow Period", 0)),
            # Performance metrics
            "total_trades": int(row.get("Total Trades", 0)),
            "win_rate": float(row.get("Win Rate [%]", 0.0)),
            "profit_factor": float(row.get("Profit Factor", 0.0)),
            "expectancy_per_trade": float(row.get("Expectancy per Trade", 0.0)),
            "sharpe_ratio": float(row.get("Sharpe Ratio", 0.0)),
            "sortino_ratio": float(row.get("Sortino Ratio", 0.0)),
            "calmar_ratio": float(row.get("Calmar Ratio", 0.0)),
            "omega_ratio": float(row.get("Omega Ratio", 0.0)),
            "total_return": float(row.get("Total Return [%]", 0.0)),
            "max_drawdown": float(row.get("Max Drawdown [%]", 0.0)),
            "annualized_return": float(row.get("Annualized Return", 0.0)),
            "annualized_volatility": float(row.get("Annualized Volatility", 0.0)),
            "score": float(row.get("Score", 0.0)),
            # Additional fields for concurrency analysis
            "allocation": 0.0,  # Triggers equal weight allocation in analysis
            "risk_contribution": 0.0,  # Will be calculated during analysis
            "start_date": row.get("Start", ""),
            "end_date": row.get("End", ""),
        }

        # Add signal_period for MACD strategies
        if strategy_data["strategy_type"] == "MACD":
            signal_period = row.get("Signal Period")
            if signal_period is not None and signal_period != "":
                strategy_data["signal_period"] = int(signal_period)

        return strategy_data

    def _extract_strategy_id(self, row: pd.Series, source_file: Path) -> str:
        """Extract or generate strategy ID."""
        if "Strategy_ID" in row and pd.notna(row["Strategy_ID"]):
            return str(row["Strategy_ID"])

        # Generate ID from available data using centralized function
        ticker = self._extract_ticker(row, source_file)
        strategy_type = row.get("Strategy Type", "SMA")
        fast = int(row.get("Fast Period", 0))
        slow = int(row.get("Slow Period", 0))

        # Get signal_period for MACD strategies (default to 0 for others)
        signal = 0
        if strategy_type == "MACD":
            signal_value = row.get("Signal Period")
            if signal_value is not None and signal_value != "":
                signal = int(signal_value)

        # Use centralized UUID generation for consistency
        from app.tools.uuid_utils import generate_strategy_id

        return generate_strategy_id(ticker, strategy_type, fast, slow, signal)

    def _extract_ticker(self, row: pd.Series, source_file: Path) -> str:
        """Extract ticker from row data or filename."""
        if "Ticker" in row and pd.notna(row["Ticker"]):
            return str(row["Ticker"])

        # Extract from filename: MSFT_D_SMA.csv -> MSFT
        filename = source_file.stem
        parts = filename.split("_")
        if len(parts) >= 1:
            return parts[0]

        return "UNKNOWN"

    def get_available_assets(self) -> List[str]:
        """Get list of available assets based on existing strategy files."""
        pattern = str(self.data_dir / "*_D_*.csv")
        file_paths = glob(pattern)

        assets = set()
        for path in file_paths:
            filename = Path(path).stem
            parts = filename.split("_")
            if len(parts) >= 1:
                assets.add(parts[0])

        return sorted(list(assets))

    def validate_asset_data(self, asset: str) -> Dict[str, Any]:
        """Validate data quality for an asset."""
        try:
            strategies = self.load_strategies_for_asset(
                asset, min_score=0.0
            )  # Load all for validation

            # Basic validation metrics
            total_strategies = len(strategies)
            score_filtered = len([s for s in strategies if s["score"] >= 1.0])

            # Strategy type distribution
            strategy_types = {}
            for strategy in strategies:
                strategy_types[strategy["strategy_type"]] = (
                    strategy_types.get(strategy["strategy_type"], 0) + 1
                )

            # Parameter ranges
            if strategies:
                fast_periods = [
                    s["fast_period"] for s in strategies if s["fast_period"] > 0
                ]
                slow_periods = [
                    s["slow_period"] for s in strategies if s["slow_period"] > 0
                ]

                validation_result = {
                    "asset": asset,
                    "total_strategies": total_strategies,
                    "score_filtered_strategies": score_filtered,
                    "strategy_types": strategy_types,
                    "parameter_ranges": {
                        "fast_period": {
                            "min": min(fast_periods) if fast_periods else 0,
                            "max": max(fast_periods) if fast_periods else 0,
                        },
                        "slow_period": {
                            "min": min(slow_periods) if slow_periods else 0,
                            "max": max(slow_periods) if slow_periods else 0,
                        },
                    },
                    "viable_for_construction": score_filtered
                    >= 5,  # Need at least 5 for smallest portfolio
                }
            else:
                validation_result = {
                    "asset": asset,
                    "total_strategies": 0,
                    "score_filtered_strategies": 0,
                    "strategy_types": {},
                    "parameter_ranges": {},
                    "viable_for_construction": False,
                }

            return validation_result

        except Exception as e:
            return {"asset": asset, "error": str(e), "viable_for_construction": False}
