#!/usr/bin/env python3
"""
CSV Data Loader Module.

This module provides comprehensive CSV data loading and validation functionality
for Phase 5 of the portfolio metrics fix plan. It treats CSV backtest data as
the source of truth for metrics validation.

Key features:
- Load and validate CSV backtest data
- Extract portfolio metrics from CSV
- Handle multiple CSV formats and schemas
- Provide data quality checks
- Support for ticker-level and portfolio-level aggregation

Classes:
    CSVLoader: Main CSV data loading interface
    CSVMetricsExtractor: Extract portfolio metrics from CSV data
    CSVValidator: Validate CSV data quality and completeness
"""

import os
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import polars as pl


@dataclass
class CSVLoadResult:
    """Result of CSV loading operation."""

    success: bool
    data: Optional[pd.DataFrame]
    schema_detected: str
    rows_loaded: int
    columns_detected: List[str]
    missing_columns: List[str]
    data_quality_score: float
    warnings: List[str]
    errors: List[str]


@dataclass
class CSVMetrics:
    """Portfolio metrics extracted from CSV data."""

    ticker_metrics: Dict[str, Dict[str, float]]
    portfolio_summary: Dict[str, float]
    strategy_breakdown: Dict[str, Dict[str, float]]
    data_quality: Dict[str, Any]
    extraction_metadata: Dict[str, Any]


