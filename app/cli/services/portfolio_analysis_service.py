"""
Portfolio Analysis Service

This service provides functionality to aggregate and analyze portfolio data
from CSV files for dry-run analysis commands.
"""

import contextlib
from pathlib import Path

import pandas as pd
from rich import print as rprint


class PortfolioAnalysisService:
    """Service for aggregating and analyzing portfolio CSV files."""

    def __init__(
        self,
        base_dir: str = "/Users/colemorton/Projects/trading",
        use_current: bool = False,
        custom_date: str | None = None,
    ):
        """Initialize the service with base directory path, current mode flag, and optional custom date."""
        self.base_dir = Path(base_dir)
        self.use_current = use_current
        self.custom_date = custom_date
        self.portfolios_best_dir = self.base_dir / "data" / "raw" / "portfolios_best"

    def _get_current_date_string(self) -> str:
        """Get current date in YYYYMMDD format, or custom date if specified."""
        if self.custom_date:
            return self.custom_date

        from datetime import datetime

        return datetime.now().strftime("%Y%m%d")

    def aggregate_portfolios_best(self, tickers: list[str]) -> pd.DataFrame:
        """
        Aggregate all portfolios_best CSV files for the given tickers.

        Args:
            tickers: List of ticker symbols to search for

        Returns:
            Combined DataFrame with all portfolio data
        """
        all_dataframes = []
        found_files = []
        missing_tickers = []

        # Show search location for current mode
        if self.use_current:
            current_date = self._get_current_date_string()
            search_location = self.portfolios_best_dir / current_date
            date_type = "custom date" if self.custom_date else "current day"
            rprint(f"[dim]Searching {date_type} directory: {search_location}[/dim]")
        else:
            search_location = self.portfolios_best_dir
            rprint(f"[dim]Searching general directory: {search_location}[/dim]")

        for ticker in tickers:
            ticker_files = self._find_ticker_files(ticker)

            if ticker_files:
                for file_path in ticker_files:
                    try:
                        df = pd.read_csv(file_path)
                        if not df.empty:
                            all_dataframes.append(df)
                            found_files.append(file_path)
                    except Exception as e:
                        rprint(
                            f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]"
                        )
            else:
                missing_tickers.append(ticker)

        if missing_tickers:
            if self.use_current:
                current_date = self._get_current_date_string()
                date_type = "custom date" if self.custom_date else "current day"
                rprint(
                    f"[dim]No {date_type} portfolio files found for: {', '.join(missing_tickers)} in {current_date}/[/dim]"
                )
            else:
                rprint(
                    f"[dim]No portfolio files found for: {', '.join(missing_tickers)}[/dim]"
                )

        if not all_dataframes:
            if self.use_current:
                current_date = self._get_current_date_string()
                date_type = "custom date" if self.custom_date else "current day"
                rprint(
                    f"[yellow]No valid {date_type} portfolio data found for any tickers[/yellow]"
                )
                if self.custom_date:
                    rprint(
                        "[dim]Try a different date or remove --date to search the general portfolios_best directory[/dim]"
                    )
                else:
                    rprint(
                        "[dim]Try without --current to search the general portfolios_best directory[/dim]"
                    )
            else:
                rprint("[yellow]No valid portfolio data found for any tickers[/yellow]")
                rprint(
                    "[dim]Make sure portfolios_best files exist in data/raw/portfolios_best/[/dim]"
                )
            return pd.DataFrame()

        # Combine all dataframes
        combined_df = pd.concat(all_dataframes, ignore_index=True)

        if self.use_current:
            date_string = self._get_current_date_string()
            date_type = "custom date" if self.custom_date else "current day"
            search_type = f"{date_type} ({date_string})"
        else:
            search_type = "general"

        rprint(
            f"[green]📊 Loaded {len(combined_df)} portfolios from {len(found_files)} files ({search_type})[/green]"
        )

        return combined_df

    def aggregate_all_current_portfolios(self) -> pd.DataFrame:
        """
        Aggregate ALL portfolio files from the current day directory.
        This method auto-discovers all CSV files without needing a ticker list.

        Returns:
            Combined DataFrame with all current day portfolio data
        """
        if not self.use_current:
            rprint(
                "[yellow]Warning: aggregate_all_current_portfolios() requires use_current=True[/yellow]"
            )
            return pd.DataFrame()

        current_date = self._get_current_date_string()
        search_dir = self.portfolios_best_dir / current_date

        date_type = "custom date" if self.custom_date else "current day"
        rprint(
            f"[dim]Auto-discovering all portfolios in {date_type} directory: {search_dir}[/dim]"
        )

        if not search_dir.exists():
            date_type = "custom date" if self.custom_date else "current date"
            rprint(
                f"[yellow]{date_type.title()} directory not found: {search_dir}[/yellow]"
            )
            return pd.DataFrame()

        # Discover all CSV files in current date directory
        all_files = self._discover_all_current_files()

        if not all_files:
            date_type = "custom date" if self.custom_date else "current day"
            rprint(
                f"[yellow]No portfolio files found in {date_type} directory: {search_dir}[/yellow]"
            )
            return pd.DataFrame()

        # Load all discovered files
        all_dataframes = []
        successful_files = []

        for file_path in all_files:
            try:
                df = pd.read_csv(file_path)
                if not df.empty:
                    all_dataframes.append(df)
                    successful_files.append(file_path)
            except Exception as e:
                rprint(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")

        if not all_dataframes:
            date_type = "custom date" if self.custom_date else "current day"
            rprint(
                f"[yellow]No valid portfolio data found in {date_type} files[/yellow]"
            )
            return pd.DataFrame()

        # Combine all dataframes
        combined_df = pd.concat(all_dataframes, ignore_index=True)

        # Extract unique tickers for reporting
        unique_tickers = set()
        for file_path in successful_files:
            filename = file_path.name
            if "_D_" in filename:
                ticker = filename.split("_D_")[0]
                unique_tickers.add(ticker)

        date_type = "custom date" if self.custom_date else "current day"
        rprint(
            f"[green]📊 Auto-discovered {len(successful_files)} portfolios from {len(unique_tickers)} tickers ({date_type}: {current_date})[/green]"
        )
        rprint(f"[dim]Tickers found: {', '.join(sorted(unique_tickers))}[/dim]")

        return combined_df

    def _discover_all_current_files(self) -> list[Path]:
        """
        Discover all CSV files in the current date directory.

        Returns:
            List of all CSV file paths in current date directory
        """
        if not self.use_current:
            return []

        current_date = self._get_current_date_string()
        search_dir = self.portfolios_best_dir / current_date

        if not search_dir.exists():
            return []

        # Find all CSV files in the current date directory
        all_csv_files = list(search_dir.glob("*.csv"))

        # Filter for portfolio files (basic pattern matching)
        portfolio_files = []
        for file_path in all_csv_files:
            filename = file_path.name
            # Match pattern: {TICKER}_D_{STRATEGY}.csv or similar
            if "_D_" in filename and filename.endswith(".csv"):
                portfolio_files.append(file_path)

        return sorted(portfolio_files)

    def _find_ticker_files(self, ticker: str) -> list[Path]:
        """
        Find all portfolio_best files for a given ticker.

        Args:
            ticker: Ticker symbol to search for

        Returns:
            List of file paths matching the ticker
        """
        # Determine search directory based on current mode
        if self.use_current:
            current_date = self._get_current_date_string()
            search_dir = self.portfolios_best_dir / current_date

            if not search_dir.exists():
                date_type = "custom date" if self.custom_date else "current date"
                rprint(
                    f"[yellow]Warning: {date_type.title()} directory not found: {search_dir}[/yellow]"
                )
                return []
        else:
            search_dir = self.portfolios_best_dir

        if not search_dir.exists():
            return []

        # Pattern matching for ticker files
        patterns = [
            f"{ticker}_2D_*.csv",  # {TICKER}_2D_{STRATEGY}.csv
            f"{ticker}_2D.csv",  # {TICKER}_2D.csv
            f"{ticker}_D_*.csv",  # {TICKER}_D_{STRATEGY}.csv
            f"{ticker}_D.csv",  # {TICKER}_D.csv
            f"{ticker}_4H_*.csv",  # {TICKER}_4H_{STRATEGY}.csv
            f"{ticker}_4H.csv",  # {TICKER}_4H.csv
            f"{ticker}_H_*.csv",  # {TICKER}_H_{STRATEGY}.csv
            f"{ticker}_H.csv",  # {TICKER}_H.csv
        ]

        found_files: list[Path] = []
        for pattern in patterns:
            found_files.extend(search_dir.glob(pattern))

        return sorted(found_files)

    def remove_metric_type_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove the Metric Type column from the dataframe.

        Args:
            df: Input dataframe

        Returns:
            Dataframe with Metric Type column removed
        """
        if df.empty:
            return df

        # Remove Metric Type column if it exists
        if "Metric Type" in df.columns:
            df = df.drop("Metric Type", axis=1)

        return df

    def sort_portfolios(
        self, df: pd.DataFrame, sort_by: str = "Score", ascending: bool = False
    ) -> pd.DataFrame:
        """
        Sort portfolios by specified column.

        Args:
            df: Input dataframe
            sort_by: Column name to sort by
            ascending: Sort order (False for descending)

        Returns:
            Sorted dataframe
        """
        if df.empty or sort_by not in df.columns:
            return df

        # Convert to numeric if possible for proper sorting
        with contextlib.suppress(Exception):
            df[sort_by] = pd.to_numeric(df[sort_by], errors="coerce")

        return df.sort_values(
            by=sort_by, ascending=ascending, na_position="last"
        ).reset_index(drop=True)

    def format_for_display(self, df: pd.DataFrame, top_n: int = 50) -> dict:
        """
        Format dataframe data for display purposes.

        Args:
            df: Input dataframe
            top_n: Number of top results to include in summary

        Returns:
            Dictionary with formatted data and statistics
        """
        if df.empty:
            return {
                "top_results": pd.DataFrame(),
                "all_results": pd.DataFrame(),
                "stats": {
                    "total_portfolios": 0,
                    "avg_score": 0,
                    "win_rate_range": (0, 0),
                    "best_ticker": "N/A",
                    "best_return": 0,
                },
            }

        # Get top N results for table display
        top_results = df.head(top_n)

        # Calculate statistics
        stats = self._calculate_stats(df)

        return {"top_results": top_results, "all_results": df, "stats": stats}

    def _calculate_stats(self, df: pd.DataFrame) -> dict:
        """Calculate summary statistics from the dataframe."""
        if df.empty:
            return {
                "total_portfolios": 0,
                "avg_score": 0,
                "win_rate_range": (0, 0),
                "best_ticker": "N/A",
                "best_return": 0,
            }

        stats = {"total_portfolios": len(df)}

        # Average score
        if "Score" in df.columns:
            try:
                avg_score = pd.to_numeric(df["Score"], errors="coerce").mean()
                stats["avg_score"] = avg_score if not pd.isna(avg_score) else 0
            except:
                stats["avg_score"] = 0
        else:
            stats["avg_score"] = 0

        # Win rate range
        if "Win Rate [%]" in df.columns:
            try:
                win_rates = pd.to_numeric(df["Win Rate [%]"], errors="coerce")
                win_rates_clean = win_rates.dropna()
                if len(win_rates_clean) > 0:
                    stats["win_rate_range"] = (
                        win_rates_clean.min(),
                        win_rates_clean.max(),
                    )
                else:
                    stats["win_rate_range"] = (0, 0)
            except:
                stats["win_rate_range"] = (0, 0)
        else:
            stats["win_rate_range"] = (0, 0)

        # Best performing ticker and return
        if "Total Return [%]" in df.columns and "Ticker" in df.columns:
            try:
                returns = pd.to_numeric(df["Total Return [%]"], errors="coerce")
                if not returns.empty and not returns.isna().all():
                    best_idx = returns.idxmax()
                    stats["best_ticker"] = df.loc[best_idx, "Ticker"]
                    stats["best_return"] = returns.loc[best_idx]
                else:
                    stats["best_ticker"] = "N/A"
                    stats["best_return"] = 0
            except:
                stats["best_ticker"] = "N/A"
                stats["best_return"] = 0
        else:
            stats["best_ticker"] = "N/A"
            stats["best_return"] = 0

        return stats

    def generate_csv_output(self, df: pd.DataFrame) -> str:
        """
        Generate CSV string output ready for copy/paste.

        Args:
            df: Input dataframe

        Returns:
            CSV formatted string with headers and proper newlines
        """
        if df.empty:
            return "No data available"

        # Standardize schema and fix data types before output
        standardized_df = self._standardize_output_schema(df)

        # Convert dataframe to CSV string with proper line breaks
        csv_string = standardized_df.to_csv(index=False, lineterminator="\n")

        # Ensure each row is on a new line for better readability
        lines = csv_string.strip().split("\n")
        formatted_csv = "\n".join(lines)

        return formatted_csv

    def _standardize_output_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize DataFrame schema to ensure consistent output format.

        Fixes:
        1. Remove legacy columns (Alpha, Beta, Short Window, Long Window, Signal Window)
        2. Convert Fast/Slow/Signal Period from float to integer
        3. Fix data corruption (migrate data from wrong columns)

        Args:
            df: Input DataFrame with potentially inconsistent schema

        Returns:
            DataFrame with standardized 61-column Extended schema
        """
        # Create a copy to avoid modifying the original
        standardized_df = df.copy()

        # Define the target Extended schema columns (61 columns)
        target_columns = [
            "Ticker",
            "Strategy Type",
            "Fast Period",
            "Slow Period",
            "Signal Period",
            "Signal Entry",
            "Signal Exit",
            "Signal Unconfirmed",
            "Total Open Trades",
            "Total Trades",
            "Score",
            "Win Rate [%]",
            "Profit Factor",
            "Expectancy per Trade",
            "Sortino Ratio",
            "Beats BNH [%]",
            "Avg Trade Duration",
            "Trades Per Day",
            "Trades per Month",
            "Signals per Month",
            "Expectancy per Month",
            "Start",
            "End",
            "Period",
            "Start Value",
            "End Value",
            "Total Return [%]",
            "Benchmark Return [%]",
            "Max Gross Exposure [%]",
            "Total Fees Paid",
            "Max Drawdown [%]",
            "Max Drawdown Duration",
            "Total Closed Trades",
            "Open Trade PnL",
            "Best Trade [%]",
            "Worst Trade [%]",
            "Avg Winning Trade [%]",
            "Avg Losing Trade [%]",
            "Avg Winning Trade Duration",
            "Avg Losing Trade Duration",
            "Expectancy",
            "Sharpe Ratio",
            "Calmar Ratio",
            "Omega Ratio",
            "Skew",
            "Kurtosis",
            "Tail Ratio",
            "Common Sense Ratio",
            "Value at Risk",
            "Daily Returns",
            "Annual Returns",
            "Cumulative Returns",
            "Annualized Return",
            "Annualized Volatility",
            "Signal Count",
            "Position Count",
            "Total Period",
            "Allocation [%]",
            "Stop Loss [%]",
            "Last Position Open Date",
            "Last Position Close Date",
        ]

        # Fix data corruption: migrate data from wrong columns to correct columns
        # Handle cases where Fast/Slow/Signal Period are empty but data exists in Short/Long/Signal Window
        if all(
            col in standardized_df.columns
            for col in ["Short Window", "Long Window", "Signal Window"]
        ):
            for idx, row in standardized_df.iterrows():
                # Check if Fast/Slow/Signal Period are missing/empty AND Short/Long/Signal Window have data
                fast_empty = (
                    pd.isna(row.get("Fast Period")) or row.get("Fast Period") == ""
                )
                slow_empty = (
                    pd.isna(row.get("Slow Period")) or row.get("Slow Period") == ""
                )
                signal_empty = (
                    pd.isna(row.get("Signal Period")) or row.get("Signal Period") == ""
                )

                short_has_data = (
                    not pd.isna(row.get("Short Window"))
                    and row.get("Short Window") != ""
                )
                long_has_data = (
                    not pd.isna(row.get("Long Window")) and row.get("Long Window") != ""
                )
                signal_has_data = (
                    not pd.isna(row.get("Signal Window"))
                    and row.get("Signal Window") != ""
                )

                # Migrate data if corruption detected
                if fast_empty and short_has_data:
                    standardized_df.at[idx, "Fast Period"] = row["Short Window"]
                if slow_empty and long_has_data:
                    standardized_df.at[idx, "Slow Period"] = row["Long Window"]
                if signal_empty and signal_has_data:
                    standardized_df.at[idx, "Signal Period"] = row["Signal Window"]

        # Remove legacy columns that should not be in output
        legacy_columns = [
            "Alpha",
            "Beta",
            "Short Window",
            "Long Window",
            "Signal Window",
        ]
        columns_to_remove = [
            col for col in legacy_columns if col in standardized_df.columns
        ]
        if columns_to_remove:
            standardized_df = standardized_df.drop(columns=columns_to_remove)

        # Fix data types: convert Fast/Slow/Signal Period to integers
        period_columns = ["Fast Period", "Slow Period", "Signal Period"]
        for col in period_columns:
            if col in standardized_df.columns:
                # Convert to numeric first (handles string numbers), then to int
                standardized_df[col] = pd.to_numeric(
                    standardized_df[col], errors="coerce"
                )
                # Convert to integer, handling NaN values
                standardized_df[col] = standardized_df[col].fillna(0).astype("int64")

        # Ensure we only output the target columns in the correct order
        output_columns = [
            col for col in target_columns if col in standardized_df.columns
        ]
        standardized_df = standardized_df[output_columns]

        return standardized_df

    def get_display_columns(self) -> list[str]:
        """Get the key columns to display in the summary table."""
        return [
            "Ticker",  # Position 1
            "Strategy Type",  # Position 2
            "Score",  # Position 10
            "Win Rate [%]",  # Position 11
            "Profit Factor",  # Position 12 - NEW
            "Expectancy per Trade",  # Position 13 - NEW
            "Sortino Ratio",  # Position 14 - NEW
            "Total Return [%]",  # Position 26
            "Sharpe Ratio",  # Position 41
            "Max Drawdown [%]",  # Position 30
            "Total Trades",  # Position 9
        ]

    def export_to_csv(self, df: pd.DataFrame, output_dir: str) -> tuple[bool, str]:
        """
        Export DataFrame to timestamped CSV file.

        Args:
            df: DataFrame to export
            output_dir: Base output directory path

        Returns:
            Tuple of (success: bool, file_path: str)
        """
        from datetime import datetime

        if df.empty:
            raise ValueError("Cannot export empty DataFrame")

        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}.csv"
        file_path = output_path / filename

        # Export standardized CSV
        standardized_df = self._standardize_output_schema(df)
        standardized_df.to_csv(file_path, index=False)

        return True, str(file_path)
