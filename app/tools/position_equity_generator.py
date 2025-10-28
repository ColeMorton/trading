"""
Position Equity Generator Module

This module generates equity curves from position-level data by reconstructing
portfolio timelines and using VectorBT to calculate comprehensive equity metrics.

CLI Usage:
    # Generate equity data for a portfolio
    trading-cli positions equity --portfolio protected

    # Validate mathematical consistency
    trading-cli positions validate-equity --portfolio protected

    # Generate for multiple portfolios
    trading-cli positions equity --portfolio live_signals,risk_on,protected
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import vectorbt as vbt

from app.tools.equity_data_extractor import EquityData, EquityDataExtractor, MetricType
from app.tools.exceptions import TradingSystemError
from app.tools.portfolio_baseline_calculator import PortfolioBaselineCalculator
from app.tools.precision_fee_calculator import (
    PrecisionEquityCalculator,
    PrecisionFeeCalculator,
)
from app.tools.project_utils import get_project_root


@dataclass
class PositionEntry:
    """Represents a single position entry from position CSV file."""

    position_uuid: str
    ticker: str
    strategy_type: str
    fast_period: int
    slow_period: int
    signal_period: int
    entry_timestamp: datetime
    exit_timestamp: datetime | None
    avg_entry_price: float
    avg_exit_price: float | None
    position_size: float
    direction: str
    status: str
    pnl: float | None
    current_unrealized_pnl: float | None


class PositionDataLoader:
    """Loads and parses position data from CSV files."""

    def __init__(self, log: Callable[[str, str], None] | None = None):
        self.log = log or self._default_log
        self.positions_dir = Path(get_project_root()) / "data" / "raw" / "positions"

    def _default_log(self, message: str, level: str = "info") -> None:
        """Default logging function when none provided."""
        print(f"[{level.upper()}] {message}")

    def load_position_file(self, portfolio_name: str) -> list[PositionEntry]:
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
            error_msg = f"Failed to load position file {portfolio_name}: {e!s}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def _parse_position_row(self, row: pd.Series) -> PositionEntry:
        """Parse a single position row into PositionEntry object."""
        # Parse timestamps with robust date handling
        entry_timestamp = self._parse_timestamp_robust(row["Entry_Timestamp"])
        exit_timestamp = None
        if pd.notna(row.get("Exit_Timestamp")):
            exit_timestamp = self._parse_timestamp_robust(row["Exit_Timestamp"])

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
            fast_period=int(row["Fast_Period"]),
            slow_period=int(row["Slow_Period"]),
            signal_period=int(row.get("Signal_Period", 0)),
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

    def _parse_timestamp_robust(self, timestamp_str: str) -> datetime:
        """
        Parse timestamp with fallback for malformed dates.

        Handles formats like:
        - "2025-06-16 00:00:00" (standard)
        - "20250620 00:00:00" (malformed - missing hyphens)
        """
        if pd.isna(timestamp_str):
            raise ValueError("Timestamp is NaN")

        timestamp_str = str(timestamp_str).strip()

        try:
            # Try standard pandas parsing first
            return pd.to_datetime(timestamp_str)
        except Exception:
            # Handle malformed dates like "20250620 00:00:00"
            try:
                # Check if it's the problematic format (8 digits + time)
                if len(timestamp_str) >= 8 and timestamp_str[:8].isdigit():
                    date_part = timestamp_str[:8]  # YYYYMMDD
                    time_part = timestamp_str[8:].strip()  # " 00:00:00"

                    # Insert hyphens: YYYYMMDD -> YYYY-MM-DD
                    formatted_date = (
                        f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                    )
                    formatted_timestamp = f"{formatted_date}{time_part}"

                    self.log(
                        f"Fixed malformed date: '{timestamp_str}' -> '{formatted_timestamp}'",
                        "debug",
                    )
                    return pd.to_datetime(formatted_timestamp)
                # Try other common formats
                return pd.to_datetime(timestamp_str, format="mixed")
            except Exception as e:
                self.log(f"Failed to parse timestamp '{timestamp_str}': {e!s}", "error")
                raise ValueError(f"Unable to parse timestamp: {timestamp_str}") from e


class DirectEquityCalculator:
    """
    Calculates equity curves directly from position data without portfolio simulation.

    This approach provides mathematically exact equity curves by:
    1. Only changing equity on actual entry/exit events
    2. Using exact entry/exit prices from position data
    3. Applying transaction fees directly
    4. Avoiding VectorBT portfolio simulation complexity
    """

    def __init__(self, log: Callable[[str, str], None] | None = None):
        self.log = log or self._default_log
        self.fee_rate = 0.001  # 0.1% transaction fee
        self.precision_fee_calculator = PrecisionFeeCalculator(self.fee_rate)
        self.precision_equity_calculator = PrecisionEquityCalculator(self.fee_rate)
        self.baseline_calculator = PortfolioBaselineCalculator(self.fee_rate)
        self._positions_cache: list[dict[str, Any]] = (
            []
        )  # Cache for position data access

    def _default_log(self, message: str, level: str = "info") -> None:
        """Default logging function when none provided."""
        print(f"[{level.upper()}] {message}")

    def calculate_equity_timeline(
        self, positions: list[PositionEntry], init_cash: float = 10000.0
    ) -> pd.DataFrame:
        """
        Calculate equity timeline from position events.

        Args:
            positions: List of position entries
            init_cash: Initial cash (will be calculated from position entry values)

        Returns:
            DataFrame with daily equity values
        """
        # Cache positions for current value calculations
        self._positions_cache = positions

        # Process all position events chronologically
        events = self._process_position_events(positions)

        if not events:
            raise TradingSystemError("No position events to process")

        # Sort events by timestamp
        events.sort(key=lambda x: x["timestamp"])

        # Calculate required starting cash using sophisticated cash flow analysis
        required_starting_cash = self._calculate_total_entry_cost(positions)
        portfolio_value = required_starting_cash  # Start with required capital for chronological execution

        self.log(f"Starting portfolio value: ${portfolio_value:.2f}", "info")

        # Track cash and positions
        cash = portfolio_value
        open_positions = {}  # position_uuid -> position details

        # Build equity timeline - group events by date to handle multiple events per day
        equity_timeline: list[dict[str, Any]] = []

        for event in events:
            timestamp = event["timestamp"]
            event_date = timestamp.date()

            if event["type"] == "entry":
                # Position entry with high-precision calculations
                cash_flow = self.precision_equity_calculator.calculate_cash_flow(
                    "entry", event["price"], event["size"]
                )
                entry_cost = float(cash_flow["gross_amount"])
                entry_fee = float(cash_flow["fee"])
                total_cost = float(-cash_flow["net_cash_flow"])  # Convert to positive

                # Check if we have enough cash
                if cash < total_cost:
                    self.log(
                        f"Warning: Insufficient cash for {event['ticker']} entry",
                        "warning",
                    )
                    continue

                # Update cash and track position
                cash -= total_cost
                open_positions[event["position_uuid"]] = {
                    "ticker": event["ticker"],
                    "size": event["size"],
                    "entry_price": event["price"],
                    "entry_cost": entry_cost,
                }

                self.log(
                    f"{event_date}: Entry {event['ticker']} - Cost: ${entry_cost:.2f}, Fee: ${entry_fee:.2f}",
                    "debug",
                )

            elif event["type"] == "exit":
                # Position exit with high-precision calculations
                if event["position_uuid"] not in open_positions:
                    self.log(
                        f"Warning: Exit without entry for {event['position_uuid']}",
                        "warning",
                    )
                    continue

                position = open_positions.pop(event["position_uuid"])

                # Use precision calculator for exit
                cash_flow = self.precision_equity_calculator.calculate_cash_flow(
                    "exit", event["price"], position["size"]
                )
                exit_proceeds = float(cash_flow["gross_amount"])
                exit_fee = float(cash_flow["fee"])
                net_proceeds = float(cash_flow["net_cash_flow"])

                # Update cash
                cash += net_proceeds

                # Calculate P&L for logging with precision
                pnl_breakdown = self.precision_fee_calculator.calculate_net_pnl(
                    position["entry_price"], event["price"], position["size"]
                )
                net_pnl = float(pnl_breakdown["net_pnl"])

                self.log(
                    f"{event_date}: Exit {position['ticker']} - "
                    f"Proceeds: ${exit_proceeds:.2f}, Fee: ${exit_fee:.2f}, Net P&L: ${net_pnl:.2f}",
                    "debug",
                )

            # Only add one entry per day (last event for that day)
            # Calculate total portfolio value (cash + open positions at current market value)
            positions_value = self._calculate_open_positions_current_value(
                open_positions, timestamp
            )
            current_value = cash + positions_value

            # Check if this is a new date or update existing date
            if equity_timeline and equity_timeline[-1]["date"] == event_date:
                # Update the existing entry for this date
                equity_timeline[-1].update(
                    {
                        "timestamp": timestamp,
                        "cash": cash,
                        "positions_value": positions_value,
                        "total_value": current_value,
                        "num_open_positions": len(open_positions),
                    }
                )
            else:
                # Add new entry for this date
                equity_timeline.append(
                    {
                        "date": event_date,
                        "timestamp": timestamp,
                        "cash": cash,
                        "positions_value": positions_value,
                        "total_value": current_value,
                        "num_open_positions": len(open_positions),
                    }
                )

        # Convert to DataFrame and clean up
        equity_df = pd.DataFrame(equity_timeline)
        equity_df = equity_df.drop(
            "date", axis=1
        )  # Remove date column used for grouping
        equity_df.set_index("timestamp", inplace=True)

        # Generate daily timeline
        daily_equity = self._generate_daily_equity(equity_df)

        return daily_equity

    def _process_position_events(self, positions: list[PositionEntry]) -> list[dict]:
        """Convert positions to chronological entry/exit events."""
        events = []

        for position in positions:
            # Entry event
            events.append(
                {
                    "timestamp": position.entry_timestamp,
                    "type": "entry",
                    "ticker": position.ticker,
                    "position_uuid": position.position_uuid,
                    "price": position.avg_entry_price,
                    "size": position.position_size,
                    "direction": position.direction,
                }
            )

            # Exit event (only for closed positions)
            if (
                position.status == "Closed"
                and position.exit_timestamp
                and position.avg_exit_price
            ):
                events.append(
                    {
                        "timestamp": position.exit_timestamp,
                        "type": "exit",
                        "ticker": position.ticker,
                        "position_uuid": position.position_uuid,
                        "price": position.avg_exit_price,
                        "size": position.position_size,
                        "direction": position.direction,
                    }
                )

        return events

    def _calculate_open_positions_current_value(
        self, open_positions: dict, current_timestamp: datetime
    ) -> float:
        """
        Calculate current market value of open positions using unrealized P&L data.

        Args:
            open_positions: Dictionary of open positions {position_uuid: position_details}
            current_timestamp: Current timestamp for valuation

        Returns:
            Current market value of all open positions
        """
        from decimal import Decimal

        total_current_value = Decimal("0")

        for position_uuid, position_details in open_positions.items():
            ticker = position_details["ticker"]
            entry_cost = Decimal(str(position_details["entry_cost"]))

            # Find the corresponding position entry to get unrealized P&L
            matching_position = None
            for pos in self._positions_cache:
                if pos.position_uuid == position_uuid:
                    matching_position = pos
                    break

            if (
                matching_position
                and matching_position.current_unrealized_pnl is not None
            ):
                # Use current unrealized P&L to calculate current market value
                unrealized_pnl = Decimal(str(matching_position.current_unrealized_pnl))
                current_value = entry_cost + unrealized_pnl

                self.log(
                    f"  {ticker}: Entry cost ${entry_cost:.2f} + Unrealized P&L ${unrealized_pnl:.2f} = Current value ${current_value:.2f}",
                    "debug",
                )
            else:
                # Fallback to entry cost if no unrealized P&L available
                current_value = entry_cost
                self.log(
                    f"  {ticker}: Using entry cost ${entry_cost:.2f} (no unrealized P&L available)",
                    "debug",
                )

            total_current_value += current_value

        return float(total_current_value)

    def _calculate_total_entry_cost(self, positions: list[PositionEntry]) -> float:
        """Calculate required starting cash using sophisticated cash flow analysis."""
        # Use baseline calculator for accurate starting value methodology
        baseline_calc = self.baseline_calculator.calculate_required_starting_cash(
            positions
        )

        required_cash = float(baseline_calc["required_starting_cash"])
        total_entry_costs = float(baseline_calc["total_entry_costs"])

        self.log(
            f"Cash flow analysis: Required starting cash: ${required_cash:.2f}, "
            f"Total entry costs: ${total_entry_costs:.2f}, "
            f"Max cash deficit: ${float(baseline_calc['max_cash_deficit']):.2f}",
            "info",
        )

        # Check for cash adequacy warnings
        adequacy_analysis = self.baseline_calculator.analyze_cash_flow_adequacy(
            positions
        )
        if not adequacy_analysis["is_adequate"]:
            failed_count = len(adequacy_analysis["failed_transactions"])
            self.log(
                f"WARNING: {failed_count} transactions would fail with current cash flow methodology",
                "warning",
            )
            for failed in adequacy_analysis["failed_transactions"][
                :3
            ]:  # Show first 3 failures
                self.log(
                    f"  Failed: {failed['ticker']} on {failed['timestamp']} (shortfall: ${failed['shortfall']:.2f})",
                    "warning",
                )

        # Use required starting cash (accounts for chronological cash flows)
        # Add small buffer to account for precision differences during execution
        buffer_amount = 1.0  # $1 buffer for rounding precision
        final_cash = required_cash + buffer_amount

        self.log(
            f"Final starting cash: ${final_cash:.2f} (required: ${required_cash:.2f} + ${buffer_amount:.2f} buffer)",
            "info",
        )

        return final_cash

    def _generate_daily_equity(self, equity_df: pd.DataFrame) -> pd.DataFrame:
        """Generate daily equity values by forward-filling between events."""
        if equity_df.empty:
            return equity_df

        # Create date range from first to last event
        start_date = equity_df.index.min()
        end_date = equity_df.index.max()

        # Generate daily date range
        daily_dates = pd.date_range(start=start_date, end=end_date, freq="D")

        # Reindex to daily frequency and forward fill
        daily_equity = equity_df.reindex(daily_dates).ffill()

        # Fill any remaining NaN values at the beginning
        daily_equity = daily_equity.bfill()

        return daily_equity

    def reconstruct_portfolio(
        self, positions: list[PositionEntry], init_cash: float = 10000.0
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Calculate portfolio equity curve directly from position data.

        This method calculates equity curves without portfolio simulation by:
        1. Processing only actual entry/exit events
        2. Using exact entry/exit prices from position data
        3. Applying transaction fees directly

        Args:
            positions: List of position entries
            init_cash: Initial cash (recalculated from position entry values)

        Returns:
            Tuple of (equity DataFrame, dummy price DataFrame for compatibility)

        Raises:
            TradingSystemError: If calculation fails
        """
        try:
            if not positions:
                raise TradingSystemError("No positions provided for reconstruction")

            self.log(f"Calculating equity for {len(positions)} positions", "info")

            # Calculate equity timeline directly
            daily_equity = self.calculate_equity_timeline(positions, init_cash)

            # Create equity DataFrame in expected format
            equity_changes = (
                daily_equity["total_value"] - daily_equity["total_value"].iloc[0]
            )

            combined_equity = pd.DataFrame(
                {
                    "Close": equity_changes,  # Equity changes indexed at 0
                    "portfolio_value": daily_equity[
                        "total_value"
                    ],  # Actual portfolio values
                    "starting_value": daily_equity["total_value"].iloc[
                        0
                    ],  # Starting value
                },
                index=daily_equity.index,
            )

            # Create dummy price DataFrame for compatibility (not used)
            dummy_prices = pd.DataFrame(
                {"Close": [100.0] * len(daily_equity)},  # Dummy data
                index=daily_equity.index,
            )

            final_value = daily_equity["total_value"].iloc[-1]
            starting_value = daily_equity["total_value"].iloc[0]
            total_change = final_value - starting_value

            self.log(
                f"Portfolio starting value: ${starting_value:.2f}, "
                f"Final value: ${final_value:.2f}, "
                f"Total change: ${total_change:.2f}",
                "info",
            )

            return combined_equity, dummy_prices

        except Exception as e:
            error_msg = f"Failed to calculate portfolio equity: {e!s}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def _calculate_position_based_allocation(
        self, ticker_positions: dict[str, list[PositionEntry]]
    ) -> dict[str, float]:
        """
        Calculate the actual cash allocation for each ticker based on position entry values.

        Args:
            ticker_positions: Dictionary mapping tickers to their position lists

        Returns:
            Dictionary mapping tickers to their required cash allocation
        """
        ticker_cash_allocation = {}

        for ticker, positions in ticker_positions.items():
            total_cash_needed = 0.0

            for position in positions:
                # Calculate the cash needed for this position at entry
                position_value = position.avg_entry_price * position.position_size
                total_cash_needed += position_value

                self.log(
                    f"{ticker} position: ${position.avg_entry_price:.2f} × {position.position_size} = ${position_value:.2f}",
                    "debug",
                )

            ticker_cash_allocation[ticker] = total_cash_needed
            self.log(f"{ticker} total allocation: ${total_cash_needed:.2f}", "info")

        return ticker_cash_allocation

    def _load_combined_prices(
        self, tickers: list[str], positions: list[PositionEntry]
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
        price_file = self.prices_dir / f"{primary_ticker}_D.csv"

        if not price_file.exists():
            raise TradingSystemError(
                f"Price data not found for {primary_ticker}: {price_file}"
            )

        prices = pd.read_csv(price_file)
        prices["Date"] = pd.to_datetime(prices["Date"])
        prices = prices.set_index("Date")

        # Filter to relevant date range
        prices = prices[(prices.index >= start_date) & (prices.index <= end_date)]

        if prices.empty:
            raise TradingSystemError(
                f"No price data in date range {start_date} to {end_date}"
            )

        self.log(
            f"Loaded price data from {start_date} to {end_date} ({len(price_data)} days)",
            "info",
        )
        return prices

    def _create_order_sequence(
        self, positions: list[PositionEntry], prices: pd.DataFrame
    ) -> pd.DataFrame:
        """Create chronological order sequence from positions."""
        orders = []

        for position in positions:
            # Entry order
            entry_order = {
                "timestamp": position.entry_timestamp,
                "ticker": position.ticker,
                "size": (
                    position.position_size
                    if position.direction == "Long"
                    else -position.position_size
                ),
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
                    "size": (
                        -position.position_size
                        if position.direction == "Long"
                        else position.position_size
                    ),
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
        self, orders_df: pd.DataFrame, prices: pd.DataFrame, init_cash: float
    ) -> vbt.Portfolio:
        """Create VectorBT portfolio from order sequence."""
        try:
            # Align orders with price data timeline
            aligned_orders = self._align_orders_with_prices(orders_df, prices)

            # CRITICAL FIX: Override close prices on execution dates to match actual execution prices
            # VectorBT's price parameter doesn't work as expected - it still uses close prices for valuation
            modified_close_prices = prices["Close"].copy()

            for date, row in aligned_orders.iterrows():
                if row["size"] != 0 and pd.notna(row["price"]):
                    # Override the close price on this date to match our execution price
                    modified_close_prices[date] = row["price"]
                    self.log(
                        f"Overriding close price on {date.date()}: ${prices['Close'][date]:.2f} -> ${row['price']:.2f}",
                        "debug",
                    )

            # Create VectorBT portfolio using modified close prices
            portfolio = vbt.Portfolio.from_orders(
                close=modified_close_prices,
                size=aligned_orders["size"],
                init_cash=init_cash,
                fees=0.001,  # 0.1% transaction fee
                freq="D",
            )

            return portfolio

        except Exception as e:
            raise TradingSystemError(
                f"Failed to create VectorBT portfolio: {e!s}"
            ) from e

    def _align_orders_with_prices(
        self, orders_df: pd.DataFrame, prices: pd.DataFrame
    ) -> pd.DataFrame:
        """Align orders with price data timeline."""
        # Create series aligned with price data index
        size_series = pd.Series(0.0, index=prices.index)
        price_series = pd.Series(np.nan, index=prices.index)

        for _, order in orders_df.iterrows():
            order_date = pd.to_datetime(order["timestamp"]).date()

            # Find closest trading day
            matching_dates = [idx for idx in prices.index if idx.date() == order_date]

            if matching_dates:
                order_idx = matching_dates[0]
                size_series[order_idx] += order["size"]
                price_series[order_idx] = order["price"]

        return pd.DataFrame({"size": size_series, "price": price_series})

    def _create_ticker_portfolio(
        self, ticker: str, positions: list[PositionEntry], allocated_cash: float
    ) -> tuple[vbt.Portfolio, pd.DataFrame]:
        """Create VectorBT portfolio for a single ticker."""
        try:
            # Load price data for this ticker
            price_file = self.prices_dir / f"{ticker}_D.csv"
            prices = pd.read_csv(price_file)
            prices["Date"] = pd.to_datetime(prices["Date"])
            prices = prices.set_index("Date")

            # Determine date range from positions
            start_date = min(pos.entry_timestamp for pos in positions)
            end_date = max(
                pos.exit_timestamp if pos.exit_timestamp else datetime.now()
                for pos in positions
            )

            # Filter price data to relevant range
            prices = prices[(prices.index >= start_date) & (prices.index <= end_date)]

            if prices.empty:
                raise TradingSystemError(
                    f"No price data for {ticker} in date range {start_date} to {end_date}"
                )

            # Create order sequence for this ticker
            orders_df = self._create_ticker_order_sequence(positions, prices)

            if orders_df.empty:
                raise TradingSystemError(f"No valid orders for {ticker}")

            # Create VectorBT portfolio
            portfolio = self._create_vectorbt_portfolio(
                orders_df, prices, allocated_cash
            )

            return portfolio, prices

        except Exception as e:
            raise TradingSystemError(
                f"Failed to create portfolio for {ticker}: {e!s}"
            ) from e

    def _create_ticker_order_sequence(
        self, positions: list[PositionEntry], prices: pd.DataFrame
    ) -> pd.DataFrame:
        """Create order sequence for a single ticker."""
        orders = []

        for position in positions:
            # Entry order
            entry_order = {
                "timestamp": position.entry_timestamp,
                "size": (
                    position.position_size
                    if position.direction == "Long"
                    else -position.position_size
                ),
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
                    "size": (
                        -position.position_size
                        if position.direction == "Long"
                        else position.position_size
                    ),
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
        ticker_equity_curves: dict[str, dict],
        all_prices: dict[str, pd.DataFrame],
        ticker_position_data: dict[str, dict],
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
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

            # Calculate total portfolio starting value from actual positions
            total_portfolio_starting_value = sum(
                ticker_position_data[ticker]["allocated_cash"]
                for ticker in ticker_equity_curves
                if ticker in ticker_position_data
            )

            # Combine equity curves using actual position-based values
            combined_equity_values = pd.Series(0.0, index=union_index)

            for ticker, curve_data in ticker_equity_curves.items():
                if ticker not in ticker_position_data:
                    self.log(
                        f"Skipping {ticker} - no position data available", "warning"
                    )
                    continue

                # Get the actual cash allocation for this ticker
                ticker_initial_value = ticker_position_data[ticker]["allocated_cash"]

                # Create equity series for this ticker (VectorBT returns indexed at 0)
                ticker_equity = pd.Series(
                    curve_data["equity"], index=curve_data["index"]
                )

                # VectorBT portfolio.value() already returns absolute portfolio values
                # No need to add initial allocation - ticker_equity is already absolute values
                ticker_actual_values = ticker_equity

                # Reindex to union_index
                ticker_aligned = ticker_actual_values.reindex(union_index)

                # For dates before this ticker's first date, use initial cash allocation
                first_date = ticker_equity.index.min()
                ticker_aligned.loc[ticker_aligned.index < first_date] = (
                    ticker_initial_value
                )

                # Forward fill remaining NaN values
                ticker_aligned = ticker_aligned.ffill()

                # Backward fill any remaining NaN values at the beginning
                ticker_aligned = ticker_aligned.bfill()

                # Add this ticker's contribution to total
                combined_equity_values += ticker_aligned

                self.log(
                    f"{ticker}: Initial ${ticker_initial_value:.2f}, Final ${ticker_aligned.iloc[-1]:.2f}",
                    "debug",
                )

            # Convert combined values back to VectorBT format (indexed at 0)
            (combined_equity_values - total_portfolio_starting_value)

            # Create combined price data using first ticker as reference, extended to full date range
            first_ticker = next(iter(all_prices.keys()))
            reference_prices = all_prices[first_ticker]

            # Reindex reference price data to union_index
            combined_prices = reference_prices.reindex(union_index).ffill()
            combined_prices = combined_prices.bfill()

            # Create equity DataFrame with Close prices for VectorBT compatibility
            # Use actual portfolio values since VectorBT expects absolute values
            combined_equity = pd.DataFrame(
                {
                    "Close": combined_equity_values,  # Use actual values, not changes
                    "portfolio_value": combined_equity_values,  # Keep actual values for reference
                    "starting_value": total_portfolio_starting_value,  # Store starting value
                },
                index=union_index,
            )

            self.log(
                f"Combined equity curves across {len(union_index)} dates from {len(ticker_equity_curves)} tickers",
                "info",
            )
            total_change = (
                combined_equity_values.iloc[-1] - total_portfolio_starting_value
            )
            self.log(
                f"Portfolio starting value: ${total_portfolio_starting_value:.2f}, "
                f"Final value: ${combined_equity_values.iloc[-1]:.2f}, "
                f"Total change: ${total_change:.2f}",
                "info",
            )
            return combined_equity, combined_prices

        except Exception as e:
            raise TradingSystemError(f"Failed to combine equity curves: {e!s}") from e


class PositionEquityGenerator:
    """Main class for generating equity curves from position data."""

    def __init__(self, log: Callable[[str, str], None] | None = None):
        self.log = log or self._default_log
        self.position_loader = PositionDataLoader(log=log)
        self.equity_calculator = DirectEquityCalculator(log=log)
        self.equity_extractor = EquityDataExtractor(log=log)

    def _default_log(self, message: str, level: str = "info") -> None:
        """Default logging function when none provided."""
        print(f"[{level.upper()}] {message}")

    def _create_mock_portfolio(
        self, combined_equity: pd.DataFrame, prices: pd.DataFrame
    ):
        """Create a mock VectorBT portfolio from combined equity data."""

        # Create a simple mock object that has the necessary attributes for EquityDataExtractor
        class MockPortfolio:
            def __init__(self, equity_values, index, starting_value):
                self._equity_values = equity_values
                self._index = index
                self._starting_value = starting_value

            def value(self):
                """Return portfolio value series."""
                # The equity values are already absolute portfolio values from VectorBT
                # EquityDataExtractor expects actual portfolio values
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

        # Extract actual portfolio values from combined_equity DataFrame
        portfolio_values = (
            combined_equity["Close"].values
            if "Close" in combined_equity.columns
            else combined_equity.iloc[:, 0].values
        )

        starting_value = (
            combined_equity["starting_value"].iloc[0]
            if "starting_value" in combined_equity.columns
            else 0.0
        )

        return MockPortfolio(portfolio_values, combined_equity.index, starting_value)

    def generate_equity_data(
        self,
        portfolio_name: str,
        metric_type: MetricType = MetricType.MEAN,
        init_cash: float = 10000.0,
        config: dict[str, Any] | None = None,
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

            # Calculate portfolio equity directly
            (
                combined_equity,
                price_data,
            ) = self.equity_calculator.reconstruct_portfolio(positions, init_cash)

            # Create a mock VectorBT portfolio from combined equity data
            mock_portfolio = self._create_mock_portfolio(combined_equity, prices)

            # Extract equity data using existing infrastructure
            equity_data = self.equity_extractor.extract_equity_data(
                mock_portfolio, metric_type, config
            )

            self.log(f"Successfully generated equity data for {portfolio_name}", "info")
            return equity_data

        except Exception as e:
            error_msg = f"Failed to generate equity data for {portfolio_name}: {e!s}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def export_equity_data(
        self,
        portfolio_name: str,
        output_dir: str | None = None,
        metric_type: MetricType = MetricType.MEAN,
        init_cash: float = 10000.0,
        config: dict[str, Any] | None = None,
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
            error_msg = f"Failed to export equity data for {portfolio_name}: {e!s}"
            self.log(error_msg, "error")
            return False


def generate_position_equity(
    portfolio_name: str,
    output_dir: str | None = None,
    metric_type: str | MetricType = MetricType.MEAN,
    init_cash: float = 10000.0,
    config: dict[str, Any] | None = None,
    log: Callable[[str, str], None] | None = None,
) -> bool:
    """
    Convenience function for generating equity data from position files.

    DEPRECATED: Use CLI interface instead:
        trading-cli positions equity --portfolio <portfolio_name>

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
