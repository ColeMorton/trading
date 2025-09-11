"""
Sector comparison analysis engine.

Provides functionality to compare sector ETF performance using SMA strategy scores,
generating cross-comparison matrices for sector opportunity identification.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
from rich.console import Console

from .console_logging import ConsoleLogger


class SectorComparisonEngine:
    """Engine for analyzing and comparing sector ETF SMA strategy performance."""

    SECTOR_MAPPING = {
        "XLK": "Technology",
        "XLY": "Consumer Discretionary",
        "XLE": "Energy",
        "XLU": "Utilities",
        "XLRE": "Real Estate",
        "XLI": "Industrials",
        "XLV": "Healthcare",
        "XLP": "Consumer Staples",
        "XLB": "Materials",
        "XLF": "Financials",
        "XLC": "Communication Services",
    }

    def __init__(
        self,
        data_directory: Union[
            str, Path
        ] = "/Users/colemorton/Projects/trading/data/raw",
        date: Optional[str] = None,
        benchmark_ticker: Optional[str] = None,
    ):
        """
        Initialize sector comparison engine.

        Args:
            data_directory: Path to raw data directory
            date: Specific date in YYYYMMDD format, or None for latest available
            benchmark_ticker: Optional benchmark ticker (e.g., 'SPY', 'BTC-USD') for comparison
        """
        self.data_directory = Path(data_directory)
        self.portfolios_best_dir = self.data_directory / "portfolios_best"
        self.portfolios_dir = self.data_directory / "portfolios"
        self.date = date
        self.benchmark_ticker = benchmark_ticker
        self.benchmark_data = None
        self.console = Console()
        self.logger = ConsoleLogger()

    def get_available_dates(self) -> List[str]:
        """
        Get list of available dates in portfolios_best directory.

        Returns:
            List of date strings in YYYYMMDD format, sorted newest first
        """
        if not self.portfolios_best_dir.exists():
            return []

        dates = []
        for path in self.portfolios_best_dir.iterdir():
            if path.is_dir() and path.name.isdigit() and len(path.name) == 8:
                dates.append(path.name)

        return sorted(dates, reverse=True)  # Newest first

    def get_latest_date(self) -> Optional[str]:
        """
        Get the latest available date from portfolios_best directory.

        Returns:
            Latest date string in YYYYMMDD format, or None if no dates available
        """
        available_dates = self.get_available_dates()
        return available_dates[0] if available_dates else None

    def resolve_target_date(self) -> Optional[str]:
        """
        Resolve the target date to use for data loading.

        Returns:
            Date string in YYYYMMDD format, or None if no suitable date found
        """
        if self.date:
            # Use specified date
            return self.date
        else:
            # Use latest available date
            return self.get_latest_date()

    def get_data_directory(self, use_dated: bool = True) -> Path:
        """
        Get the appropriate data directory for loading sector data.

        Args:
            use_dated: Whether to use dated directory structure

        Returns:
            Path to data directory
        """
        if use_dated:
            target_date = self.resolve_target_date()
            if target_date:
                dated_dir = self.portfolios_best_dir / target_date
                if dated_dir.exists():
                    # Check if this directory actually contains sector ETF data
                    sector_files = list(dated_dir.glob("XL*_D_SMA.csv"))
                    if sector_files:
                        return dated_dir
                    else:
                        self.logger.debug(
                            f"Dated directory {target_date} exists but contains no sector ETF files"
                        )

        # Fallback to regular portfolios directory
        return self.portfolios_dir

    def load_benchmark_data(self) -> Optional[Dict]:
        """
        Load benchmark data if benchmark_ticker is specified.

        Returns:
            Dict with benchmark strategy info, or None if not found/specified
        """
        if not self.benchmark_ticker:
            return None

        data_dir = self.get_data_directory(use_dated=True)
        benchmark_file = data_dir / f"{self.benchmark_ticker}_D_SMA.csv"

        if benchmark_file.exists():
            try:
                df = pd.read_csv(benchmark_file)
                if not df.empty and "Score" in df.columns:
                    best_row = df.loc[df["Score"].idxmax()]

                    benchmark_info = {
                        "ticker": self.benchmark_ticker,
                        "score": float(best_row["Score"]),
                        "short_window": int(best_row["Fast Period"]),
                        "long_window": int(best_row["Slow Period"]),
                        "win_rate": float(best_row["Win Rate [%]"]),
                        "total_return": float(best_row["Total Return [%]"]),
                        "profit_factor": float(best_row["Profit Factor"]),
                        "sortino_ratio": float(best_row["Sortino Ratio"]),
                        "sharpe_ratio": float(best_row["Sharpe Ratio"]),
                        "max_drawdown": float(best_row["Max Drawdown [%]"]),
                        "annualized_volatility": float(
                            best_row["Annualized Volatility"]
                        ),
                        "total_trades": int(best_row["Total Trades"]),
                        "expectancy_per_trade": float(best_row["Expectancy per Trade"]),
                        "calmar_ratio": float(best_row["Calmar Ratio"]),
                    }

                    self.logger.info(
                        f"Loaded benchmark data for {self.benchmark_ticker} (Score: {benchmark_info['score']:.4f})"
                    )
                    return benchmark_info

            except Exception as e:
                self.logger.error(
                    f"Error loading benchmark {self.benchmark_ticker}: {str(e)}"
                )

        self.logger.warning(f"Benchmark file not found: {benchmark_file}")
        return None

    def check_current_data_freshness(self) -> bool:
        """
        Check if current date sector data exists and is complete.

        Returns:
            True if all sector data exists for today, False otherwise
        """
        from datetime import datetime

        current_date = datetime.now().strftime("%Y%m%d")
        current_dir = self.portfolios_best_dir / current_date

        if not current_dir.exists():
            self.logger.debug(f"Current date directory not found: {current_date}")
            return False

        # Check if all 11 sector ETF files exist
        missing_sectors = []
        for ticker in self.SECTOR_MAPPING.keys():
            sector_file = current_dir / f"{ticker}_D_SMA.csv"
            if not sector_file.exists():
                missing_sectors.append(ticker)

        if missing_sectors:
            self.logger.debug(
                f"Missing sector files for current date: {', '.join(missing_sectors)}"
            )
            return False

        self.logger.debug(f"All sector data exists for current date: {current_date}")
        return True

    def needs_data_refresh(self, force_refresh: bool = False) -> bool:
        """
        Determine if sector data needs to be refreshed.

        Args:
            force_refresh: If True, always return True

        Returns:
            True if data refresh is needed, False otherwise
        """
        if force_refresh:
            self.logger.info("Force refresh requested - will regenerate sector data")
            return True

        if not self.check_current_data_freshness():
            self.logger.info(
                "Current sector data incomplete - will generate missing data"
            )
            return True

        self.logger.debug("Current sector data is fresh and complete")
        return False

    def load_sector_data(self) -> Dict[str, pd.DataFrame]:
        """
        Load SMA portfolio data for all sector ETFs.

        Returns:
            Dict mapping ticker to DataFrame with portfolio results
        """
        sector_data = {}
        missing_tickers = []

        # Determine which directory to use
        data_dir = self.get_data_directory(use_dated=True)
        target_date = self.resolve_target_date()

        if target_date and data_dir == self.portfolios_best_dir / target_date:
            self.logger.info(f"Loading sector data from dated directory: {target_date}")
        else:
            self.logger.info(f"Loading sector data from fallback directory: {data_dir}")
            if target_date is None and self.portfolios_best_dir.exists():
                available_dates = self.get_available_dates()
                if available_dates:
                    self.logger.warning(
                        f"No current date data found. Available dates: {', '.join(available_dates[:3])}"
                    )
                else:
                    self.logger.warning("No dated directories found in portfolios_best")

        for ticker in self.SECTOR_MAPPING.keys():
            portfolio_file = data_dir / f"{ticker}_D_SMA.csv"

            if portfolio_file.exists():
                try:
                    df = pd.read_csv(portfolio_file)
                    if not df.empty and "Score" in df.columns:
                        sector_data[ticker] = df
                        self.logger.debug(f"Loaded {len(df)} strategies for {ticker}")
                    else:
                        self.logger.warning(f"Empty or invalid data for {ticker}")
                        missing_tickers.append(ticker)
                except Exception as e:
                    self.logger.error(f"Error loading {ticker}: {str(e)}")
                    missing_tickers.append(ticker)
            else:
                self.logger.warning(
                    f"Portfolio file not found for {ticker}: {portfolio_file}"
                )
                missing_tickers.append(ticker)

        if missing_tickers:
            self.logger.warning(
                f"Missing data for tickers: {', '.join(missing_tickers)}"
            )

        self.logger.info(f"Successfully loaded data for {len(sector_data)} sectors")
        return sector_data

    def extract_best_strategies(
        self, sector_data: Dict[str, pd.DataFrame]
    ) -> List[Dict]:
        """
        Extract the best performing strategy for each sector based on Score.

        Args:
            sector_data: Dict mapping ticker to portfolio DataFrame

        Returns:
            List of dicts with best strategy info for each sector
        """
        results = []

        for ticker, df in sector_data.items():
            if df.empty or "Score" not in df.columns:
                continue

            best_row = df.loc[df["Score"].idxmax()]

            strategy_info = {
                "ticker": ticker,
                "sector_name": self.SECTOR_MAPPING[ticker],
                "score": float(best_row["Score"]),
                "short_window": int(best_row["Fast Period"]),
                "long_window": int(best_row["Slow Period"]),
                "win_rate": float(best_row["Win Rate [%]"]),
                "total_return": float(best_row["Total Return [%]"]),
                "profit_factor": float(best_row["Profit Factor"]),
                "sortino_ratio": float(best_row["Sortino Ratio"]),
                "sharpe_ratio": float(best_row["Sharpe Ratio"]),
                "max_drawdown": float(best_row["Max Drawdown [%]"]),
                "annualized_volatility": float(best_row["Annualized Volatility"]),
                "total_trades": int(best_row["Total Trades"]),
                "expectancy_per_trade": float(best_row["Expectancy per Trade"]),
                "calmar_ratio": float(best_row["Calmar Ratio"]),
            }

            results.append(strategy_info)
            self.logger.debug(
                f"{ticker} best score: {strategy_info['score']:.4f} (SMA {strategy_info['short_window']}/{strategy_info['long_window']})"
            )

        return results

    def rank_sectors(self, strategies: List[Dict]) -> List[Dict]:
        """
        Rank sectors by Score and add ranking information.

        Args:
            strategies: List of strategy dicts from extract_best_strategies

        Returns:
            List of strategy dicts with ranking information added
        """
        if not strategies:
            return []

        sorted_strategies = sorted(strategies, key=lambda x: x["score"], reverse=True)

        top_score = sorted_strategies[0]["score"] if sorted_strategies else 0

        # Add benchmark comparisons if available
        if self.benchmark_data:
            benchmark_score = self.benchmark_data["score"]
            for strategy in sorted_strategies:
                strategy["score_vs_benchmark_pct"] = (
                    (strategy["score"] / benchmark_score * 100)
                    if benchmark_score > 0
                    else 0
                )
                strategy["outperforms_benchmark"] = strategy["score"] > benchmark_score

        for i, strategy in enumerate(sorted_strategies):
            strategy["rank"] = i + 1
            strategy["score_vs_top_pct"] = (
                (strategy["score"] / top_score * 100) if top_score > 0 else 0
            )

        self.logger.info(f"Ranked {len(sorted_strategies)} sectors by Score")
        if self.benchmark_data:
            outperforming = sum(
                1 for s in sorted_strategies if s.get("outperforms_benchmark", False)
            )
            self.logger.info(
                f"{outperforming}/{len(sorted_strategies)} sectors outperform {self.benchmark_ticker}"
            )
        return sorted_strategies

    def generate_comparison_matrix(self) -> List[Dict]:
        """
        Generate complete sector comparison matrix.

        Returns:
            List of ranked sector comparison data
        """
        self.logger.info("Starting sector comparison analysis")

        # Load benchmark data if specified
        if self.benchmark_ticker:
            self.benchmark_data = self.load_benchmark_data()

        sector_data = self.load_sector_data()
        if not sector_data:
            available_dates = self.get_available_dates()
            if available_dates:
                self.logger.error(
                    f"No sector data loaded. Try running: trading-cli strategy run -p sectors_current"
                )
                self.logger.error(f"Available dates: {', '.join(available_dates[:5])}")
            else:
                self.logger.error(
                    "No sector data found. Run: trading-cli strategy run -p sectors_current"
                )
            return []

        best_strategies = self.extract_best_strategies(sector_data)
        if not best_strategies:
            self.logger.error(
                "No valid strategies found - cannot generate comparison matrix"
            )
            return []

        ranked_results = self.rank_sectors(best_strategies)

        self.logger.info(
            f"Generated comparison matrix with {len(ranked_results)} sectors"
        )
        return ranked_results

    def export_to_json(
        self, comparison_data: List[Dict], output_file: Union[str, Path]
    ) -> bool:
        """
        Export comparison data to JSON file.

        Args:
            comparison_data: Ranked comparison data from generate_comparison_matrix
            output_file: Path to output JSON file

        Returns:
            True if successful, False otherwise
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w") as f:
                json.dump(comparison_data, f, indent=2)

            self.logger.info(f"Exported sector comparison to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {str(e)}")
            return False

    def export_to_csv(
        self, comparison_data: List[Dict], output_file: Union[str, Path]
    ) -> bool:
        """
        Export comparison data to CSV file.

        Args:
            comparison_data: Ranked comparison data from generate_comparison_matrix
            output_file: Path to output CSV file

        Returns:
            True if successful, False otherwise
        """
        try:
            if not comparison_data:
                self.logger.warning("No data to export")
                return False

            df = pd.DataFrame(comparison_data)
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            df.to_csv(output_path, index=False)

            self.logger.info(f"Exported sector comparison to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {str(e)}")
            return False
