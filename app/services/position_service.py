"""
Unified Position Service

Single entry point for all position-related operations, replacing multiple
parallel implementations with a consolidated, well-structured service.

This service consolidates functionality from:
- generalized_trade_history_exporter.py
- trade_history_csv_exporter.py
- trade_history_close_live_signal.py
"""

from datetime import datetime
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from ..cli.utils import resolve_portfolio_path
from ..exceptions import (
    CalculationError,
    DataNotFoundError,
    PortfolioError,
    PriceDataError,
    SignalValidationError,
    ValidationError,
)
from ..tools.position_calculator import get_position_calculator
from ..tools.utils.mfe_mae_calculator import get_mfe_mae_calculator
from ..tools.uuid_utils import generate_position_uuid


class TradingSystemConfig:
    """Configuration for trading system file paths and settings."""

    def __init__(self, base_dir: str | None = None):
        """Initialize configuration with base directory."""
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

    @property
    def prices_dir(self) -> Path:
        """Directory containing price data files."""
        return self.base_dir / "data" / "raw" / "prices"

    @property
    def positions_dir(self) -> Path:
        """Directory for position-level CSV files."""
        return self.base_dir / "data" / "raw" / "positions"

    @property
    def trade_history_dir(self) -> Path:
        """Directory for JSON trade history files."""
        return self.base_dir / "data" / "raw" / "reports" / "trade_history"

    def get_prices_file(self, ticker: str, timeframe: str = "D") -> Path:
        """Get price data file path for any ticker and timeframe."""
        return self.prices_dir / f"{ticker}_{timeframe}.csv"

    def get_portfolio_file(self, portfolio_name: str) -> Path:
        """Get portfolio positions file path."""
        return self.positions_dir / resolve_portfolio_path(portfolio_name)

    def ensure_directories(self):
        """Create all required directories if they don't exist."""
        for directory in [self.prices_dir, self.positions_dir, self.trade_history_dir]:
            directory.mkdir(parents=True, exist_ok=True)


