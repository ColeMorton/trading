#!/usr/bin/env python3
"""
Strategy Data Analysis Script

This script loads and analyzes two CSV files containing strategy backtest data
using the existing concurrency analysis framework from app/concurrency/.

Files to analyze:
- ./csv/strategies/trades.csv
- ./csv/strategies/incoming.csv

Corresponding JSON enhancement data (if available):
- ./json/concurrency/trades.json
- ./json/concurrency/incoming.json (not found, using None)

The script leverages the existing CSV loading patterns and data processing
infrastructure already established in the codebase.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import polars as pl

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.concurrency.tools.csv_loader import (
    CSVLoader,
    CSVMetricsExtractor,
    CSVValidator,
)
from app.tools.processing import read_large_csv, to_polars


class StrategyDataAnalyzer:
    """
    Analyzer for strategy backtest data using existing concurrency framework.

    This class loads CSV strategy data and optional JSON enhancement data,
    preparing it for quantitative analysis including performance metrics,
    risk assessment, and correlation analysis.
    """

    def __init__(self, log_function: Optional[callable] = None):
        """Initialize the analyzer with optional logging."""
        self.log = log_function or self._default_log
        self.csv_loader = CSVLoader(strict_validation=False)
        self.metrics_extractor = CSVMetricsExtractor(
            aggregation_method="trade_weighted"
        )
        self.validator = CSVValidator()

    def _default_log(self, message: str, level: str = "info"):
        """Default logging function."""
        print(f"[{level.upper()}] {message}")

    def load_csv_file(self, csv_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a CSV file using the existing CSV loader framework.

        Args:
            csv_path: Path to CSV file

        Returns:
            Dictionary containing loaded data and metadata
        """
        csv_path = Path(csv_path)
        self.log(f"Loading CSV file: {csv_path}")

        # Use the existing CSV loader
        load_result = self.csv_loader.load_csv(csv_path, self.log)

        if not load_result.success:
            self.log(f"Failed to load CSV: {load_result.errors}", "error")
            return {
                "success": False,
                "data": None,
                "errors": load_result.errors,
                "warnings": load_result.warnings,
            }

        # Extract metrics using the existing metrics extractor
        csv_metrics = self.metrics_extractor.extract_metrics(load_result.data, self.log)

        # Validate data quality
        validation_results = self.validator.validate_csv_data(
            load_result.data, self.log
        )

        return {
            "success": True,
            "file_path": str(csv_path),
            "data": load_result.data,
            "schema_detected": load_result.schema_detected,
            "rows_loaded": load_result.rows_loaded,
            "columns": load_result.columns_detected,
            "data_quality_score": load_result.data_quality_score,
            "metrics": csv_metrics,
            "validation": validation_results,
            "warnings": load_result.warnings,
            "errors": load_result.errors,
        }

    def load_json_enhancement(
        self, json_path: Union[str, Path]
    ) -> Optional[Dict[str, Any]]:
        """
        Load JSON enhancement data if available.

        Args:
            json_path: Path to JSON file

        Returns:
            JSON data dictionary or None if file doesn't exist
        """
        json_path = Path(json_path)

        if not json_path.exists():
            self.log(f"JSON enhancement file not found: {json_path}", "warning")
            return None

        try:
            with open(json_path, "r") as f:
                data = json.load(f)
            self.log(f"Loaded JSON enhancement data: {json_path}")
            return data
        except Exception as e:
            self.log(f"Error loading JSON file {json_path}: {str(e)}", "error")
            return None

    def analyze_files(
        self,
        csv_files: List[Union[str, Path]],
        json_files: Optional[List[Union[str, Path]]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze multiple CSV files with optional JSON enhancement data.

        Args:
            csv_files: List of CSV file paths
            json_files: Optional list of JSON file paths

        Returns:
            Comprehensive analysis results
        """
        json_files = json_files or []
        results = {
            "analysis_timestamp": pd.Timestamp.now().isoformat(),
            "files_analyzed": [],
            "combined_metrics": {},
            "data_quality": {},
            "summary": {},
        }

        all_data = []

        for i, csv_file in enumerate(csv_files):
            csv_file = Path(csv_file)
            json_file = json_files[i] if i < len(json_files) else None

            self.log(f"Analyzing file {i+1}/{len(csv_files)}: {csv_file.name}")

            # Load CSV data
            csv_result = self.load_csv_file(csv_file)

            # Load JSON enhancement if available
            json_data = None
            if json_file:
                json_data = self.load_json_enhancement(json_file)

            # Store file results
            file_result = {
                "csv_file": str(csv_file),
                "json_file": str(json_file) if json_file else None,
                "csv_data": csv_result,
                "json_enhancement": json_data,
            }
            results["files_analyzed"].append(file_result)

            # Collect data for combined analysis
            if csv_result["success"] and csv_result["data"] is not None:
                # Add file identifier to data
                data_copy = csv_result["data"].copy()
                data_copy["source_file"] = csv_file.stem
                all_data.append(data_copy)

        # Perform combined analysis if we have data
        if all_data:
            self.log("Performing combined analysis across all files...")
            combined_df = pd.concat(all_data, ignore_index=True)

            # Extract combined metrics
            combined_metrics = self.metrics_extractor.extract_metrics(
                combined_df, self.log
            )
            results["combined_metrics"] = {
                "ticker_metrics": combined_metrics.ticker_metrics,
                "portfolio_summary": combined_metrics.portfolio_summary,
                "strategy_breakdown": combined_metrics.strategy_breakdown,
                "extraction_metadata": combined_metrics.extraction_metadata,
            }

            # Overall data quality assessment
            combined_validation = self.validator.validate_csv_data(
                combined_df, self.log
            )
            results["data_quality"] = combined_validation

            # Generate summary statistics
            results["summary"] = self._generate_analysis_summary(
                combined_df, combined_metrics
            )

        return results

    def _generate_analysis_summary(
        self, data: pd.DataFrame, metrics: Any
    ) -> Dict[str, Any]:
        """Generate summary statistics from the combined data."""
        summary = {
            "total_strategies": len(data),
            "unique_tickers": data["Ticker"].nunique()
            if "Ticker" in data.columns
            else 0,
            "unique_strategy_types": data["Strategy Type"].nunique()
            if "Strategy Type" in data.columns
            else 0,
            "total_trades": data["Total Trades"].sum()
            if "Total Trades" in data.columns
            else 0,
        }

        # Performance metrics summary
        if "Win Rate [%]" in data.columns:
            summary["avg_win_rate"] = float(data["Win Rate [%]"].mean())
            summary["win_rate_range"] = [
                float(data["Win Rate [%]"].min()),
                float(data["Win Rate [%]"].max()),
            ]

        if "Total Return [%]" in data.columns:
            summary["avg_total_return"] = float(data["Total Return [%]"].mean())
            summary["return_range"] = [
                float(data["Total Return [%]"].min()),
                float(data["Total Return [%]"].max()),
            ]

        if "Max Drawdown [%]" in data.columns:
            summary["avg_max_drawdown"] = float(data["Max Drawdown [%]"].mean())
            summary["drawdown_range"] = [
                float(data["Max Drawdown [%]"].min()),
                float(data["Max Drawdown [%]"].max()),
            ]

        if "Sharpe Ratio" in data.columns:
            summary["avg_sharpe_ratio"] = float(data["Sharpe Ratio"].mean())
            summary["sharpe_range"] = [
                float(data["Sharpe Ratio"].min()),
                float(data["Sharpe Ratio"].max()),
            ]

        # Risk metrics
        if "Score" in data.columns:
            summary["avg_score"] = float(data["Score"].mean())
            summary["score_range"] = [
                float(data["Score"].min()),
                float(data["Score"].max()),
            ]

        return summary

    def get_data_for_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and prepare data structures for quantitative analysis.

        Args:
            results: Analysis results from analyze_files()

        Returns:
            Dictionary with prepared data for analysis
        """
        analysis_data = {
            "dataframes": {},
            "metrics": {},
            "correlation_data": {},
            "risk_data": {},
            "performance_data": {},
        }

        # Extract individual DataFrames
        for file_result in results["files_analyzed"]:
            if file_result["csv_data"]["success"]:
                file_name = Path(file_result["csv_file"]).stem
                analysis_data["dataframes"][file_name] = file_result["csv_data"]["data"]

        # Combined DataFrame for correlation analysis
        if analysis_data["dataframes"]:
            all_dfs = []
            for name, df in analysis_data["dataframes"].items():
                df_copy = df.copy()
                df_copy["source"] = name
                all_dfs.append(df_copy)
            analysis_data["dataframes"]["combined"] = pd.concat(
                all_dfs, ignore_index=True
            )

        # Extract metrics for analysis
        if "combined_metrics" in results:
            analysis_data["metrics"] = results["combined_metrics"]

        # Prepare correlation analysis data
        combined_df = analysis_data["dataframes"].get("combined")
        if combined_df is not None:
            # Select numeric columns for correlation analysis
            numeric_cols = [
                "Total Return [%]",
                "Win Rate [%]",
                "Sharpe Ratio",
                "Max Drawdown [%]",
                "Profit Factor",
                "Expectancy per Trade",
                "Total Trades",
                "Score",
            ]
            numeric_cols = [col for col in numeric_cols if col in combined_df.columns]

            if numeric_cols:
                analysis_data["correlation_data"] = {
                    "correlation_matrix": combined_df[numeric_cols].corr(),
                    "numeric_data": combined_df[numeric_cols],
                    "column_descriptions": {
                        "Total Return [%]": "Total return percentage",
                        "Win Rate [%]": "Percentage of winning trades",
                        "Sharpe Ratio": "Risk-adjusted return metric",
                        "Max Drawdown [%]": "Maximum drawdown percentage",
                        "Profit Factor": "Ratio of gross profit to gross loss",
                        "Expectancy per Trade": "Expected return per trade",
                        "Total Trades": "Total number of trades executed",
                        "Score": "Overall strategy score",
                    },
                }

        # Prepare risk assessment data
        if combined_df is not None:
            risk_cols = [
                "Max Drawdown [%]",
                "Sharpe Ratio",
                "Sortino Ratio",
                "Calmar Ratio",
                "Value at Risk",
                "Total Return [%]",
                "Annualized Volatility",
            ]
            risk_cols = [col for col in risk_cols if col in combined_df.columns]

            if risk_cols:
                analysis_data["risk_data"] = {
                    "risk_metrics": combined_df[risk_cols],
                    "risk_summary": combined_df[risk_cols].describe(),
                    "high_risk_strategies": combined_df[
                        combined_df["Max Drawdown [%]"] > 50
                    ]
                    if "Max Drawdown [%]" in combined_df.columns
                    else pd.DataFrame(),
                }

        # Prepare performance data
        if combined_df is not None:
            perf_cols = [
                "Total Return [%]",
                "Win Rate [%]",
                "Profit Factor",
                "Expectancy per Trade",
                "Total Trades",
                "Score",
                "Annualized Return",
            ]
            perf_cols = [col for col in perf_cols if col in combined_df.columns]

            if perf_cols:
                analysis_data["performance_data"] = {
                    "performance_metrics": combined_df[perf_cols],
                    "performance_summary": combined_df[perf_cols].describe(),
                    "top_performers": combined_df.nlargest(10, "Score")
                    if "Score" in combined_df.columns
                    else pd.DataFrame(),
                    "strategy_type_performance": combined_df.groupby("Strategy Type")[
                        perf_cols
                    ].mean()
                    if "Strategy Type" in combined_df.columns
                    else pd.DataFrame(),
                }

        return analysis_data


def main():
    """Main execution function."""
    print("Strategy Data Analysis using Concurrency Framework")
    print("=" * 60)

    # Initialize analyzer
    analyzer = StrategyDataAnalyzer()

    # Define file paths
    csv_files = ["./csv/strategies/trades.csv", "./csv/strategies/incoming.csv"]

    json_files = [
        "./json/concurrency/trades.json",
        "./json/concurrency/incoming.json",  # May not exist
    ]

    # Verify CSV files exist
    for csv_file in csv_files:
        if not Path(csv_file).exists():
            print(f"ERROR: CSV file not found: {csv_file}")
            return

    # Perform analysis
    print("Starting analysis...")
    results = analyzer.analyze_files(csv_files, json_files)

    # Display summary
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)

    if "summary" in results:
        summary = results["summary"]
        print(f"Total Strategies Analyzed: {summary.get('total_strategies', 0)}")
        print(f"Unique Tickers: {summary.get('unique_tickers', 0)}")
        print(f"Unique Strategy Types: {summary.get('unique_strategy_types', 0)}")
        print(f"Total Trades: {summary.get('total_trades', 0):,}")

        if "avg_win_rate" in summary:
            print(f"Average Win Rate: {summary['avg_win_rate']:.2f}%")
            print(
                f"Win Rate Range: {summary['win_rate_range'][0]:.2f}% - {summary['win_rate_range'][1]:.2f}%"
            )

        if "avg_total_return" in summary:
            print(f"Average Total Return: {summary['avg_total_return']:.2f}%")
            print(
                f"Return Range: {summary['return_range'][0]:.2f}% - {summary['return_range'][1]:.2f}%"
            )

        if "avg_max_drawdown" in summary:
            print(f"Average Max Drawdown: {summary['avg_max_drawdown']:.2f}%")
            print(
                f"Drawdown Range: {summary['drawdown_range'][0]:.2f}% - {summary['drawdown_range'][1]:.2f}%"
            )

        if "avg_sharpe_ratio" in summary:
            print(f"Average Sharpe Ratio: {summary['avg_sharpe_ratio']:.2f}")
            print(
                f"Sharpe Range: {summary['sharpe_range'][0]:.2f} - {summary['sharpe_range'][1]:.2f}"
            )

    # Display data quality information
    print("\n" + "=" * 60)
    print("DATA QUALITY ASSESSMENT")
    print("=" * 60)

    if "data_quality" in results:
        quality = results["data_quality"]
        print(f"Overall Valid: {quality.get('overall_valid', False)}")
        print(f"Quality Score: {quality.get('quality_score', 0):.2f}")

        if quality.get("warnings"):
            print(f"Warnings: {len(quality['warnings'])}")
            for warning in quality["warnings"][:3]:  # Show first 3 warnings
                print(f"  - {warning}")

        if quality.get("errors"):
            print(f"Errors: {len(quality['errors'])}")
            for error in quality["errors"][:3]:  # Show first 3 errors
                print(f"  - {error}")

    # Prepare data for analysis
    analysis_data = analyzer.get_data_for_analysis(results)

    print("\n" + "=" * 60)
    print("DATA PREPARED FOR ANALYSIS")
    print("=" * 60)

    print("Available DataFrames:")
    for name, df in analysis_data["dataframes"].items():
        print(f"  - {name}: {len(df)} rows, {len(df.columns)} columns")

    if analysis_data["correlation_data"]:
        print(
            f"Correlation analysis ready: {len(analysis_data['correlation_data']['numeric_data'].columns)} metrics"
        )

    if analysis_data["risk_data"]:
        print(
            f"Risk analysis ready: {len(analysis_data['risk_data']['risk_metrics'].columns)} risk metrics"
        )

    if analysis_data["performance_data"]:
        print(
            f"Performance analysis ready: {len(analysis_data['performance_data']['performance_metrics'].columns)} performance metrics"
        )

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print("Data structures are now ready for quantitative analysis.")
    print("Use the returned analysis_data dictionary for further analysis.")

    return results, analysis_data


if __name__ == "__main__":
    results, analysis_data = main()