class CSVLoader:
    """
    Comprehensive CSV data loader for portfolio backtest data.

    This loader treats CSV files as the authoritative source of truth
    for portfolio metrics validation, addressing the data consistency
    issues identified in the portfolio metrics fix plan.
    """

    def __init__(self, strict_validation: bool = True):
        """
        Initialize the CSV loader.

        Args:
            strict_validation: Whether to enforce strict data validation
        """
        self.strict_validation = strict_validation
        self.supported_schemas = {
            "vectorbt_standard": [
                "Ticker",
                "Strategy",
                "Start",
                "End",
                "Duration",
                "Total Return %",
                "Annual Return %",
                "Cumulative Return %",
                "Annual Volatility %",
                "Sharpe Ratio",
                "Calmar Ratio",
                "Max Drawdown %",
                "Total Trades",
                "Win Rate %",
                "Avg Win %",
                "Avg Loss %",
                "Profit Factor",
                "Expectancy per Trade",
            ],
            "vectorbt_extended": [
                "Ticker",
                "Strategy",
                "Start",
                "End",
                "Duration",
                "Total Return %",
                "Annual Return %",
                "Cumulative Return %",
                "Annual Volatility %",
                "Sharpe Ratio",
                "Sortino Ratio",
                "Calmar Ratio",
                "Max Drawdown %",
                "Annual Max Drawdown %",
                "Recovery Factor",
                "Ulcer Index",
                "Value at Risk 95%",
                "Conditional VaR 95%",
                "Total Trades",
                "Win Rate %",
                "Avg Win %",
                "Avg Loss %",
                "Profit Factor",
                "Expectancy per Trade",
                "Kelly Criterion %",
            ],
            "custom_strategy": [
                "Ticker",
                "Strategy",
                "Total Return %",
                "Max Drawdown %",
                "Sharpe Ratio",
                "Total Trades",
                "Win Rate %",
                "Expectancy per Trade",
            ],
        }

    def load_csv(
        self,
        csv_path: Union[str, Path],
        log: Optional[Callable[[str, str], None]] = None,
    ) -> CSVLoadResult:
        """
        Load and validate CSV backtest data.

        Args:
            csv_path: Path to CSV file
            log: Optional logging function

        Returns:
            CSVLoadResult with loaded data and metadata
        """
        csv_path = Path(csv_path)
        warnings_list = []
        errors_list = []

        try:
            if not csv_path.exists():
                return CSVLoadResult(
                    success=False,
                    data=None,
                    schema_detected="unknown",
                    rows_loaded=0,
                    columns_detected=[],
                    missing_columns=[],
                    data_quality_score=0.0,
                    warnings=[],
                    errors=[f"CSV file not found: {csv_path}"],
                )

            # Try to read CSV with different encodings
            encodings = ["utf-8", "latin-1", "cp1252"]
            data = None

            for encoding in encodings:
                try:
                    data = pd.read_csv(csv_path, encoding=encoding)
                    if log:
                        log(f"CSV loaded with {encoding} encoding", "info")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    errors_list.append(f"Error reading with {encoding}: {str(e)}")

            if data is None:
                return CSVLoadResult(
                    success=False,
                    data=None,
                    schema_detected="unknown",
                    rows_loaded=0,
                    columns_detected=[],
                    missing_columns=[],
                    data_quality_score=0.0,
                    warnings=warnings_list,
                    errors=errors_list + ["Failed to read CSV with any encoding"],
                )

            # Detect schema
            schema_detected = self._detect_schema(data.columns.tolist())

            # Validate schema
            expected_columns = self.supported_schemas.get(schema_detected, [])
            missing_columns = [
                col for col in expected_columns if col not in data.columns
            ]

            if missing_columns and self.strict_validation:
                warnings_list.append(f"Missing expected columns: {missing_columns}")

            # Clean and validate data
            data_cleaned = self._clean_data(data, warnings_list, errors_list)

            # Calculate data quality score
            quality_score = self._calculate_data_quality_score(
                data_cleaned, schema_detected
            )

            if log:
                log(
                    f"CSV loaded: {len(data_cleaned)} rows, schema: {schema_detected}, quality: {quality_score:.2f}",
                    "info",
                )
                if missing_columns:
                    log(f"Missing columns: {missing_columns}", "warning")

            return CSVLoadResult(
                success=True,
                data=data_cleaned,
                schema_detected=schema_detected,
                rows_loaded=len(data_cleaned),
                columns_detected=data_cleaned.columns.tolist(),
                missing_columns=missing_columns,
                data_quality_score=quality_score,
                warnings=warnings_list,
                errors=errors_list,
            )

        except Exception as e:
            error_msg = f"Unexpected error loading CSV: {str(e)}"
            if log:
                log(error_msg, "error")

            return CSVLoadResult(
                success=False,
                data=None,
                schema_detected="unknown",
                rows_loaded=0,
                columns_detected=[],
                missing_columns=[],
                data_quality_score=0.0,
                warnings=warnings_list,
                errors=errors_list + [error_msg],
            )

    def _detect_schema(self, columns: List[str]) -> str:
        """
        Detect the schema type based on column names.

        Args:
            columns: List of column names

        Returns:
            Schema type identifier
        """
        best_match = "unknown"
        best_score = 0

        for schema_name, expected_cols in self.supported_schemas.items():
            # Calculate match score as percentage of expected columns present
            matches = sum(1 for col in expected_cols if col in columns)
            score = matches / len(expected_cols)

            if score > best_score:
                best_score = score
                best_match = schema_name

        # Require at least 60% match to detect a schema
        if best_score < 0.6:
            return "unknown"

        return best_match

    def _clean_data(
        self, data: pd.DataFrame, warnings_list: List[str], errors_list: List[str]
    ) -> pd.DataFrame:
        """
        Clean and validate CSV data.

        Args:
            data: Raw DataFrame
            warnings_list: List to append warnings to
            errors_list: List to append errors to

        Returns:
            Cleaned DataFrame
        """
        cleaned_data = data.copy()

        # Remove completely empty rows
        initial_rows = len(cleaned_data)
        cleaned_data = cleaned_data.dropna(how="all")
        dropped_rows = initial_rows - len(cleaned_data)

        if dropped_rows > 0:
            warnings_list.append(f"Dropped {dropped_rows} completely empty rows")

        # Clean percentage columns (remove % signs and convert to float)
        percentage_columns = [col for col in cleaned_data.columns if "%" in col]
        for col in percentage_columns:
            if col in cleaned_data.columns:
                # Convert percentage strings to numeric values
                cleaned_data[col] = pd.to_numeric(
                    cleaned_data[col]
                    .astype(str)
                    .str.replace("%", "")
                    .str.replace(",", ""),
                    errors="coerce",
                )

        # Clean numeric columns
        numeric_columns = [
            "Total Trades",
            "Duration",
            "Sharpe Ratio",
            "Calmar Ratio",
            "Sortino Ratio",
            "Profit Factor",
            "Recovery Factor",
            "Ulcer Index",
        ]

        for col in numeric_columns:
            if col in cleaned_data.columns:
                cleaned_data[col] = pd.to_numeric(cleaned_data[col], errors="coerce")

        # Handle date columns
        date_columns = ["Start", "End"]
        for col in date_columns:
            if col in cleaned_data.columns:
                try:
                    cleaned_data[col] = pd.to_datetime(cleaned_data[col])
                except Exception as e:
                    warnings_list.append(
                        f"Could not parse dates in column {col}: {str(e)}"
                    )

        # Validate data ranges
        self._validate_data_ranges(cleaned_data, warnings_list, errors_list)

        return cleaned_data

    def _validate_data_ranges(
        self, data: pd.DataFrame, warnings_list: List[str], errors_list: List[str]
    ) -> None:
        """
        Validate that data values are within reasonable ranges.

        Args:
            data: DataFrame to validate
            warnings_list: List to append warnings to
            errors_list: List to append errors to
        """
        validations = [
            ("Win Rate %", 0, 100, "Win rates should be between 0% and 100%"),
            ("Max Drawdown %", 0, 100, "Max drawdown should be between 0% and 100%"),
            (
                "Annual Volatility %",
                0,
                1000,
                "Annual volatility should be between 0% and 1000%",
            ),
            (
                "Total Trades",
                0,
                100000,
                "Total trades should be positive and reasonable",
            ),
            ("Profit Factor", 0, 100, "Profit factor should be positive"),
            ("Sharpe Ratio", -10, 10, "Sharpe ratio should be between -10 and 10"),
        ]

        for col, min_val, max_val, message in validations:
            if col in data.columns:
                out_of_range = data[(data[col] < min_val) | (data[col] > max_val)][
                    col
                ].dropna()
                if len(out_of_range) > 0:
                    warnings_list.append(
                        f"{message}. Found {len(out_of_range)} out-of-range values in {col}"
                    )

    def _calculate_data_quality_score(self, data: pd.DataFrame, schema: str) -> float:
        """
        Calculate a data quality score from 0.0 to 1.0.

        Args:
            data: DataFrame to assess
            schema: Detected schema type

        Returns:
            Quality score between 0.0 and 1.0
        """
        if len(data) == 0:
            return 0.0

        scores = []

        # Completeness score (percentage of non-null values)
        total_cells = data.size
        non_null_cells = data.count().sum()
        completeness = non_null_cells / total_cells if total_cells > 0 else 0
        scores.append(completeness)

        # Schema compliance score
        expected_columns = self.supported_schemas.get(schema, [])
        if expected_columns:
            present_columns = [col for col in expected_columns if col in data.columns]
            schema_compliance = len(present_columns) / len(expected_columns)
            scores.append(schema_compliance)

        # Data consistency score (check for reasonable values)
        consistency_checks = 0
        total_checks = 0

        # Check if win rates are reasonable
        if "Win Rate %" in data.columns:
            total_checks += 1
            reasonable_win_rates = data[
                (data["Win Rate %"] >= 0) & (data["Win Rate %"] <= 100)
            ]
            if len(reasonable_win_rates) == len(data.dropna(subset=["Win Rate %"])):
                consistency_checks += 1

        # Check if drawdowns are reasonable
        if "Max Drawdown %" in data.columns:
            total_checks += 1
            reasonable_drawdowns = data[
                (data["Max Drawdown %"] >= 0) & (data["Max Drawdown %"] <= 100)
            ]
            if len(reasonable_drawdowns) == len(data.dropna(subset=["Max Drawdown %"])):
                consistency_checks += 1

        # Check if total trades are positive
        if "Total Trades" in data.columns:
            total_checks += 1
            positive_trades = data[data["Total Trades"] > 0]
            if len(positive_trades) == len(data.dropna(subset=["Total Trades"])):
                consistency_checks += 1

        if total_checks > 0:
            consistency_score = consistency_checks / total_checks
            scores.append(consistency_score)

        # Return average of all scores
        return np.mean(scores) if scores else 0.0


