"""
Trade History Analyzer

Specialized analyzer for individual trade-level statistical analysis.
Analyzes trade performance distributions, MFE/MAE patterns, and exit efficiency.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..config.statistical_analysis_config import SPDSConfig
from ..models.statistical_analysis_models import (
    ConfidenceLevel,
    PercentileMetrics,
    StatisticalMetrics,
    TradeHistoryMetrics,
    VaRMetrics,
)
from ..utils.mfe_mae_calculator import (
    get_mfe_mae_calculator,
    standardize_mfe_mae_columns,
)


class TradeHistoryAnalyzer:
    """
    Analyzes individual trade-level data for statistical patterns.

    Provides detailed analysis of:
    - Trade return distributions
    - Maximum Favorable Excursion (MFE) patterns
    - Maximum Adverse Excursion (MAE) patterns
    - Trade duration analysis
    - Exit efficiency metrics
    """

    def __init__(self, config: SPDSConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize the Trade History Analyzer

        Args:
            config: SPDS configuration instance
            logger: Logger instance for operations
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Trade quality thresholds
        self.excellent_return_threshold = 0.10  # 10% return
        self.good_return_threshold = 0.05  # 5% return
        self.poor_return_threshold = -0.02  # -2% return

        # Exit efficiency thresholds
        self.high_efficiency_threshold = 0.80  # 80% of MFE captured
        self.medium_efficiency_threshold = 0.60  # 60% of MFE captured

        self.logger.info("TradeHistoryAnalyzer initialized")

    async def analyze_strategy_trades(
        self, strategy_name: str, ticker: str
    ) -> Dict[str, Any]:
        """
        Analyze all trades for a specific strategy and ticker

        Args:
            strategy_name: Strategy identifier
            ticker: Asset ticker symbol

        Returns:
            Dictionary containing comprehensive trade analysis
        """
        try:
            # Load trade history data
            trade_data = await self._load_trade_history(strategy_name, ticker)

            if trade_data is None or len(trade_data) == 0:
                raise ValueError(
                    f"No trade history found for {strategy_name} on {ticker}"
                )

            # Analyze trade returns
            return_analysis = self._analyze_trade_returns(trade_data)

            # Analyze MFE/MAE patterns
            mfe_analysis = self._analyze_mfe_patterns(trade_data)
            mae_analysis = self._analyze_mae_patterns(trade_data)

            # Analyze trade durations
            duration_analysis = self._analyze_trade_durations(trade_data)

            # Calculate exit efficiency
            exit_efficiency = self._calculate_exit_efficiency(trade_data)

            # Assess trade quality
            quality_metrics = self._assess_trade_quality(trade_data)

            # Calculate VaR metrics
            var_metrics = self._calculate_var_metrics(trade_data["returns"])

            return {
                "strategy_name": strategy_name,
                "ticker": ticker,
                "total_trades": len(trade_data),
                "closed_trades": len(trade_data[trade_data["status"] == "closed"]),
                "open_positions": len(trade_data[trade_data["status"] == "open"]),
                "return_statistics": return_analysis["statistics"],
                "return_percentiles": return_analysis["percentiles"],
                "var_metrics": var_metrics,
                "mfe_statistics": mfe_analysis["statistics"],
                "mae_statistics": mae_analysis["statistics"],
                "duration_statistics": duration_analysis["statistics"],
                "win_rate": return_analysis["win_rate"],
                "profit_factor": return_analysis["profit_factor"],
                "sharpe_ratio": return_analysis["sharpe_ratio"],
                "max_drawdown": return_analysis["max_drawdown"],
                "average_exit_efficiency": exit_efficiency["average_efficiency"],
                "mfe_capture_ratio": exit_efficiency["mfe_capture_ratio"],
                "excellent_trades": quality_metrics["excellent_trades"],
                "good_trades": quality_metrics["good_trades"],
                "poor_trades": quality_metrics["poor_trades"],
                "returns": trade_data["returns"].tolist(),  # For bootstrap validation
            }

        except Exception as e:
            self.logger.error(
                f"Failed to analyze trades for {strategy_name} on {ticker}: {e}"
            )
            raise

    async def get_trade_metrics(
        self, strategy_name: str, ticker: str
    ) -> TradeHistoryMetrics:
        """
        Get trade history metrics in structured format

        Args:
            strategy_name: Strategy identifier
            ticker: Asset ticker symbol

        Returns:
            Structured trade history metrics
        """
        try:
            analysis_result = await self.analyze_strategy_trades(strategy_name, ticker)

            return TradeHistoryMetrics(
                total_trades=analysis_result["total_trades"],
                closed_trades=analysis_result["closed_trades"],
                open_positions=analysis_result["open_positions"],
                return_distribution=analysis_result["return_statistics"],
                mfe_distribution=analysis_result["mfe_statistics"],
                mae_distribution=analysis_result["mae_statistics"],
                duration_distribution=analysis_result["duration_statistics"],
                excellent_trades=analysis_result["excellent_trades"],
                good_trades=analysis_result["good_trades"],
                poor_trades=analysis_result["poor_trades"],
                average_exit_efficiency=analysis_result["average_exit_efficiency"],
                mfe_capture_ratio=analysis_result["mfe_capture_ratio"],
            )

        except Exception as e:
            self.logger.error(
                f"Failed to get trade metrics for {strategy_name} on {ticker}: {e}"
            )
            raise

    async def _load_trade_history(
        self, strategy_name: str, ticker: str
    ) -> Optional[pd.DataFrame]:
        """
        Load trade history data from available sources

        Args:
            strategy_name: Strategy identifier
            ticker: Asset ticker symbol

        Returns:
            DataFrame with trade history or None if not found
        """
        # Try most common pattern first (actual file structure)
        primary_file = (
            Path("./json/trade_history/") / f"{ticker}_D_{strategy_name}.json"
        )
        if primary_file.exists():
            return await self._load_json_trade_history(primary_file)

        # Fallback to legacy patterns
        fallback_files = [
            Path(self.config.TRADE_HISTORY_PATH) / f"{ticker}_{strategy_name}.json",
            Path(self.config.TRADE_HISTORY_PATH) / f"{strategy_name}_{ticker}.json",
            Path("./csv/positions/") / f"{strategy_name}_{ticker}_positions.csv",
        ]

        for file_path in fallback_files:
            if file_path.exists():
                if file_path.suffix == ".json":
                    return await self._load_json_trade_history(file_path)
                else:
                    return await self._load_csv_trade_history(file_path)

        return None

    async def _load_json_trade_history(self, file_path: Path) -> pd.DataFrame:
        """Load trade history from JSON format"""
        try:
            with open(file_path, "r") as f:
                trade_data = json.load(f)

            # Convert to DataFrame
            if "trades" in trade_data:
                trades_list = trade_data["trades"]
            else:
                trades_list = trade_data  # Assume it's already a list of trades

            df = pd.DataFrame(trades_list)

            # Standardize column names
            df = self._standardize_trade_columns(df)

            return df

        except Exception as e:
            self.logger.error(
                f"Failed to load JSON trade history from {file_path}: {e}"
            )
            raise

    async def _load_csv_trade_history(self, file_path: Path) -> pd.DataFrame:
        """Load trade history from CSV format"""
        try:
            df = pd.read_csv(file_path)

            # Standardize column names
            df = self._standardize_trade_columns(df)

            return df

        except Exception as e:
            self.logger.error(f"Failed to load CSV trade history from {file_path}: {e}")
            raise

    def _standardize_trade_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize trade data column names and formats using centralized MFE/MAE utility"""
        # Non-MFE/MAE column mappings
        column_mappings = {
            "pnl": "return_pct",
            "pnl_pct": "return_pct",
            "return": "return_pct",
            "Return": "return_pct",
            "profit_loss": "return_pct",
            "entry_date": "entry_time",
            "exit_date": "exit_time",
            "open_date": "entry_time",
            "close_date": "exit_time",
            "Entry_Timestamp": "entry_time",
            "Exit_Timestamp": "exit_time",
            "duration_days": "duration",
            "Duration_Days": "duration",
            "holding_period": "duration",
        }

        # Apply non-MFE/MAE mappings first
        df = df.rename(columns=column_mappings)

        # Use centralized MFE/MAE utility for standardization and calculation
        df = standardize_mfe_mae_columns(df)

        # Get centralized calculator for enhanced MFE/MAE handling
        mfe_mae_calculator = get_mfe_mae_calculator(self.logger)

        # If MFE/MAE data is missing or invalid, try to calculate from available data
        if (
            "mfe" not in df.columns
            or "mae" not in df.columns
            or df["mfe"].isna().any()
            or df["mae"].isna().any()
            or (df["mfe"] == 0.0).all()
            and (df["mae"] == 0.0).all()
        ):
            self.logger.info(
                "MFE/MAE data missing or invalid, attempting calculation from trade data"
            )

            # Try to calculate MFE/MAE from available trade data
            try:
                df = mfe_mae_calculator.calculate_from_trades(
                    df,
                    entry_price_col="entry_price"
                    if "entry_price" in df.columns
                    else "Avg Entry Price",
                    exit_price_col="exit_price"
                    if "exit_price" in df.columns
                    else "Avg Exit Price",
                    direction_col="direction"
                    if "direction" in df.columns
                    else "Direction",
                    return_col="return_pct",
                )
                self.logger.debug(
                    f"Successfully calculated MFE/MAE for {len(df)} trades"
                )
            except Exception as e:
                self.logger.warning(f"Failed to calculate MFE/MAE from trade data: {e}")

        # Validate MFE/MAE data consistency using centralized utility
        if "mfe" in df.columns and "mae" in df.columns and "return_pct" in df.columns:
            direction_col = "direction" if "direction" in df.columns else "Direction"
            default_direction = "Long"  # Default assumption if direction not available

            for idx, row in df.iterrows():
                current_return = row.get("return_pct", 0.0)
                mfe = row.get("mfe", 0.0)
                mae = row.get("mae", 0.0)
                direction = row.get(direction_col, default_direction)

                # Validate using centralized utility
                validation_errors = mfe_mae_calculator.validate_mfe_mae(
                    current_return, mfe, mae, direction
                )

                if validation_errors:
                    strategy_id = f"{row.get('strategy_name', 'Unknown')}_{idx}"
                    self.logger.warning(
                        f"MFE/MAE validation issues for {strategy_id}: {validation_errors}"
                    )

                    # Apply corrective measures for common validation failures
                    if "exceeds MFE" in str(validation_errors):
                        # If current return exceeds MFE, adjust MFE to match current return
                        df.at[idx, "mfe"] = (
                            abs(current_return) if current_return > 0 else mfe
                        )

                    if "Negative MFE" in str(
                        validation_errors
                    ) and "positive return" in str(validation_errors):
                        # For positive returns with negative MFE, recalculate MFE
                        if current_return > 0:
                            df.at[idx, "mfe"] = abs(current_return)
                            df.at[idx, "mae"] = 0.0

        # Ensure required columns exist with defaults
        required_columns = {
            "return_pct": 0.0,
            "duration": 1.0,
            "status": "closed",
            "entry_time": None,
            "exit_time": None,
        }

        for col, default_value in required_columns.items():
            if col not in df.columns:
                df[col] = default_value

        # Comprehensive data type conversion with robust error handling and fallbacks
        type_conversions = {
            "return_pct": (pd.to_numeric, 0.0, "Return percentage"),
            "duration": (pd.to_numeric, 1.0, "Trade duration"),
            "mfe": (pd.to_numeric, 0.0, "Maximum Favorable Excursion"),
            "mae": (pd.to_numeric, 0.0, "Maximum Adverse Excursion"),
        }

        for col, (converter, default_value, description) in type_conversions.items():
            if col in df.columns:
                try:
                    # Handle string conversions for JSON data
                    if df[col].dtype == "object":
                        # Remove any non-numeric characters and handle special cases
                        df[col] = (
                            df[col].astype(str).str.replace("[^0-9.-]", "", regex=True)
                        )
                        df[col] = df[col].replace("", default_value)

                    # Convert to numeric with coercion
                    original_values = df[col].copy()
                    df[col] = converter(df[col], errors="coerce")

                    # Fill NaN values with defaults
                    nan_count = df[col].isna().sum()
                    if nan_count > 0:
                        self.logger.debug(
                            f"Found {nan_count} invalid values in {col} ({description}), using default: {default_value}"
                        )
                        df[col] = df[col].fillna(default_value)

                    # Validate reasonable ranges
                    if col in ["mfe", "mae"]:
                        # MFE/MAE should not be negative
                        negative_count = (df[col] < 0).sum()
                        if negative_count > 0:
                            self.logger.warning(
                                f"Found {negative_count} negative values in {col}, converting to absolute values"
                            )
                            df[col] = df[col].abs()

                    elif col == "duration":
                        # Duration should be positive
                        zero_or_negative = (df[col] <= 0).sum()
                        if zero_or_negative > 0:
                            self.logger.warning(
                                f"Found {zero_or_negative} zero/negative duration values, setting to default: {default_value}"
                            )
                            df.loc[df[col] <= 0, col] = default_value

                    self.logger.debug(
                        f"Successfully converted {col} ({description}) to numeric type"
                    )

                except Exception as conversion_error:
                    self.logger.error(
                        f"Failed to convert {col} ({description}) to numeric: {conversion_error}"
                    )
                    self.logger.info(
                        f"Setting all {col} values to default: {default_value}"
                    )
                    df[col] = default_value

        # Handle timestamp columns with fallbacks
        timestamp_columns = ["entry_time", "exit_time"]
        for col in timestamp_columns:
            if col in df.columns and df[col].notna().any():
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                    invalid_timestamps = df[col].isna().sum()
                    if invalid_timestamps > 0:
                        self.logger.debug(
                            f"Found {invalid_timestamps} invalid timestamps in {col}"
                        )
                except Exception as e:
                    self.logger.warning(f"Failed to convert {col} to datetime: {e}")

        # Validate final data integrity
        self._validate_data_integrity(df)

        # Add returns column for convenience
        df["returns"] = df["return_pct"]

        return df

    def _validate_data_integrity(self, df: pd.DataFrame) -> None:
        """Final validation of data integrity after all conversions"""
        try:
            total_rows = len(df)
            if total_rows == 0:
                self.logger.warning("DataFrame is empty after standardization")
                return

            # Check for required columns
            required_cols = ["return_pct", "mfe", "mae"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                self.logger.error(
                    f"Missing critical columns after standardization: {missing_cols}"
                )

            # Validate data types
            numeric_cols = ["return_pct", "mfe", "mae", "duration"]
            for col in numeric_cols:
                if col in df.columns:
                    non_numeric_count = (
                        df[col]
                        .apply(
                            lambda x: not isinstance(
                                x, (int, float, np.integer, np.floating)
                            )
                        )
                        .sum()
                    )
                    if non_numeric_count > 0:
                        self.logger.warning(
                            f"Found {non_numeric_count} non-numeric values in {col} after conversion"
                        )

            # Check for extreme outliers that might indicate data issues
            if "return_pct" in df.columns:
                extreme_returns = (df["return_pct"].abs() > 5.0).sum()  # >500% returns
                if extreme_returns > 0:
                    self.logger.info(
                        f"Found {extreme_returns} trades with extreme returns (>500%)"
                    )

            if "mfe" in df.columns and "mae" in df.columns:
                extreme_mfe = (df["mfe"] > 10.0).sum()  # >1000% MFE
                extreme_mae = (df["mae"] > 10.0).sum()  # >1000% MAE
                if extreme_mfe > 0:
                    self.logger.info(
                        f"Found {extreme_mfe} trades with extreme MFE (>1000%)"
                    )
                if extreme_mae > 0:
                    self.logger.info(
                        f"Found {extreme_mae} trades with extreme MAE (>1000%)"
                    )

            # Summary of data quality
            self.logger.debug(
                f"Data integrity validation complete: {total_rows} rows processed"
            )

        except Exception as e:
            self.logger.error(f"Error during data integrity validation: {e}")

    def _analyze_trade_returns(self, trade_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trade return distributions"""
        returns = trade_data["returns"].dropna()

        if len(returns) == 0:
            # Return empty statistics
            return {
                "statistics": self._create_empty_statistics(),
                "percentiles": self._create_empty_percentiles(),
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
            }

        # Basic statistics
        statistics = self._calculate_statistical_metrics(returns)
        percentiles = self._calculate_percentile_metrics(returns)

        # Trading-specific metrics
        winning_trades = returns[returns > 0]
        losing_trades = returns[returns < 0]

        win_rate = len(winning_trades) / len(returns) if len(returns) > 0 else 0.0

        profit_factor = (
            winning_trades.sum() / abs(losing_trades.sum())
            if len(losing_trades) > 0 and losing_trades.sum() < 0
            else float("inf")
            if len(winning_trades) > 0
            else 0.0
        )

        sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0.0

        # Calculate max drawdown
        cumulative_returns = (1 + returns).cumprod()
        max_drawdown = self._calculate_max_drawdown(cumulative_returns)

        return {
            "statistics": statistics,
            "percentiles": percentiles,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
        }

    def _analyze_mfe_patterns(self, trade_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze Maximum Favorable Excursion patterns"""
        mfe_data = trade_data["mfe"].dropna()

        if len(mfe_data) == 0:
            return {"statistics": self._create_empty_statistics()}

        statistics = self._calculate_statistical_metrics(mfe_data)

        return {"statistics": statistics}

    def _analyze_mae_patterns(self, trade_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze Maximum Adverse Excursion patterns"""
        mae_data = trade_data["mae"].dropna()

        if len(mae_data) == 0:
            return {"statistics": self._create_empty_statistics()}

        # MAE is typically negative, so we take absolute values for analysis
        mae_abs = mae_data.abs()
        statistics = self._calculate_statistical_metrics(mae_abs)

        return {"statistics": statistics}

    def _analyze_trade_durations(self, trade_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trade duration patterns"""
        duration_data = trade_data["duration"].dropna()

        if len(duration_data) == 0:
            return {"statistics": self._create_empty_statistics()}

        statistics = self._calculate_statistical_metrics(duration_data)

        return {"statistics": statistics}

    def _calculate_exit_efficiency(self, trade_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate exit efficiency metrics"""
        try:
            # Filter for closed trades with valid MFE and return data
            closed_trades = trade_data[
                (trade_data["status"] == "closed")
                & (trade_data["mfe"].notna())
                & (trade_data["returns"].notna())
            ]

            if len(closed_trades) == 0:
                return {"average_efficiency": 0.0, "mfe_capture_ratio": 0.0}

            # Calculate efficiency for each trade (return / MFE)
            efficiency_scores = []
            mfe_capture_ratios = []

            for _, trade in closed_trades.iterrows():
                mfe = trade["mfe"]
                trade_return = trade["returns"]

                if mfe > 0:
                    efficiency = min(trade_return / mfe, 1.0)  # Cap at 100%
                    efficiency_scores.append(
                        max(efficiency, 0.0)
                    )  # Ensure non-negative
                    mfe_capture_ratios.append(efficiency)

            average_efficiency = (
                np.mean(efficiency_scores) if efficiency_scores else 0.0
            )
            mfe_capture_ratio = (
                np.mean(mfe_capture_ratios) if mfe_capture_ratios else 0.0
            )

            return {
                "average_efficiency": average_efficiency,
                "mfe_capture_ratio": mfe_capture_ratio,
            }

        except Exception as e:
            self.logger.warning(f"Failed to calculate exit efficiency: {e}")
            return {"average_efficiency": 0.0, "mfe_capture_ratio": 0.0}

    def _assess_trade_quality(self, trade_data: pd.DataFrame) -> Dict[str, int]:
        """Assess trade quality based on returns"""
        returns = trade_data["returns"].dropna()

        excellent_trades = len(returns[returns >= self.excellent_return_threshold])
        good_trades = len(
            returns[
                (returns >= self.good_return_threshold)
                & (returns < self.excellent_return_threshold)
            ]
        )
        poor_trades = len(returns[returns <= self.poor_return_threshold])

        return {
            "excellent_trades": excellent_trades,
            "good_trades": good_trades,
            "poor_trades": poor_trades,
        }

    def _calculate_statistical_metrics(self, data: pd.Series) -> StatisticalMetrics:
        """Calculate statistical metrics for a data series"""
        if len(data) == 0:
            return self._create_empty_statistics()

        return StatisticalMetrics(
            mean=float(data.mean()),
            median=float(data.median()),
            std=float(data.std()),
            min=float(data.min()),
            max=float(data.max()),
            skewness=float(data.skew()) if len(data) > 2 else 0.0,
            kurtosis=float(data.kurtosis()) if len(data) > 3 else 0.0,
            count=len(data),
        )

    def _calculate_percentile_metrics(self, data: pd.Series) -> PercentileMetrics:
        """Calculate percentile metrics for a data series"""
        if len(data) == 0:
            return self._create_empty_percentiles()

        return PercentileMetrics(
            p5=float(data.quantile(0.05)),
            p10=float(data.quantile(0.10)),
            p25=float(data.quantile(0.25)),
            p50=float(data.quantile(0.50)),
            p75=float(data.quantile(0.75)),
            p90=float(data.quantile(0.90)),
            p95=float(data.quantile(0.95)),
            p99=float(data.quantile(0.99)),
        )

    def _calculate_var_metrics(self, data: pd.Series) -> VaRMetrics:
        """Calculate VaR metrics for a data series"""
        if len(data) == 0:
            return VaRMetrics(
                var_95=0.0,
                var_99=0.0,
                expected_shortfall_95=0.0,
                expected_shortfall_99=0.0,
            )

        var_95 = float(data.quantile(0.05))  # 95% VaR (5th percentile)
        var_99 = float(data.quantile(0.01))  # 99% VaR (1st percentile)

        # Calculate expected shortfall (CVaR)
        es_95_data = data[data <= var_95]
        es_99_data = data[data <= var_99]

        es_95 = float(es_95_data.mean()) if len(es_95_data) > 0 else var_95
        es_99 = float(es_99_data.mean()) if len(es_99_data) > 0 else var_99

        return VaRMetrics(
            var_95=var_95,
            var_99=var_99,
            expected_shortfall_95=es_95,
            expected_shortfall_99=es_99,
        )

    def _calculate_max_drawdown(self, cumulative_returns: pd.Series) -> float:
        """Calculate maximum drawdown from cumulative returns"""
        try:
            peak = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - peak) / peak
            return float(drawdown.min())
        except:
            return 0.0

    def _create_empty_statistics(self) -> StatisticalMetrics:
        """Create empty statistical metrics"""
        return StatisticalMetrics(
            mean=0.0,
            median=0.0,
            std=0.0,
            min=0.0,
            max=0.0,
            skewness=0.0,
            kurtosis=0.0,
            count=0,
        )

    def _create_empty_percentiles(self) -> PercentileMetrics:
        """Create empty percentile metrics"""
        return PercentileMetrics(
            p5=0.0, p10=0.0, p25=0.0, p50=0.0, p75=0.0, p90=0.0, p95=0.0, p99=0.0
        )
