"""
Position Equity Generator Module

This module generates equity curves from position-level data by reconstructing
portfolio timelines and using VectorBT to calculate comprehensive equity metrics.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import vectorbt as vbt

from app.tools.equity_data_extractor import EquityData, EquityDataExtractor, MetricType
from app.tools.exceptions import TradingSystemError
from app.tools.project_utils import get_project_root


@dataclass
class PositionEntry:
    """Represents a single position entry from position CSV file."""

    position_uuid: str
    ticker: str
    strategy_type: str
    short_window: int
    long_window: int
    signal_window: int
    entry_timestamp: datetime
    exit_timestamp: Optional[datetime]
    avg_entry_price: float
    avg_exit_price: Optional[float]
    position_size: float
    direction: str
    status: str
    pnl: Optional[float]
    current_unrealized_pnl: Optional[float]


class PositionDataLoader:
    """Loads and parses position data from CSV files."""

    def __init__(self, log: Optional[Callable[[str, str], None]] = None):
        self.log = log or self._default_log
        self.positions_dir = Path(get_project_root()) / "csv" / "positions"

    def _default_log(self, message: str, level: str = "info") -> None:
        """Default logging function when none provided."""
        print(f"[{level.upper()}] {message}")

    def load_position_file(self, portfolio_name: str) -> List[PositionEntry]:
        """
        Load position data from CSV file.

        Args:
            portfolio_name: Name of portfolio (e.g., "live_signals", "risk_on")

        Returns:
            List of PositionEntry objects

        Raises:
            TradingSystemError: If file cannot be loaded or parsed
        """
        try:
            file_path = self.positions_dir / f"{portfolio_name}.csv"

            if not file_path.exists():
                raise TradingSystemError(f"Position file not found: {file_path}")

            self.log(f"Loading position data from: {file_path}", "info")

            # Read CSV file
            df = pd.read_csv(file_path)

            if df.empty:
                raise TradingSystemError(f"Position file is empty: {file_path}")

            # Parse position entries
            positions = []
            for _, row in df.iterrows():
                try:
                    position = self._parse_position_row(row)
                    positions.append(position)
                except Exception as e:
                    self.log(f"Failed to parse position row: {e}", "warning")
                    continue

            self.log(f"Loaded {len(positions)} positions from {portfolio_name}", "info")
            return positions

        except Exception as e:
            error_msg = f"Failed to load position file {portfolio_name}: {str(e)}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def _parse_position_row(self, row: pd.Series) -> PositionEntry:
        """Parse a single position row into PositionEntry object."""
        # Parse timestamps
        entry_timestamp = pd.to_datetime(row["Entry_Timestamp"])
        exit_timestamp = None
        if pd.notna(row.get("Exit_Timestamp")):
            exit_timestamp = pd.to_datetime(row["Exit_Timestamp"])

        # Parse numeric values with proper handling of NaN
        avg_exit_price = None
        if pd.notna(row.get("Avg_Exit_Price")):
            avg_exit_price = float(row["Avg_Exit_Price"])

        pnl = None
        if pd.notna(row.get("PnL")):
            pnl = float(row["PnL"])

        current_unrealized_pnl = None
        if pd.notna(row.get("Current_Unrealized_PnL")):
            current_unrealized_pnl = float(row["Current_Unrealized_PnL"])

        return PositionEntry(
            position_uuid=str(row["Position_UUID"]),
            ticker=str(row["Ticker"]),
            strategy_type=str(row["Strategy_Type"]),
            short_window=int(row["Short_Window"]),
            long_window=int(row["Long_Window"]),
            signal_window=int(row.get("Signal_Window", 0)),
            entry_timestamp=entry_timestamp,
            exit_timestamp=exit_timestamp,
            avg_entry_price=float(row["Avg_Entry_Price"]),
            avg_exit_price=avg_exit_price,
            position_size=float(row["Position_Size"]),
            direction=str(row["Direction"]),
            status=str(row["Status"]),
            pnl=pnl,
            current_unrealized_pnl=current_unrealized_pnl,
        )


class PortfolioTimelineReconstructor:
    """Reconstructs portfolio timeline from position-level data."""

    def __init__(self, log: Optional[Callable[[str, str], None]] = None):
        self.log = log or self._default_log
        self.price_data_dir = Path(get_project_root()) / "csv" / "price_data"

    def _default_log(self, message: str, level: str = "info") -> None:
        """Default logging function when none provided."""
        print(f"[{level.upper()}] {message}")

    def reconstruct_portfolio(
        self, positions: List[PositionEntry], init_cash: float = 10000.0
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Reconstruct portfolio equity curve from position data.

        This method creates individual VectorBT portfolios for each ticker and
        combines their equity curves to create a total portfolio equity curve.

        Args:
            positions: List of position entries
            init_cash: Initial cash for portfolio

        Returns:
            Tuple of (combined equity DataFrame, combined price data DataFrame)

        Raises:
            TradingSystemError: If reconstruction fails
        """
        try:
            if not positions:
                raise TradingSystemError("No positions provided for reconstruction")

            # Group positions by ticker
            ticker_positions = {}
            for position in positions:
                if position.ticker not in ticker_positions:
                    ticker_positions[position.ticker] = []
                ticker_positions[position.ticker].append(position)

            self.log(
                f"Reconstructing portfolio for {len(ticker_positions)} tickers: {list(ticker_positions.keys())}",
                "info",
            )

            # Create individual portfolios for each ticker
            ticker_equity_curves = {}
            all_price_data = {}

            for ticker, ticker_pos_list in ticker_positions.items():
                try:
                    # Check if price data exists for this ticker
                    price_file = self.price_data_dir / f"{ticker}_D.csv"
                    if not price_file.exists():
                        self.log(
                            f"Skipping {ticker} - price data not found: {price_file}",
                            "warning",
                        )
                        continue

                    # Create portfolio for this ticker
                    portfolio, price_data = self._create_ticker_portfolio(
                        ticker, ticker_pos_list, init_cash / len(ticker_positions)
                    )

                    # Extract equity curve
                    equity_curve = portfolio.value()
                    if hasattr(equity_curve, "values"):
                        equity_values = equity_curve.values
                    else:
                        equity_values = equity_curve

                    ticker_equity_curves[ticker] = {
                        "equity": equity_values,
                        "index": price_data.index,
                    }
                    all_price_data[ticker] = price_data

                    self.log(
                        f"Created portfolio for {ticker} with {len(ticker_pos_list)} positions",
                        "info",
                    )

                except Exception as e:
                    self.log(
                        f"Failed to create portfolio for {ticker}: {str(e)}", "warning"
                    )
                    continue

            if not ticker_equity_curves:
                raise TradingSystemError("No valid ticker portfolios could be created")

            # Combine equity curves
            combined_equity, combined_price_data = self._combine_equity_curves(
                ticker_equity_curves, all_price_data
            )

            self.log(
                f"Successfully reconstructed combined portfolio from {len(ticker_equity_curves)} ticker portfolios",
                "info",
            )
            return combined_equity, combined_price_data

        except Exception as e:
            error_msg = f"Failed to reconstruct portfolio: {str(e)}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def _load_combined_price_data(
        self, tickers: List[str], positions: List[PositionEntry]
    ) -> pd.DataFrame:
        """Load and combine price data for all tickers."""
        # Determine date range from positions
        start_date = min(pos.entry_timestamp for pos in positions)
        end_date = max(
            pos.exit_timestamp if pos.exit_timestamp else datetime.now()
            for pos in positions
        )

        # Load price data for first ticker to get the baseline timeline
        primary_ticker = tickers[0]
        price_file = self.price_data_dir / f"{primary_ticker}_D.csv"

        if not price_file.exists():
            raise TradingSystemError(
                f"Price data not found for {primary_ticker}: {price_file}"
            )

        price_data = pd.read_csv(price_file)
        price_data["Date"] = pd.to_datetime(price_data["Date"])
        price_data = price_data.set_index("Date")

        # Filter to relevant date range
        price_data = price_data[
            (price_data.index >= start_date) & (price_data.index <= end_date)
        ]

        if price_data.empty:
            raise TradingSystemError(
                f"No price data in date range {start_date} to {end_date}"
            )

        self.log(
            f"Loaded price data from {start_date} to {end_date} ({len(price_data)} days)",
            "info",
        )
        return price_data

    def _create_order_sequence(
        self, positions: List[PositionEntry], price_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Create chronological order sequence from positions."""
        orders = []

        for position in positions:
            # Entry order
            entry_order = {
                "timestamp": position.entry_timestamp,
                "ticker": position.ticker,
                "size": position.position_size
                if position.direction == "Long"
                else -position.position_size,
                "price": position.avg_entry_price,
                "order_type": "entry",
                "position_uuid": position.position_uuid,
            }
            orders.append(entry_order)

            # Exit order (only for closed positions)
            if (
                position.status == "Closed"
                and position.exit_timestamp
                and position.avg_exit_price
            ):
                exit_order = {
                    "timestamp": position.exit_timestamp,
                    "ticker": position.ticker,
                    "size": -position.position_size
                    if position.direction == "Long"
                    else position.position_size,
                    "price": position.avg_exit_price,
                    "order_type": "exit",
                    "position_uuid": position.position_uuid,
                }
                orders.append(exit_order)

        # Convert to DataFrame and sort by timestamp
        orders_df = pd.DataFrame(orders)
        if not orders_df.empty:
            orders_df = orders_df.sort_values("timestamp").reset_index(drop=True)

        self.log(
            f"Created {len(orders_df)} orders from {len(positions)} positions", "info"
        )
        return orders_df

    def _create_vectorbt_portfolio(
        self, orders_df: pd.DataFrame, price_data: pd.DataFrame, init_cash: float
    ) -> vbt.Portfolio:
        """Create VectorBT portfolio from order sequence."""
        try:
            # Align orders with price data timeline
            aligned_orders = self._align_orders_with_price_data(orders_df, price_data)

            # Create VectorBT portfolio using from_orders
            portfolio = vbt.Portfolio.from_orders(
                close=price_data["Close"],
                size=aligned_orders["size"],
                price=aligned_orders["price"],
                init_cash=init_cash,
                fees=0.001,  # 0.1% transaction fee
                freq="D",
            )

            return portfolio

        except Exception as e:
            raise TradingSystemError(
                f"Failed to create VectorBT portfolio: {str(e)}"
            ) from e

    def _align_orders_with_price_data(
        self, orders_df: pd.DataFrame, price_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Align orders with price data timeline."""
        # Create series aligned with price data index
        size_series = pd.Series(0.0, index=price_data.index)
        price_series = pd.Series(np.nan, index=price_data.index)

        for _, order in orders_df.iterrows():
            order_date = pd.to_datetime(order["timestamp"]).date()

            # Find closest trading day
            matching_dates = [
                idx for idx in price_data.index if idx.date() == order_date
            ]

            if matching_dates:
                order_idx = matching_dates[0]
                size_series[order_idx] += order["size"]
                price_series[order_idx] = order["price"]

        return pd.DataFrame({"size": size_series, "price": price_series})

    def _create_ticker_portfolio(
        self, ticker: str, positions: List[PositionEntry], allocated_cash: float
    ) -> Tuple[vbt.Portfolio, pd.DataFrame]:
        """Create VectorBT portfolio for a single ticker."""
        try:
            # Load price data for this ticker
            price_file = self.price_data_dir / f"{ticker}_D.csv"
            price_data = pd.read_csv(price_file)
            price_data["Date"] = pd.to_datetime(price_data["Date"])
            price_data = price_data.set_index("Date")

            # Determine date range from positions
            start_date = min(pos.entry_timestamp for pos in positions)
            end_date = max(
                pos.exit_timestamp if pos.exit_timestamp else datetime.now()
                for pos in positions
            )

            # Filter price data to relevant range
            price_data = price_data[
                (price_data.index >= start_date) & (price_data.index <= end_date)
            ]

            if price_data.empty:
                raise TradingSystemError(
                    f"No price data for {ticker} in date range {start_date} to {end_date}"
                )

            # Create order sequence for this ticker
            orders_df = self._create_ticker_order_sequence(positions, price_data)

            if orders_df.empty:
                raise TradingSystemError(f"No valid orders for {ticker}")

            # Create VectorBT portfolio
            portfolio = self._create_vectorbt_portfolio(
                orders_df, price_data, allocated_cash
            )

            return portfolio, price_data

        except Exception as e:
            raise TradingSystemError(
                f"Failed to create portfolio for {ticker}: {str(e)}"
            ) from e

    def _create_ticker_order_sequence(
        self, positions: List[PositionEntry], price_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Create order sequence for a single ticker."""
        orders = []

        for position in positions:
            # Entry order
            entry_order = {
                "timestamp": position.entry_timestamp,
                "size": position.position_size
                if position.direction == "Long"
                else -position.position_size,
                "price": position.avg_entry_price,
                "order_type": "entry",
                "position_uuid": position.position_uuid,
            }
            orders.append(entry_order)

            # Exit order (only for closed positions)
            if (
                position.status == "Closed"
                and position.exit_timestamp
                and position.avg_exit_price
            ):
                exit_order = {
                    "timestamp": position.exit_timestamp,
                    "size": -position.position_size
                    if position.direction == "Long"
                    else position.position_size,
                    "price": position.avg_exit_price,
                    "order_type": "exit",
                    "position_uuid": position.position_uuid,
                }
                orders.append(exit_order)

        # Convert to DataFrame and sort by timestamp
        orders_df = pd.DataFrame(orders)
        if not orders_df.empty:
            orders_df = orders_df.sort_values("timestamp").reset_index(drop=True)

        return orders_df

    def _combine_equity_curves(
        self,
        ticker_equity_curves: Dict[str, Dict],
        all_price_data: Dict[str, pd.DataFrame],
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Combine individual ticker equity curves into portfolio equity curve."""
        try:
            # Find union of all date ranges (not intersection)
            all_indices = [
                curve_data["index"] for curve_data in ticker_equity_curves.values()
            ]

            # Get union of all date indices
            union_index = all_indices[0]
            for idx in all_indices[1:]:
                union_index = union_index.union(idx)

            # Sort the index
            union_index = union_index.sort_values()

            if len(union_index) == 0:
                raise TradingSystemError("No dates found in ticker equity curves")

            # Initialize combined equity starting at init_cash equivalent
            # Each ticker starts with equal allocation
            init_cash_per_ticker = 10000.0 / len(
                ticker_equity_curves
            )  # Default assumption

            # Combine equity curves by summing contributions from each ticker
            combined_equity_values = pd.Series(0.0, index=union_index)

            for ticker, curve_data in ticker_equity_curves.items():
                # Create equity series for this ticker
                ticker_equity = pd.Series(
                    curve_data["equity"], index=curve_data["index"]
                )

                # Reindex to union_index with forward fill
                ticker_aligned = ticker_equity.reindex(union_index)

                # For dates before this ticker's first date, use initial cash allocation
                first_date = ticker_equity.index.min()
                ticker_aligned.loc[
                    ticker_aligned.index < first_date
                ] = init_cash_per_ticker

                # Forward fill remaining NaN values
                ticker_aligned = ticker_aligned.fillna(method="ffill")

                # Backward fill any remaining NaN values at the beginning
                ticker_aligned = ticker_aligned.fillna(method="bfill")

                # Add this ticker's contribution to total
                combined_equity_values += ticker_aligned

            # Create combined price data using first ticker as reference, extended to full date range
            first_ticker = list(all_price_data.keys())[0]
            reference_price_data = all_price_data[first_ticker]

            # Reindex reference price data to union_index
            combined_price_data = reference_price_data.reindex(
                union_index, method="ffill"
            )
            combined_price_data = combined_price_data.fillna(method="bfill")

            # Create equity DataFrame with Close prices for VectorBT compatibility
            combined_equity = pd.DataFrame(
                {
                    "Close": combined_equity_values,
                    "portfolio_value": combined_equity_values,
                },
                index=union_index,
            )

            self.log(
                f"Combined equity curves across {len(union_index)} dates from {len(ticker_equity_curves)} tickers",
                "info",
            )
            return combined_equity, combined_price_data

        except Exception as e:
            raise TradingSystemError(
                f"Failed to combine equity curves: {str(e)}"
            ) from e


class PositionEquityGenerator:
    """Main class for generating equity curves from position data."""

    def __init__(self, log: Optional[Callable[[str, str], None]] = None):
        self.log = log or self._default_log
        self.position_loader = PositionDataLoader(log=log)
        self.timeline_reconstructor = PortfolioTimelineReconstructor(log=log)
        self.equity_extractor = EquityDataExtractor(log=log)

    def _default_log(self, message: str, level: str = "info") -> None:
        """Default logging function when none provided."""
        print(f"[{level.upper()}] {message}")

    def _create_mock_portfolio(
        self, combined_equity: pd.DataFrame, price_data: pd.DataFrame
    ):
        """Create a mock VectorBT portfolio from combined equity data."""

        # Create a simple mock object that has the necessary attributes for EquityDataExtractor
        class MockPortfolio:
            def __init__(self, equity_values, index):
                self._equity_values = equity_values
                self._index = index

            def value(self):
                """Return portfolio value series."""
                return pd.Series(self._equity_values, index=self._index)

            @property
            def wrapper(self):
                """Mock wrapper with index."""

                class MockWrapper:
                    def __init__(self, index):
                        self.index = index

                return MockWrapper(self._index)

            @property
            def trades(self):
                """Mock trades object with empty data."""

                class MockTrades:
                    @property
                    def entry_idx(self):
                        return np.array([])

                    @property
                    def exit_idx(self):
                        return np.array([])

                return MockTrades()

        # Extract equity values from combined_equity DataFrame
        equity_values = (
            combined_equity["Close"].values
            if "Close" in combined_equity.columns
            else combined_equity.iloc[:, 0].values
        )
        return MockPortfolio(equity_values, combined_equity.index)

    def generate_equity_data(
        self,
        portfolio_name: str,
        metric_type: MetricType = MetricType.MEAN,
        init_cash: float = 10000.0,
        config: Optional[Dict[str, Any]] = None,
    ) -> EquityData:
        """
        Generate equity curve data from position file.

        Args:
            portfolio_name: Name of portfolio (e.g., "live_signals")
            metric_type: Metric type for equity calculation
            init_cash: Initial cash for portfolio reconstruction
            config: Optional configuration dictionary

        Returns:
            EquityData object with comprehensive equity metrics

        Raises:
            TradingSystemError: If generation fails
        """
        try:
            self.log(
                f"Starting equity generation for portfolio: {portfolio_name}", "info"
            )

            # Load position data
            positions = self.position_loader.load_position_file(portfolio_name)

            if not positions:
                raise TradingSystemError(f"No positions found in {portfolio_name}")

            # Reconstruct portfolio timeline
            (
                combined_equity,
                price_data,
            ) = self.timeline_reconstructor.reconstruct_portfolio(positions, init_cash)

            # Create a mock VectorBT portfolio from combined equity data
            mock_portfolio = self._create_mock_portfolio(combined_equity, price_data)

            # Extract equity data using existing infrastructure
            equity_data = self.equity_extractor.extract_equity_data(
                mock_portfolio, metric_type, config
            )

            self.log(f"Successfully generated equity data for {portfolio_name}", "info")
            return equity_data

        except Exception as e:
            error_msg = f"Failed to generate equity data for {portfolio_name}: {str(e)}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def export_equity_data(
        self,
        portfolio_name: str,
        output_dir: Optional[str] = None,
        metric_type: MetricType = MetricType.MEAN,
        init_cash: float = 10000.0,
        config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Generate and export equity data to CSV file.

        Args:
            portfolio_name: Name of portfolio
            output_dir: Custom output directory (optional)
            metric_type: Metric type for equity calculation
            init_cash: Initial cash for portfolio reconstruction
            config: Optional configuration dictionary

        Returns:
            True if export successful, False otherwise
        """
        try:
            # Generate equity data
            equity_data = self.generate_equity_data(
                portfolio_name, metric_type, init_cash, config
            )

            # Determine output path
            if output_dir:
                export_dir = Path(output_dir)
            else:
                export_dir = Path(get_project_root()) / "csv" / "positions" / "equity"

            # Ensure directory exists
            export_dir.mkdir(parents=True, exist_ok=True)

            # Export to CSV
            filename = f"{portfolio_name}_equity.csv"
            file_path = export_dir / filename

            df = equity_data.to_dataframe()
            df.to_csv(file_path, index=False)

            self.log(f"Successfully exported equity data to: {file_path}", "info")
            self.log(f"Exported {len(df)} data points for {portfolio_name}", "info")

            return True

        except Exception as e:
            error_msg = f"Failed to export equity data for {portfolio_name}: {str(e)}"
            self.log(error_msg, "error")
            return False


def generate_position_equity(
    portfolio_name: str,
    output_dir: Optional[str] = None,
    metric_type: Union[str, MetricType] = MetricType.MEAN,
    init_cash: float = 10000.0,
    config: Optional[Dict[str, Any]] = None,
    log: Optional[Callable[[str, str], None]] = None,
) -> bool:
    """
    Convenience function for generating equity data from position files.

    Args:
        portfolio_name: Name of portfolio (e.g., "live_signals", "risk_on")
        output_dir: Custom output directory (optional)
        metric_type: Metric type for equity calculation
        init_cash: Initial cash for portfolio reconstruction
        config: Optional configuration dictionary
        log: Optional logging function

    Returns:
        True if generation successful, False otherwise
    """
    # Convert string metric type to enum
    if isinstance(metric_type, str):
        try:
            metric_type = MetricType(metric_type.lower())
        except ValueError:
            if log:
                log(f"Invalid metric type '{metric_type}', using 'mean'", "warning")
            metric_type = MetricType.MEAN

    # Create generator and export
    generator = PositionEquityGenerator(log=log)
    return generator.export_equity_data(
        portfolio_name, output_dir, metric_type, init_cash, config
    )