class CSVMetricsExtractor:
    """
    Extract portfolio metrics from CSV backtest data.

    This class provides methods to extract ticker-level and portfolio-level
    metrics from CSV data, treating it as the authoritative source.
    """

    def __init__(self, aggregation_method: str = "weighted"):
        """
        Initialize the metrics extractor.

        Args:
            aggregation_method: Method for aggregating metrics ("weighted", "equal", "trade_weighted")
        """
        self.aggregation_method = aggregation_method

    def extract_metrics(
        self, csv_data: pd.DataFrame, log: Optional[Callable[[str, str], None]] = None
    ) -> CSVMetrics:
        """
        Extract comprehensive metrics from CSV data.

        Args:
            csv_data: Loaded CSV DataFrame
            log: Optional logging function

        Returns:
            CSVMetrics with extracted metrics
        """
        try:
            # Extract ticker-level metrics
            ticker_metrics = self._extract_ticker_metrics(csv_data, log)

            # Calculate portfolio-level summary
            portfolio_summary = self._calculate_portfolio_summary(csv_data, log)

            # Extract strategy breakdown
            strategy_breakdown = self._extract_strategy_breakdown(csv_data, log)

            # Assess data quality
            data_quality = self._assess_data_quality(csv_data, log)

            # Create extraction metadata
            extraction_metadata = {
                "rows_processed": len(csv_data),
                "unique_tickers": (
                    csv_data["Ticker"].nunique() if "Ticker" in csv_data.columns else 0
                ),
                "unique_strategies": (
                    csv_data["Strategy"].nunique()
                    if "Strategy" in csv_data.columns
                    else 0
                ),
                "date_range": self._get_date_range(csv_data),
                "aggregation_method": self.aggregation_method,
            }

            if log:
                log(
                    f"Metrics extracted: {len(ticker_metrics)} tickers, {len(strategy_breakdown)} strategies",
                    "info",
                )

            return CSVMetrics(
                ticker_metrics=ticker_metrics,
                portfolio_summary=portfolio_summary,
                strategy_breakdown=strategy_breakdown,
                data_quality=data_quality,
                extraction_metadata=extraction_metadata,
            )

        except Exception as e:
            error_msg = f"Error extracting metrics from CSV: {str(e)}"
            if log:
                log(error_msg, "error")

            # Return empty metrics on error
            return CSVMetrics(
                ticker_metrics={},
                portfolio_summary={},
                strategy_breakdown={},
                data_quality={"error": error_msg},
                extraction_metadata={"error": error_msg},
            )

    def _extract_ticker_metrics(
        self, csv_data: pd.DataFrame, log: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Dict[str, float]]:
        """Extract metrics aggregated by ticker."""
        if "Ticker" not in csv_data.columns:
            return {}

        ticker_metrics = {}

        for ticker in csv_data["Ticker"].unique():
            ticker_data = csv_data[csv_data["Ticker"] == ticker]

            # Calculate aggregated metrics for this ticker
            metrics = {}

            # Numeric columns to aggregate
            numeric_columns = [
                "Total Return %",
                "Annual Return %",
                "Annual Volatility %",
                "Sharpe Ratio",
                "Max Drawdown %",
                "Win Rate %",
                "Profit Factor",
                "Expectancy per Trade",
                "Total Trades",
            ]

            for col in numeric_columns:
                if col in ticker_data.columns:
                    # Use different aggregation methods based on column type
                    if col == "Total Trades":
                        # Sum total trades
                        metrics[
                            col.lower().replace(" ", "_").replace("%", "_pct")
                        ] = float(ticker_data[col].sum())
                    elif col in ["Max Drawdown %"]:
                        # Use maximum for drawdown
                        metrics[
                            col.lower().replace(" ", "_").replace("%", "_pct")
                        ] = float(ticker_data[col].max())
                    else:
                        # Use weighted average for other metrics
                        if (
                            self.aggregation_method == "trade_weighted"
                            and "Total Trades" in ticker_data.columns
                        ):
                            weights = ticker_data["Total Trades"]
                            weighted_avg = np.average(
                                ticker_data[col].dropna(),
                                weights=weights[ticker_data[col].notna()],
                            )
                            metrics[
                                col.lower().replace(" ", "_").replace("%", "_pct")
                            ] = float(weighted_avg)
                        else:
                            # Simple average
                            metrics[
                                col.lower().replace(" ", "_").replace("%", "_pct")
                            ] = float(ticker_data[col].mean())

            ticker_metrics[ticker] = metrics

        return ticker_metrics

    def _calculate_portfolio_summary(
        self, csv_data: pd.DataFrame, log: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, float]:
        """Calculate portfolio-level summary metrics."""
        summary = {}

        # Total metrics
        if "Total Trades" in csv_data.columns:
            summary["total_trades"] = float(csv_data["Total Trades"].sum())

        # Weighted averages
        numeric_columns = [
            "Total Return %",
            "Annual Return %",
            "Annual Volatility %",
            "Sharpe Ratio",
            "Win Rate %",
            "Profit Factor",
            "Expectancy per Trade",
        ]

        for col in numeric_columns:
            if col in csv_data.columns:
                if (
                    self.aggregation_method == "trade_weighted"
                    and "Total Trades" in csv_data.columns
                ):
                    weights = csv_data["Total Trades"]
                    weighted_avg = np.average(
                        csv_data[col].dropna(), weights=weights[csv_data[col].notna()]
                    )
                    summary[col.lower().replace(" ", "_").replace("%", "_pct")] = float(
                        weighted_avg
                    )
                else:
                    summary[col.lower().replace(" ", "_").replace("%", "_pct")] = float(
                        csv_data[col].mean()
                    )

        # Maximum drawdown (worst case across all strategies)
        if "Max Drawdown %" in csv_data.columns:
            summary["max_drawdown_pct"] = float(csv_data["Max Drawdown %"].max())

        # Portfolio diversity metrics
        if "Ticker" in csv_data.columns:
            summary["unique_tickers"] = float(csv_data["Ticker"].nunique())

        if "Strategy" in csv_data.columns:
            summary["unique_strategies"] = float(csv_data["Strategy"].nunique())

        return summary

    def _extract_strategy_breakdown(
        self, csv_data: pd.DataFrame, log: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Dict[str, float]]:
        """Extract metrics broken down by strategy."""
        if "Strategy" not in csv_data.columns:
            return {}

        strategy_metrics = {}

        for strategy in csv_data["Strategy"].unique():
            strategy_data = csv_data[csv_data["Strategy"] == strategy]

            metrics = {}

            # Aggregate numeric columns
            numeric_columns = [
                "Total Return %",
                "Annual Return %",
                "Annual Volatility %",
                "Sharpe Ratio",
                "Max Drawdown %",
                "Win Rate %",
                "Profit Factor",
                "Expectancy per Trade",
                "Total Trades",
            ]

            for col in numeric_columns:
                if col in strategy_data.columns:
                    if col == "Total Trades":
                        metrics[
                            col.lower().replace(" ", "_").replace("%", "_pct")
                        ] = float(strategy_data[col].sum())
                    elif col == "Max Drawdown %":
                        metrics[
                            col.lower().replace(" ", "_").replace("%", "_pct")
                        ] = float(strategy_data[col].max())
                    else:
                        metrics[
                            col.lower().replace(" ", "_").replace("%", "_pct")
                        ] = float(strategy_data[col].mean())

            # Add strategy-specific metrics
            if "Ticker" in strategy_data.columns:
                metrics["tickers_covered"] = float(strategy_data["Ticker"].nunique())

            strategy_metrics[strategy] = metrics

        return strategy_metrics

    def _assess_data_quality(
        self, csv_data: pd.DataFrame, log: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        """Assess data quality of the CSV data."""
        quality = {}

        # Completeness metrics
        total_cells = csv_data.size
        non_null_cells = csv_data.count().sum()
        quality["completeness_ratio"] = (
            float(non_null_cells / total_cells) if total_cells > 0 else 0.0
        )

        # Coverage metrics
        quality["row_count"] = len(csv_data)
        quality["column_count"] = len(csv_data.columns)

        # Value range validations
        validations = {}

        if "Win Rate %" in csv_data.columns:
            win_rates = csv_data["Win Rate %"].dropna()
            validations["win_rate_valid"] = (
                float(
                    len(win_rates[(win_rates >= 0) & (win_rates <= 100)])
                    / len(win_rates)
                )
                if len(win_rates) > 0
                else 1.0
            )

        if "Max Drawdown %" in csv_data.columns:
            drawdowns = csv_data["Max Drawdown %"].dropna()
            validations["drawdown_valid"] = (
                float(
                    len(drawdowns[(drawdowns >= 0) & (drawdowns <= 100)])
                    / len(drawdowns)
                )
                if len(drawdowns) > 0
                else 1.0
            )

        if "Total Trades" in csv_data.columns:
            trades = csv_data["Total Trades"].dropna()
            validations["trades_valid"] = (
                float(len(trades[trades > 0]) / len(trades)) if len(trades) > 0 else 1.0
            )

        quality["validation_scores"] = validations
        quality["overall_quality"] = (
            float(np.mean(list(validations.values()))) if validations else 1.0
        )

        return quality

    def _get_date_range(self, csv_data: pd.DataFrame) -> Dict[str, str]:
        """Get date range from CSV data."""
        date_range = {}

        if "Start" in csv_data.columns:
            try:
                start_dates = pd.to_datetime(csv_data["Start"].dropna())
                if len(start_dates) > 0:
                    date_range["earliest_start"] = str(start_dates.min())
                    date_range["latest_start"] = str(start_dates.max())
            except Exception:
                pass

        if "End" in csv_data.columns:
            try:
                end_dates = pd.to_datetime(csv_data["End"].dropna())
                if len(end_dates) > 0:
                    date_range["earliest_end"] = str(end_dates.min())
                    date_range["latest_end"] = str(end_dates.max())
            except Exception:
                pass

        return date_range


class CSVValidator:
    """
    Validate CSV data quality and consistency.

    This class provides comprehensive validation of CSV data to ensure
    it meets quality standards for use as source of truth.
    """

    def __init__(self, tolerance_levels: Dict[str, float] = None):
        """
        Initialize the CSV validator.

        Args:
            tolerance_levels: Custom tolerance levels for validation
        """
        self.tolerance_levels = tolerance_levels or {
            "completeness_threshold": 0.8,
            "win_rate_bounds": (0, 100),
            "drawdown_bounds": (0, 100),
            "sharpe_bounds": (-10, 10),
            "trades_minimum": 1,
        }

    def validate_csv_data(
        self, csv_data: pd.DataFrame, log: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive validation of CSV data.

        Args:
            csv_data: DataFrame to validate
            log: Optional logging function

        Returns:
            Validation results dictionary
        """
        validation_results = {
            "overall_valid": True,
            "checks_performed": [],
            "warnings": [],
            "errors": [],
            "quality_score": 0.0,
        }

        try:
            # Check data completeness
            self._check_completeness(csv_data, validation_results, log)

            # Check data ranges
            self._check_data_ranges(csv_data, validation_results, log)

            # Check data consistency
            self._check_data_consistency(csv_data, validation_results, log)

            # Check for duplicates
            self._check_duplicates(csv_data, validation_results, log)

            # Calculate overall quality score
            validation_results["quality_score"] = self._calculate_quality_score(
                validation_results
            )

            # Determine overall validity
            validation_results["overall_valid"] = (
                len(validation_results["errors"]) == 0
                and validation_results["quality_score"] >= 0.7
            )

            if log:
                status = "VALID" if validation_results["overall_valid"] else "INVALID"
                log(
                    f"CSV validation completed: {status} (quality: {validation_results['quality_score']:.2f})",
                    "info",
                )

        except Exception as e:
            validation_results["overall_valid"] = False
            validation_results["errors"].append(f"Validation error: {str(e)}")
            if log:
                log(f"CSV validation failed: {str(e)}", "error")

        return validation_results

    def _check_completeness(
        self,
        csv_data: pd.DataFrame,
        results: Dict[str, Any],
        log: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        """Check data completeness."""
        results["checks_performed"].append("completeness")

        if len(csv_data) == 0:
            results["errors"].append("CSV data is empty")
            return

        # Check overall completeness
        total_cells = csv_data.size
        non_null_cells = csv_data.count().sum()
        completeness = non_null_cells / total_cells if total_cells > 0 else 0

        if completeness < self.tolerance_levels["completeness_threshold"]:
            results["warnings"].append(
                f"Data completeness below threshold: {completeness:.2%}"
            )

        # Check for completely missing critical columns
        critical_columns = [
            "Ticker",
            "Total Return %",
            "Max Drawdown %",
            "Total Trades",
        ]
        for col in critical_columns:
            if col in csv_data.columns and csv_data[col].isna().all():
                results["errors"].append(f"Critical column {col} is completely empty")

    def _check_data_ranges(
        self,
        csv_data: pd.DataFrame,
        results: Dict[str, Any],
        log: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        """Check that data values are within reasonable ranges."""
        results["checks_performed"].append("data_ranges")

        range_checks = [
            ("Win Rate %", self.tolerance_levels["win_rate_bounds"]),
            ("Max Drawdown %", self.tolerance_levels["drawdown_bounds"]),
            ("Sharpe Ratio", self.tolerance_levels["sharpe_bounds"]),
        ]

        for col, (min_val, max_val) in range_checks:
            if col in csv_data.columns:
                out_of_range = csv_data[
                    (csv_data[col] < min_val) | (csv_data[col] > max_val)
                ][col].dropna()
                if len(out_of_range) > 0:
                    results["warnings"].append(
                        f"{col}: {len(out_of_range)} values out of range [{min_val}, {max_val}]"
                    )

        # Check minimum trades
        if "Total Trades" in csv_data.columns:
            low_trades = csv_data[
                csv_data["Total Trades"] < self.tolerance_levels["trades_minimum"]
            ]
            if len(low_trades) > 0:
                results["warnings"].append(
                    f"Total Trades: {len(low_trades)} entries below minimum threshold"
                )

    def _check_data_consistency(
        self,
        csv_data: pd.DataFrame,
        results: Dict[str, Any],
        log: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        """Check internal data consistency."""
        results["checks_performed"].append("data_consistency")

        # Check if win rate and profit factor are consistent
        if "Win Rate %" in csv_data.columns and "Profit Factor" in csv_data.columns:
            inconsistent = csv_data[
                ((csv_data["Win Rate %"] > 50) & (csv_data["Profit Factor"] < 0.8))
                | ((csv_data["Win Rate %"] < 40) & (csv_data["Profit Factor"] > 1.5))
            ]
            if len(inconsistent) > 0:
                results["warnings"].append(
                    f"Win rate and profit factor inconsistency in {len(inconsistent)} entries"
                )

        # Check if positive returns have negative Sharpe ratios
        if "Total Return %" in csv_data.columns and "Sharpe Ratio" in csv_data.columns:
            inconsistent_sharpe = csv_data[
                ((csv_data["Total Return %"] > 10) & (csv_data["Sharpe Ratio"] < -0.1))
                | (
                    (csv_data["Total Return %"] < -10)
                    & (csv_data["Sharpe Ratio"] > 0.1)
                )
            ]
            if len(inconsistent_sharpe) > 0:
                results["warnings"].append(
                    f"Return and Sharpe ratio inconsistency in {len(inconsistent_sharpe)} entries"
                )

    def _check_duplicates(
        self,
        csv_data: pd.DataFrame,
        results: Dict[str, Any],
        log: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        """Check for duplicate entries."""
        results["checks_performed"].append("duplicates")

        if "Ticker" in csv_data.columns and "Strategy" in csv_data.columns:
            duplicates = csv_data.duplicated(subset=["Ticker", "Strategy"])
            if duplicates.any():
                results["warnings"].append(
                    f"Found {duplicates.sum()} duplicate Ticker-Strategy combinations"
                )

    def _calculate_quality_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall data quality score."""
        # Start with perfect score
        score = 1.0

        # Deduct for errors (more severe)
        score -= len(results["errors"]) * 0.2

        # Deduct for warnings (less severe)
        score -= len(results["warnings"]) * 0.05

        # Ensure score is non-negative
        return max(0.0, score)
