"""
Portfolio Data Export Service

Service for extracting and exporting raw data from VectorBT portfolios
to enable external chart generation and custom analysis.
"""

import json
import os
import pickle
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import polars as pl
import vectorbt as vbt


class ExportFormat(Enum):
    """Supported export formats."""

    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    PICKLE = "pickle"


class DataType(Enum):
    """Available data types for export."""

    PORTFOLIO_VALUE = "portfolio_value"
    RETURNS = "returns"
    TRADES = "trades"
    ORDERS = "orders"
    POSITIONS = "positions"
    STATISTICS = "statistics"
    PRICE_DATA = "prices"
    DRAWDOWNS = "drawdowns"
    CUMULATIVE_RETURNS = "cumulative_returns"
    ALL = "all"


@dataclass
class ExportConfig:
    """Configuration for portfolio data export."""

    output_dir: str = "data/outputs/portfolio/raw_data"
    export_formats: List[ExportFormat] = field(
        default_factory=lambda: [ExportFormat.CSV, ExportFormat.JSON]
    )
    data_types: List[DataType] = field(default_factory=lambda: [DataType.ALL])
    include_vectorbt_object: bool = False
    filename_prefix: str = ""
    filename_suffix: str = ""
    compress: bool = False

    def __post_init__(self):
        """Validate and normalize configuration."""
        if DataType.ALL in self.data_types:
            self.data_types = [
                DataType.PORTFOLIO_VALUE,
                DataType.RETURNS,
                DataType.TRADES,
                DataType.ORDERS,
                DataType.POSITIONS,
                DataType.STATISTICS,
                DataType.PRICE_DATA,
                DataType.DRAWDOWNS,
                DataType.CUMULATIVE_RETURNS,
            ]


@dataclass
class ExportResults:
    """Results from portfolio data export."""

    exported_files: Dict[str, List[str]] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None
    total_files: int = 0

    def add_file(self, data_type: str, file_path: str):
        """Add exported file to results."""
        if data_type not in self.exported_files:
            self.exported_files[data_type] = []
        self.exported_files[data_type].append(file_path)
        self.total_files += 1