class PositionService:
    """
    Unified service for all position-related operations.

    Provides single entry point for:
    - Position creation and management
    - Portfolio operations
    - Risk calculations (MFE/MAE)
    - Signal validation
    - Trade history analysis
    """

    def __init__(
        self, config: TradingSystemConfig = None, logger: logging.Logger | None = None,
    ):
        """Initialize the position service."""
        self.config = config or TradingSystemConfig()
        self.logger = logger or logging.getLogger(__name__)
        self.calculator = get_position_calculator(self.logger)
        self.mfe_mae_calculator = get_mfe_mae_calculator(self.logger)

        # Ensure required directories exist
        self.config.ensure_directories()

    def validate_ticker(self, ticker: str) -> None:
        """Validate ticker symbol format."""
        if not ticker or not isinstance(ticker, str):
            msg = "Ticker must be a non-empty string"
            raise ValidationError(msg)

        # Basic validation - alphanumeric with optional separators
        clean_ticker = ticker.replace("-", "").replace(".", "").replace("_", "")
        if not clean_ticker.isalnum():
            msg = f"Invalid ticker format: {ticker}"
            raise ValidationError(msg)

    def validate_strategy_type(self, strategy_type: str) -> None:
        """Validate strategy type."""
        valid_strategies = ["SMA", "EMA", "MACD", "RSI", "BOLLINGER", "STOCHASTIC"]
        if strategy_type.upper() not in valid_strategies:
            msg = (
                f"Invalid strategy type: {strategy_type}. "
                f"Valid types: {', '.join(valid_strategies)}"
            )
            raise ValidationError(
                msg,
            )

    def validate_date_string(self, date_str: str) -> None:
        """Validate date string format."""
        try:
            if " " in date_str:
                # Try with timestamp
                date_part = date_str.split(" ")[0]
                if len(date_part) == 8 and date_part.isdigit():
                    datetime.strptime(date_str, "%Y%m%d %H:%M:%S")
                else:
                    datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            # Try YYYYMMDD format first, then YYYY-MM-DD
            elif len(date_str) == 8 and date_str.isdigit():
                datetime.strptime(date_str, "%Y%m%d")
            else:
                datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            msg = f"Invalid date format: {date_str}"
            raise ValidationError(msg)

    def calculate_mfe_mae(
        self,
        ticker: str,
        entry_date: str,
        exit_date: str,
        entry_price: float,
        direction: str = "Long",
        timeframe: str = "D",
    ) -> tuple[float | None, float | None, float | None]:
        """
        Calculate Max Favourable Excursion and Max Adverse Excursion.

        Args:
            ticker: Stock/asset ticker symbol
            entry_date: Position entry date
            exit_date: Position exit date (empty for open positions)
            entry_price: Entry price for position
            direction: Position direction ('Long' or 'Short')
            timeframe: Price data timeframe

        Returns:
            Tuple of (mfe, mae, mfe_mae_ratio)
        """
        # Validate inputs
        self.validate_ticker(ticker)
        self.validate_date_string(entry_date)

        if exit_date and exit_date.strip():
            self.validate_date_string(exit_date)

        if entry_price <= 0:
            msg = f"Invalid entry price: {entry_price}"
            raise ValidationError(msg)

        try:
            # Load price data
            price_file = self.config.get_prices_file(ticker, timeframe)
            if not price_file.exists():
                msg = f"Price data not found for {ticker} at {price_file}"
                raise PriceDataError(
                    msg,
                )

            # Read price data
            df = pd.read_csv(price_file)

            # Clean data: Remove ticker symbol row (row with string values instead of numeric data)
            # Price data files have format: header, ticker_symbols_row, actual_data...
            # Filter out rows where numeric columns contain string values
            numeric_cols = ["High", "Low", "Open", "Close"]
            for col in numeric_cols:
                if col in df.columns:
                    # Convert to numeric, coercing errors (strings) to NaN
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            # Remove rows with NaN values in High/Low (these are the ticker symbol rows)
            df = df.dropna(subset=["High", "Low"])

            # Ensure we have valid data after cleaning
            if df.empty:
                msg = f"No valid numeric price data found for {ticker} after cleaning"
                raise PriceDataError(
                    msg,
                )

            df["Date"] = pd.to_datetime(df["Date"])

            # Convert dates
            entry_dt = pd.to_datetime(entry_date.split(" ")[0])
            exit_dt = pd.Timestamp.now()

            if exit_date and exit_date.strip():
                try:
                    exit_dt = pd.to_datetime(exit_date.split(" ")[0])
                except (ValueError, AttributeError):
                    self.logger.warning(
                        f"Cannot parse exit date: {exit_date}, using current date",
                    )

            # Filter to position period
            position_df = df[(df["Date"] >= entry_dt) & (df["Date"] <= exit_dt)].copy()

            if position_df.empty:
                msg = f"No price data found for {ticker} between {entry_date} and {exit_date or 'now'}"
                raise PriceDataError(
                    msg,
                )

            # Calculate MFE/MAE using centralized calculator
            mfe, mae = self.mfe_mae_calculator.calculate_from_ohlc(
                entry_price=entry_price,
                ohlc_data=position_df,
                direction=direction,
                high_col="High",
                low_col="Low",
            )

            # Calculate ratio
            mfe_mae_ratio = mfe / mae if mae != 0 else None

            return mfe, mae, mfe_mae_ratio

        except Exception as e:
            if isinstance(e, ValidationError | PriceDataError):
                raise
            msg = f"Error calculating MFE/MAE for {ticker}: {e}"
            raise CalculationError(msg)

    def verify_entry_signal(
        self,
        ticker: str,
        strategy_type: str,
        fast_period: int,
        slow_period: int,
        entry_date: str,
        direction: str = "Long",
        timeframe: str = "D",
    ) -> dict[str, Any]:
        """
        Verify that entry signal actually occurred on specified date.

        Args:
            ticker: Stock/asset ticker symbol
            strategy_type: Strategy type ('SMA', 'EMA', etc.)
            fast_period: Short period window
            slow_period: Long period window
            entry_date: Entry date to verify
            direction: Position direction
            timeframe: Price data timeframe

        Returns:
            Dict with verification results and signal details
        """
        # Validate inputs
        self.validate_ticker(ticker)
        self.validate_strategy_type(strategy_type)
        self.validate_date_string(entry_date)

        try:
            # Load price data
            price_file = self.config.get_prices_file(ticker, timeframe)
            if not price_file.exists():
                msg = f"Price data not found for {ticker}"
                raise PriceDataError(msg)

            df = pd.read_csv(price_file)
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")

            # Calculate moving averages
            if strategy_type.upper() == "SMA":
                df[f"MA_{fast_period}"] = df["Close"].rolling(window=fast_period).mean()
                df[f"MA_{slow_period}"] = df["Close"].rolling(window=slow_period).mean()
            elif strategy_type.upper() == "EMA":
                df[f"MA_{fast_period}"] = df["Close"].ewm(span=fast_period).mean()
                df[f"MA_{slow_period}"] = df["Close"].ewm(span=slow_period).mean()
            else:
                msg = f"Signal verification not implemented for {strategy_type}"
                raise ValidationError(
                    msg,
                )

            # Find entry date in data
            entry_dt = pd.to_datetime(entry_date.split(" ")[0])

            if entry_dt not in df.index:
                msg = f"Entry date {entry_date} not found in price data"
                raise DataNotFoundError(
                    msg,
                )

            # Check for crossover signal
            entry_row = df.loc[entry_dt]

            # Get previous day for crossover detection
            prev_dates = df.index[df.index < entry_dt]
            if len(prev_dates) == 0:
                msg = "No previous data available for crossover detection"
                raise DataNotFoundError(
                    msg,
                )

            prev_dt = prev_dates[-1]
            prev_row = df.loc[prev_dt]

            current_short = entry_row[f"MA_{fast_period}"]
            current_long = entry_row[f"MA_{slow_period}"]
            prev_short = prev_row[f"MA_{fast_period}"]
            prev_long = prev_row[f"MA_{slow_period}"]

            # Check crossover conditions
            bullish_crossover = (current_short > current_long) and (
                prev_short <= prev_long
            )
            bearish_crossover = (current_short < current_long) and (
                prev_short >= prev_long
            )

            signal_verified = False
            signal_type = None

            if direction.upper() == "LONG" and bullish_crossover:
                signal_verified = True
                signal_type = "Bullish Crossover"
            elif direction.upper() == "SHORT" and bearish_crossover:
                signal_verified = True
                signal_type = "Bearish Crossover"

            return {
                "verified": signal_verified,
                "signal_type": signal_type,
                "entry_date": entry_date,
                "short_ma": current_short,
                "long_ma": current_long,
                "prev_short_ma": prev_short,
                "prev_long_ma": prev_long,
                "spread": current_short - current_long,
                "prev_spread": prev_short - prev_long,
            }

        except Exception as e:
            if isinstance(e, ValidationError | DataNotFoundError | PriceDataError):
                raise
            msg = f"Error verifying signal for {ticker}: {e}"
            raise SignalValidationError(msg)

    def create_position_record(
        self,
        ticker: str,
        strategy_type: str,
        fast_period: int,
        slow_period: int,
        signal_period: int = 0,
        entry_date: str | None = None,
        entry_price: float | None = None,
        exit_date: str | None = None,
        exit_price: float | None = None,
        position_size: float = 1.0,
        direction: str = "Long",
    ) -> dict[str, Any]:
        """
        Create a complete position record with all calculated fields.

        Args:
            ticker: Stock/asset ticker symbol
            strategy_type: Strategy type
            fast_period: Short period window
            slow_period: Long period window
            signal_period: Signal period (default 0)
            entry_date: Entry date
            entry_price: Entry price
            exit_date: Exit date (None for open positions)
            exit_price: Exit price (None for open positions)
            position_size: Position size
            direction: Position direction

        Returns:
            Dict containing complete position record
        """
        # Generate Position UUID
        position_uuid = generate_position_uuid(
            ticker=ticker,
            strategy_type=strategy_type,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            entry_date=entry_date,
        )

        # Basic position data
        position_data = {
            "Position_UUID": position_uuid,
            "Ticker": ticker,
            "Strategy_Type": strategy_type,
            "Fast_Period": fast_period,
            "Slow_Period": slow_period,
            "Signal_Period": signal_period,
            "Entry_Timestamp": entry_date,
            "Exit_Timestamp": exit_date,
            "Avg_Entry_Price": entry_price,
            "Avg_Exit_Price": exit_price,
            "Position_Size": position_size,
            "Direction": direction,
            "Trade_Type": "Signal",
            "Status": "Closed" if exit_date and exit_price else "Open",
        }

        # Calculate basic metrics if we have exit data
        if exit_price is not None and entry_price is not None:
            pnl, return_pct = self.calculator.calculate_pnl_and_return(
                entry_price, exit_price, position_size, direction,
            )
            position_data["PnL"] = pnl
            position_data["Return"] = return_pct
        else:
            position_data["PnL"] = 0.0
            position_data["Return"] = 0.0

        # Calculate days since entry
        if entry_date:
            days_since = self.calculator.calculate_days_since_entry(entry_date)
            position_data["Days_Since_Entry"] = days_since

        # Calculate MFE/MAE if we have price data
        try:
            mfe, mae, mfe_mae_ratio = self.calculate_mfe_mae(
                ticker, entry_date, exit_date or "", entry_price, direction,
            )

            if mfe is not None and mae is not None:
                position_data["Max_Favourable_Excursion"] = mfe
                position_data["Max_Adverse_Excursion"] = mae
                position_data["MFE_MAE_Ratio"] = mfe_mae_ratio

                # Calculate exit efficiency if closed position
                if exit_price is not None:
                    exit_efficiency = self.calculator.calculate_exit_efficiency(
                        position_data["Return"], mfe,
                    )
                    position_data["Exit_Efficiency_Fixed"] = exit_efficiency

                # Assess trade quality
                trade_quality = self.calculator.assess_trade_quality(
                    mfe, mae, position_data.get("Return"),
                )
                position_data["Trade_Quality"] = trade_quality

        except (PriceDataError, CalculationError) as e:
            self.logger.warning(f"Could not calculate MFE/MAE for {position_uuid}: {e}")
            position_data["Max_Favourable_Excursion"] = None
            position_data["Max_Adverse_Excursion"] = None
            position_data["MFE_MAE_Ratio"] = None
            position_data["Exit_Efficiency_Fixed"] = None
            position_data["Trade_Quality"] = "Unknown"

        return position_data

    def add_position_to_portfolio(
        self,
        ticker: str,
        strategy_type: str,
        fast_period: int,
        slow_period: int,
        signal_period: int = 0,
        entry_date: str | None = None,
        entry_price: float | None = None,
        exit_date: str | None = None,
        exit_price: float | None = None,
        position_size: float = 1.0,
        direction: str = "Long",
        portfolio_name: str = "live_signals",
        verify_signal: bool = True,
    ) -> str:
        """
        Add a position to an existing portfolio CSV file.

        Args:
            ticker: Stock/asset ticker symbol
            strategy_type: Strategy type
            fast_period: Short period window
            slow_period: Long period window
            signal_period: Signal period (default 0)
            entry_date: Entry date
            entry_price: Entry price
            exit_date: Exit date (None for open)
            exit_price: Exit price (None for open)
            position_size: Position size
            direction: Position direction
            portfolio_name: Portfolio name
            verify_signal: Whether to verify entry signal

        Returns:
            Position UUID of added position
        """
        # Validate inputs
        self.validate_ticker(ticker)
        self.validate_strategy_type(strategy_type)

        if entry_date:
            self.validate_date_string(entry_date)

        if exit_date:
            self.validate_date_string(exit_date)

        # Verify signal if requested
        if verify_signal and entry_date:
            try:
                verification = self.verify_entry_signal(
                    ticker,
                    strategy_type,
                    fast_period,
                    slow_period,
                    entry_date,
                    direction,
                )
                if not verification["verified"]:
                    msg = f"No {direction} crossover signal found for {ticker} on {entry_date}"
                    raise SignalValidationError(
                        msg,
                    )
                self.logger.info(f"✓ Signal verified: {verification['signal_type']}")
            except (DataNotFoundError, PriceDataError) as e:
                self.logger.warning(f"Could not verify signal: {e}")

        # Create position record
        position_data = self.create_position_record(
            ticker=ticker,
            strategy_type=strategy_type,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            entry_date=entry_date,
            entry_price=entry_price,
            exit_date=exit_date,
            exit_price=exit_price,
            position_size=position_size,
            direction=direction,
        )

        # Load or create portfolio file
        portfolio_file = self.config.get_portfolio_file(portfolio_name)

        if portfolio_file.exists():
            df = pd.read_csv(portfolio_file)
        else:
            # Create new portfolio with proper columns
            df = pd.DataFrame(columns=list(position_data.keys()))

        # Check for duplicate position
        position_uuid = position_data["Position_UUID"]
        if (
            "Position_UUID" in df.columns
            and position_uuid in df["Position_UUID"].values
        ):
            msg = f"Position {position_uuid} already exists in portfolio {portfolio_name}"
            raise PortfolioError(
                msg,
            )

        # Add position to dataframe
        new_row = pd.DataFrame([position_data])
        df = pd.concat([df, new_row], ignore_index=True)

        # Save updated portfolio
        df.to_csv(portfolio_file, index=False)

        self.logger.info(
            f"✅ Added position {position_uuid} to portfolio {portfolio_name}",
        )
        return position_uuid

    def close_position(
        self,
        position_uuid: str,
        portfolio_name: str,
        exit_price: float,
        exit_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Close an open position in a portfolio.

        Args:
            position_uuid: Position UUID to close
            portfolio_name: Portfolio containing the position
            exit_price: Exit price
            exit_date: Exit date (defaults to current timestamp)

        Returns:
            Dict with closing results and updated position data
        """
        if exit_date is None:
            exit_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Load portfolio
        portfolio_file = self.config.get_portfolio_file(portfolio_name)
        if not portfolio_file.exists():
            msg = f"Portfolio file not found: {portfolio_file}"
            raise PortfolioError(msg)

        df = pd.read_csv(portfolio_file)

        # Find position
        position_mask = df["Position_UUID"] == position_uuid
        if not position_mask.any():
            msg = f"Position {position_uuid} not found in portfolio {portfolio_name}"
            raise DataNotFoundError(
                msg,
            )

        position_idx = df.index[position_mask][0]
        position = df.loc[position_idx]

        # Update position with exit data
        df.loc[position_idx, "Exit_Timestamp"] = exit_date
        df.loc[position_idx, "Avg_Exit_Price"] = exit_price
        df.loc[position_idx, "Status"] = "Closed"

        # Recalculate metrics using PositionCalculator
        entry_price = position["Avg_Entry_Price"]
        position_size = position["Position_Size"]
        direction = position["Direction"]

        pnl, return_pct = self.calculator.calculate_pnl_and_return(
            entry_price, exit_price, position_size, direction,
        )

        df.loc[position_idx, "PnL"] = pnl
        df.loc[position_idx, "Return"] = return_pct

        # Recalculate MFE/MAE with final exit date
        try:
            mfe, mae, mfe_mae_ratio = self.calculate_mfe_mae(
                position["Ticker"],
                position["Entry_Timestamp"],
                exit_date,
                entry_price,
                direction,
            )

            if mfe is not None and mae is not None:
                df.loc[position_idx, "Max_Favourable_Excursion"] = mfe
                df.loc[position_idx, "Max_Adverse_Excursion"] = mae
                df.loc[position_idx, "MFE_MAE_Ratio"] = mfe_mae_ratio

                # Calculate exit efficiency
                exit_efficiency = self.calculator.calculate_exit_efficiency(
                    return_pct, mfe,
                )
                df.loc[position_idx, "Exit_Efficiency_Fixed"] = exit_efficiency

                # Assess trade quality
                trade_quality = self.calculator.assess_trade_quality(
                    mfe, mae, return_pct,
                )
                df.loc[position_idx, "Trade_Quality"] = trade_quality

        except (PriceDataError, CalculationError) as e:
            self.logger.warning(
                f"Could not recalculate MFE/MAE for closed position: {e}",
            )

        # Save updated portfolio
        df.to_csv(portfolio_file, index=False)

        # Return closing results
        updated_position = df.loc[position_idx].to_dict()

        self.logger.info(f"✅ Closed position {position_uuid} at ${exit_price:.2f}")

        return {
            "success": True,
            "position_uuid": position_uuid,
            "portfolio": portfolio_name,
            "exit_price": exit_price,
            "exit_date": exit_date,
            "pnl": pnl,
            "return": return_pct,
            "position_data": updated_position,
        }

    def list_positions(
        self, portfolio_name: str, status_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List all positions in a portfolio.

        Args:
            portfolio_name: Portfolio name
            status_filter: Filter by status ('Open', 'Closed', or None for all)

        Returns:
            List of position dictionaries
        """
        portfolio_file = self.config.get_portfolio_file(portfolio_name)
        if not portfolio_file.exists():
            msg = f"Portfolio file not found: {portfolio_file}"
            raise PortfolioError(msg)

        df = pd.read_csv(portfolio_file)

        if status_filter:
            df = df[df["Status"] == status_filter]

        return df.to_dict("records")

    def get_position(self, position_uuid: str, portfolio_name: str) -> dict[str, Any]:
        """
        Get a specific position by UUID.

        Args:
            position_uuid: Position UUID
            portfolio_name: Portfolio name

        Returns:
            Position data dictionary
        """
        positions = self.list_positions(portfolio_name)

        for position in positions:
            if position.get("Position_UUID") == position_uuid:
                return position

        msg = f"Position {position_uuid} not found in portfolio {portfolio_name}"
        raise DataNotFoundError(
            msg,
        )


# Global service instance for backward compatibility
_position_service = None


def get_position_service(config: TradingSystemConfig = None) -> PositionService:
    """Get or create global position service instance."""
    global _position_service
    if _position_service is None:
        _position_service = PositionService(config)
    return _position_service


def set_position_service(service: PositionService):
    """Set global position service instance."""
    global _position_service
    _position_service = service