class PortfolioDataExportService:
    """
    Service for extracting and exporting comprehensive raw data from VectorBT portfolios.

    Provides access to all underlying data used in portfolio visualization including:
    - Portfolio value series (equity curves)
    - Returns data (daily, cumulative)
    - Trade records with P&L details
    - Order history with entry/exit information
    - Position data with sizing and duration
    - Performance statistics and metrics
    - Price data from backtests
    - Drawdown calculations
    - Optional VectorBT object preservation
    """

    def __init__(self, config: ExportConfig = None, logger=None):
        """Initialize portfolio data export service."""
        self.config = config or ExportConfig()
        self.logger = logger

    def export_portfolio_data(
        self,
        portfolio: "vbt.Portfolio",
        portfolio_name: str,
        benchmark_portfolio: Optional["vbt.Portfolio"] = None,
    ) -> ExportResults:
        """
        Export comprehensive raw data from VectorBT portfolio.

        Args:
            portfolio: Main VectorBT portfolio object
            portfolio_name: Name for exported files
            benchmark_portfolio: Optional benchmark portfolio

        Returns:
            ExportResults with information about exported files
        """
        try:
            # Create output directory
            os.makedirs(self.config.output_dir, exist_ok=True)

            results = ExportResults()

            # Generate base filename
            base_filename = self._generate_filename(portfolio_name)

            # Export each requested data type
            for data_type in self.config.data_types:
                try:
                    if data_type == DataType.PORTFOLIO_VALUE:
                        self._export_portfolio_value(portfolio, base_filename, results)
                    elif data_type == DataType.RETURNS:
                        self._export_returns(portfolio, base_filename, results)
                    elif data_type == DataType.TRADES:
                        self._export_trades(portfolio, base_filename, results)
                    elif data_type == DataType.ORDERS:
                        self._export_orders(portfolio, base_filename, results)
                    elif data_type == DataType.POSITIONS:
                        self._export_positions(portfolio, base_filename, results)
                    elif data_type == DataType.STATISTICS:
                        self._export_statistics(portfolio, base_filename, results)
                    elif data_type == DataType.PRICE_DATA:
                        self._export_prices(portfolio, base_filename, results)
                    elif data_type == DataType.DRAWDOWNS:
                        self._export_drawdowns(portfolio, base_filename, results)
                    elif data_type == DataType.CUMULATIVE_RETURNS:
                        self._export_cumulative_returns(
                            portfolio, base_filename, results
                        )

                except Exception as e:
                    self._log(f"Error exporting {data_type.value}: {str(e)}", "warning")

            # Export benchmark data if provided
            if benchmark_portfolio:
                benchmark_filename = self._generate_filename(
                    f"{portfolio_name}_benchmark"
                )
                self._export_benchmark_data(
                    benchmark_portfolio, benchmark_filename, results
                )

            # Export VectorBT object if requested
            if self.config.include_vectorbt_object:
                self._export_vectorbt_object(portfolio, base_filename, results)
                if benchmark_portfolio:
                    self._export_vectorbt_object(
                        benchmark_portfolio, benchmark_filename, results
                    )

            # Export metadata
            self._export_metadata(portfolio, portfolio_name, base_filename, results)

            self._log(
                f"Successfully exported {results.total_files} files for {portfolio_name}"
            )
            return results

        except Exception as e:
            self._log(f"Error exporting portfolio data: {str(e)}", "error")
            return ExportResults(success=False, error_message=str(e))

    def _export_portfolio_value(
        self, portfolio: "vbt.Portfolio", base_filename: str, results: ExportResults
    ):
        """Export portfolio value series (equity curve)."""
        try:
            value_series = portfolio.value()

            # Convert to DataFrame
            df = pd.DataFrame(
                {
                    "Date": value_series.index,
                    "Portfolio_Value": value_series.values,
                    "Normalized_Value": value_series.values / value_series.values[0],
                }
            ).set_index("Date")

            # Export in requested formats
            for format_type in self.config.export_formats:
                filename = f"{base_filename}_portfolio_value.{format_type.value}"
                file_path = os.path.join(self.config.output_dir, filename)

                if format_type == ExportFormat.CSV:
                    df.to_csv(file_path)
                elif format_type == ExportFormat.JSON:
                    df.reset_index().to_json(
                        file_path, orient="records", date_format="iso"
                    )
                elif format_type == ExportFormat.PARQUET:
                    df.to_parquet(file_path)

                results.add_file(DataType.PORTFOLIO_VALUE.value, file_path)

        except Exception as e:
            self._log(f"Error exporting portfolio value: {str(e)}", "warning")

    def _export_returns(
        self, portfolio: "vbt.Portfolio", base_filename: str, results: ExportResults
    ):
        """Export returns data."""
        try:
            returns = portfolio.returns()

            # Convert to DataFrame
            df = pd.DataFrame(
                {
                    "Date": returns.index,
                    "Returns": returns.values,
                    "Returns_Pct": returns.values * 100,
                }
            ).set_index("Date")

            # Export in requested formats
            for format_type in self.config.export_formats:
                filename = f"{base_filename}_returns.{format_type.value}"
                file_path = os.path.join(self.config.output_dir, filename)

                if format_type == ExportFormat.CSV:
                    df.to_csv(file_path)
                elif format_type == ExportFormat.JSON:
                    df.reset_index().to_json(
                        file_path, orient="records", date_format="iso"
                    )
                elif format_type == ExportFormat.PARQUET:
                    df.to_parquet(file_path)

                results.add_file(DataType.RETURNS.value, file_path)

        except Exception as e:
            self._log(f"Error exporting returns: {str(e)}", "warning")

    def _export_cumulative_returns(
        self, portfolio: "vbt.Portfolio", base_filename: str, results: ExportResults
    ):
        """Export cumulative returns data."""
        try:
            returns = portfolio.returns()
            cumulative_returns = returns.cumsum()

            # Convert to DataFrame
            df = pd.DataFrame(
                {
                    "Date": cumulative_returns.index,
                    "Cumulative_Returns": cumulative_returns.values,
                    "Cumulative_Returns_Pct": cumulative_returns.values * 100,
                }
            ).set_index("Date")

            # Export in requested formats
            for format_type in self.config.export_formats:
                filename = f"{base_filename}_cumulative_returns.{format_type.value}"
                file_path = os.path.join(self.config.output_dir, filename)

                if format_type == ExportFormat.CSV:
                    df.to_csv(file_path)
                elif format_type == ExportFormat.JSON:
                    df.reset_index().to_json(
                        file_path, orient="records", date_format="iso"
                    )
                elif format_type == ExportFormat.PARQUET:
                    df.to_parquet(file_path)

                results.add_file(DataType.CUMULATIVE_RETURNS.value, file_path)

        except Exception as e:
            self._log(f"Error exporting cumulative returns: {str(e)}", "warning")

    def _export_drawdowns(
        self, portfolio: "vbt.Portfolio", base_filename: str, results: ExportResults
    ):
        """Export drawdown calculations."""
        try:
            portfolio_value = portfolio.value()
            cummax = portfolio_value.expanding().max()
            drawdowns = (portfolio_value - cummax) / cummax
            drawdowns_pct = drawdowns * 100

            # Convert to DataFrame
            df = pd.DataFrame(
                {
                    "Date": drawdowns.index,
                    "Drawdown": drawdowns.values,
                    "Drawdown_Pct": drawdowns_pct.values,
                    "Peak_Value": cummax.values,
                    "Current_Value": portfolio_value.values,
                }
            ).set_index("Date")

            # Export in requested formats
            for format_type in self.config.export_formats:
                filename = f"{base_filename}_drawdowns.{format_type.value}"
                file_path = os.path.join(self.config.output_dir, filename)

                if format_type == ExportFormat.CSV:
                    df.to_csv(file_path)
                elif format_type == ExportFormat.JSON:
                    df.reset_index().to_json(
                        file_path, orient="records", date_format="iso"
                    )
                elif format_type == ExportFormat.PARQUET:
                    df.to_parquet(file_path)

                results.add_file(DataType.DRAWDOWNS.value, file_path)

        except Exception as e:
            self._log(f"Error exporting drawdowns: {str(e)}", "warning")

    def _export_trades(
        self, portfolio: "vbt.Portfolio", base_filename: str, results: ExportResults
    ):
        """Export trade records."""
        try:
            trades = portfolio.trades()

            # Handle different VectorBT versions and API changes
            trades_df = None
            if hasattr(trades, "records_readable"):
                trades_df = trades.records_readable
            elif hasattr(trades, "records"):
                trades_df = trades.records
            elif hasattr(trades, "to_pandas"):
                trades_df = trades.to_pandas()
            else:
                # Fallback: try to convert to dataframe
                trades_df = pd.DataFrame(trades)

            if trades_df is None or trades_df.empty:
                self._log(
                    "No trade data available or trades dataframe is empty", "info"
                )
                return

            # Export in requested formats
            for format_type in self.config.export_formats:
                filename = f"{base_filename}_trades.{format_type.value}"
                file_path = os.path.join(self.config.output_dir, filename)

                if format_type == ExportFormat.CSV:
                    trades_df.to_csv(file_path, index=False)
                elif format_type == ExportFormat.JSON:
                    trades_df.to_json(file_path, orient="records", date_format="iso")
                elif format_type == ExportFormat.PARQUET:
                    trades_df.to_parquet(file_path, index=False)

                results.add_file(DataType.TRADES.value, file_path)

        except Exception as e:
            self._log(f"Error exporting trades: {str(e)}", "warning")

    def _export_orders(
        self, portfolio: "vbt.Portfolio", base_filename: str, results: ExportResults
    ):
        """Export order records."""
        try:
            orders = portfolio.orders()

            # Handle different VectorBT versions and API changes
            orders_df = None
            if hasattr(orders, "records_readable"):
                orders_df = orders.records_readable
            elif hasattr(orders, "records"):
                orders_df = orders.records
            elif hasattr(orders, "to_pandas"):
                orders_df = orders.to_pandas()
            else:
                # Fallback: try to convert to dataframe
                orders_df = pd.DataFrame(orders)

            if orders_df is None or orders_df.empty:
                self._log(
                    "No order data available or orders dataframe is empty", "info"
                )
                return

            # Export in requested formats
            for format_type in self.config.export_formats:
                filename = f"{base_filename}_orders.{format_type.value}"
                file_path = os.path.join(self.config.output_dir, filename)

                if format_type == ExportFormat.CSV:
                    orders_df.to_csv(file_path, index=False)
                elif format_type == ExportFormat.JSON:
                    orders_df.to_json(file_path, orient="records", date_format="iso")
                elif format_type == ExportFormat.PARQUET:
                    orders_df.to_parquet(file_path, index=False)

                results.add_file(DataType.ORDERS.value, file_path)

        except Exception as e:
            self._log(f"Error exporting orders: {str(e)}", "warning")

    def _export_positions(
        self, portfolio: "vbt.Portfolio", base_filename: str, results: ExportResults
    ):
        """Export position records."""
        try:
            positions = portfolio.positions()

            # Handle different VectorBT versions and API changes
            positions_df = None
            if hasattr(positions, "records_readable"):
                positions_df = positions.records_readable
            elif hasattr(positions, "records"):
                positions_df = positions.records
            elif hasattr(positions, "to_pandas"):
                positions_df = positions.to_pandas()
            else:
                # Fallback: try to convert to dataframe
                positions_df = pd.DataFrame(positions)

            if positions_df is None or positions_df.empty:
                self._log(
                    "No position data available or positions dataframe is empty", "info"
                )
                return

            # Export in requested formats
            for format_type in self.config.export_formats:
                filename = f"{base_filename}_positions.{format_type.value}"
                file_path = os.path.join(self.config.output_dir, filename)

                if format_type == ExportFormat.CSV:
                    positions_df.to_csv(file_path, index=False)
                elif format_type == ExportFormat.JSON:
                    positions_df.to_json(file_path, orient="records", date_format="iso")
                elif format_type == ExportFormat.PARQUET:
                    positions_df.to_parquet(file_path, index=False)

                results.add_file(DataType.POSITIONS.value, file_path)

        except Exception as e:
            self._log(f"Error exporting positions: {str(e)}", "warning")

    def _export_statistics(
        self, portfolio: "vbt.Portfolio", base_filename: str, results: ExportResults
    ):
        """Export portfolio statistics."""
        try:
            stats = portfolio.stats()

            # Convert to dictionary format
            if hasattr(stats, "to_dict"):
                stats_dict = stats.to_dict()
            else:
                stats_dict = dict(stats)

            # Export in requested formats
            for format_type in self.config.export_formats:
                filename = f"{base_filename}_statistics.{format_type.value}"
                file_path = os.path.join(self.config.output_dir, filename)

                if format_type == ExportFormat.CSV:
                    pd.DataFrame(
                        list(stats_dict.items()), columns=["Metric", "Value"]
                    ).to_csv(file_path, index=False)
                elif format_type == ExportFormat.JSON:
                    with open(file_path, "w") as f:
                        json.dump(stats_dict, f, indent=2, default=str)
                elif format_type == ExportFormat.PARQUET:
                    pd.DataFrame(
                        list(stats_dict.items()), columns=["Metric", "Value"]
                    ).to_parquet(file_path, index=False)

                results.add_file(DataType.STATISTICS.value, file_path)

        except Exception as e:
            self._log(f"Error exporting statistics: {str(e)}", "warning")

    def _export_prices(
        self, portfolio: "vbt.Portfolio", base_filename: str, results: ExportResults
    ):
        """Export underlying price data."""
        try:
            # Get close prices from portfolio
            close_data = portfolio.close

            # Convert to DataFrame if Series
            if hasattr(close_data, "to_frame"):
                price_df = close_data.to_frame("Close")
            else:
                price_df = close_data

            # Reset index to make Date a column
            price_df = price_df.reset_index()

            # Export in requested formats
            for format_type in self.config.export_formats:
                filename = f"{base_filename}_prices.{format_type.value}"
                file_path = os.path.join(self.config.output_dir, filename)

                if format_type == ExportFormat.CSV:
                    price_df.to_csv(file_path, index=False)
                elif format_type == ExportFormat.JSON:
                    price_df.to_json(file_path, orient="records", date_format="iso")
                elif format_type == ExportFormat.PARQUET:
                    price_df.to_parquet(file_path, index=False)

                results.add_file(DataType.PRICE_DATA.value, file_path)

        except Exception as e:
            self._log(f"Error exporting price data: {str(e)}", "warning")

    def _export_benchmark_data(
        self,
        benchmark_portfolio: "vbt.Portfolio",
        benchmark_filename: str,
        results: ExportResults,
    ):
        """Export benchmark portfolio data."""
        try:
            # Export key benchmark data
            value_series = benchmark_portfolio.value()
            returns_series = benchmark_portfolio.returns()

            # Create combined benchmark DataFrame
            df = pd.DataFrame(
                {
                    "Date": value_series.index,
                    "Benchmark_Value": value_series.values,
                    "Benchmark_Returns": returns_series.values,
                    "Benchmark_Normalized_Value": value_series.values
                    / value_series.values[0],
                    "Benchmark_Cumulative_Returns": returns_series.cumsum().values,
                }
            ).set_index("Date")

            # Export in requested formats
            for format_type in self.config.export_formats:
                filename = f"{benchmark_filename}.{format_type.value}"
                file_path = os.path.join(self.config.output_dir, filename)

                if format_type == ExportFormat.CSV:
                    df.to_csv(file_path)
                elif format_type == ExportFormat.JSON:
                    df.reset_index().to_json(
                        file_path, orient="records", date_format="iso"
                    )
                elif format_type == ExportFormat.PARQUET:
                    df.to_parquet(file_path)

                results.add_file("benchmark", file_path)

        except Exception as e:
            self._log(f"Error exporting benchmark data: {str(e)}", "warning")

    def _export_vectorbt_object(
        self, portfolio: "vbt.Portfolio", base_filename: str, results: ExportResults
    ):
        """Export VectorBT portfolio object for full functionality preservation."""
        try:
            filename = f"{base_filename}_vectorbt_portfolio.pickle"
            file_path = os.path.join(self.config.output_dir, filename)

            # Try different approaches to handle VectorBT object serialization
            try:
                # First attempt: Direct pickle
                with open(file_path, "wb") as f:
                    pickle.dump(portfolio, f, protocol=pickle.HIGHEST_PROTOCOL)
                results.add_file("vectorbt_object", file_path)
                self._log("VectorBT object exported successfully using direct pickle")
                return
            except Exception as pickle_error:
                self._log(f"Direct pickle failed: {pickle_error}", "debug")

            # Second attempt: Export the essential portfolio components
            try:
                portfolio_data = {
                    "close": portfolio.close,
                    "orders": portfolio.orders().records
                    if hasattr(portfolio.orders(), "records")
                    else None,
                    "trades": portfolio.trades().records
                    if hasattr(portfolio.trades(), "records")
                    else None,
                    "init_cash": portfolio.init_cash,
                    "fees": portfolio.fees if hasattr(portfolio, "fees") else None,
                    "wrapper": {
                        "index": portfolio.wrapper.index,
                        "columns": portfolio.wrapper.columns,
                        "freq": portfolio.wrapper.freq,
                    }
                    if hasattr(portfolio, "wrapper")
                    else None,
                }

                with open(file_path, "wb") as f:
                    pickle.dump(portfolio_data, f, protocol=pickle.HIGHEST_PROTOCOL)
                results.add_file("vectorbt_components", file_path)
                self._log("VectorBT portfolio components exported successfully")
                return
            except Exception as components_error:
                self._log(f"Component export failed: {components_error}", "debug")

            # Third attempt: Export as JSON (metadata only)
            try:
                json_filename = f"{base_filename}_vectorbt_metadata.json"
                json_file_path = os.path.join(self.config.output_dir, json_filename)

                metadata = {
                    "portfolio_type": str(type(portfolio)),
                    "shape": getattr(portfolio.wrapper, "shape", None),
                    "columns": list(portfolio.wrapper.columns)
                    if hasattr(portfolio.wrapper, "columns")
                    else None,
                    "index_start": str(portfolio.wrapper.index[0])
                    if hasattr(portfolio.wrapper, "index")
                    else None,
                    "index_end": str(portfolio.wrapper.index[-1])
                    if hasattr(portfolio.wrapper, "index")
                    else None,
                    "init_cash": float(portfolio.init_cash)
                    if hasattr(portfolio, "init_cash")
                    else None,
                    "note": "VectorBT object could not be serialized. This file contains metadata only.",
                }

                import json

                with open(json_file_path, "w") as f:
                    json.dump(metadata, f, indent=2)
                results.add_file("vectorbt_metadata", json_file_path)
                self._log("VectorBT metadata exported as JSON fallback")

            except Exception as json_error:
                self._log(f"JSON metadata export failed: {json_error}", "debug")
                raise

        except Exception as e:
            self._log(
                f"Error exporting VectorBT object (all methods failed): {str(e)}",
                "warning",
            )
            self._log(
                "Note: VectorBT objects may not be serializable due to internal caching mechanisms",
                "info",
            )

    def _export_metadata(
        self,
        portfolio: "vbt.Portfolio",
        portfolio_name: str,
        base_filename: str,
        results: ExportResults,
    ):
        """Export metadata about the portfolio and export process."""
        try:
            metadata = {
                "portfolio_name": portfolio_name,
                "export_timestamp": pd.Timestamp.now().isoformat(),
                "export_config": {
                    "output_dir": self.config.output_dir,
                    "export_formats": [f.value for f in self.config.export_formats],
                    "data_types": [dt.value for dt in self.config.data_types],
                    "include_vectorbt_object": self.config.include_vectorbt_object,
                },
                "portfolio_info": {
                    "start_date": str(portfolio.wrapper.index[0])
                    if hasattr(portfolio.wrapper, "index")
                    else None,
                    "end_date": str(portfolio.wrapper.index[-1])
                    if hasattr(portfolio.wrapper, "index")
                    else None,
                    "total_periods": len(portfolio.wrapper.index)
                    if hasattr(portfolio.wrapper, "index")
                    else None,
                    "columns": list(portfolio.wrapper.columns)
                    if hasattr(portfolio.wrapper, "columns")
                    else None,
                },
                "exported_files": results.exported_files,
                "total_files_exported": results.total_files,
            }

            filename = f"{base_filename}_metadata.json"
            file_path = os.path.join(self.config.output_dir, filename)

            with open(file_path, "w") as f:
                json.dump(metadata, f, indent=2, default=str)

            results.add_file("metadata", file_path)

        except Exception as e:
            self._log(f"Error exporting metadata: {str(e)}", "warning")

    def _generate_filename(self, portfolio_name: str) -> str:
        """Generate base filename for exports."""
        # Clean portfolio name for filename
        clean_name = "".join(
            c for c in portfolio_name if c.isalnum() or c in ("_", "-")
        ).rstrip()

        # Build filename with prefix/suffix
        parts = []
        if self.config.filename_prefix:
            parts.append(self.config.filename_prefix)
        parts.append(clean_name)
        if self.config.filename_suffix:
            parts.append(self.config.filename_suffix)

        return "_".join(parts)

    def load_vectorbt_portfolio(self, file_path: str) -> "vbt.Portfolio":
        """Load a saved VectorBT portfolio object."""
        try:
            with open(file_path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            self._log(f"Error loading VectorBT portfolio: {str(e)}", "error")
            raise

    def get_export_summary(self, results: ExportResults) -> str:
        """Generate a human-readable summary of export results."""
        if not results.success:
            return f"Export failed: {results.error_message}"

        summary_lines = [
            f"Export completed successfully!",
            f"Total files exported: {results.total_files}",
            f"Output directory: {self.config.output_dir}",
            "",
            "Exported data types:",
        ]

        for data_type, files in results.exported_files.items():
            summary_lines.append(f"  - {data_type}: {len(files)} files")
            for file_path in files:
                filename = os.path.basename(file_path)
                summary_lines.append(f"    • {filename}")

        return "\n".join(summary_lines)

    def _log(self, message: str, level: str = "info"):
        """Log message using provided logger or print."""
        if self.logger:
            getattr(self.logger, level)(message)
        else:
            print(f"[{level.upper()}] {message}")
