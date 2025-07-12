"""
Generalized Trade History Exporter

Universal exporter for creating position-level trade history CSV files from any ticker and strategy.
Fully configurable and reusable across different trading systems and data sources.

Features:
- Configuration-driven file paths supporting any directory structure
- Generic ticker/strategy support with comprehensive validation
- Modular MFE/MAE calculation for any price data format and timeframe
- Reusable position extraction and migration functions
- Support for multiple strategy types (SMA, EMA, MACD, etc.)
- Flexible data source handling (JSON, CSV, database)

Usage:
    from app.tools.generalized_trade_history_exporter import *

    # Configure for your trading system
    config = TradingSystemConfig(base_dir="/path/to/trading/system")
    set_config(config)

    # Add position to any portfolio
    add_position_to_portfolio(
        ticker="AAPL",
        strategy_type="SMA",
        short_window=20,
        long_window=50,
        entry_date="20250101",
        entry_price=150.00,
        portfolio_name="my_portfolio"
    )
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import polars as pl

from app.cli.utils import resolve_portfolio_path

from .utils.mfe_mae_calculator import get_mfe_mae_calculator

try:
    from .uuid_utils import generate_position_uuid as _generate_position_uuid
except ImportError:
    from app.tools.uuid_utils import generate_position_uuid as _generate_position_uuid

logger = logging.getLogger(__name__)


class TradingSystemConfig:
    """Configuration for trading system file paths and settings."""

    def __init__(self, base_dir: str = None):
        """Initialize configuration with base directory."""
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

    @property
    def price_data_dir(self) -> Path:
        """Directory containing price data files."""
        return self.base_dir / "csv" / "price_data"

    @property
    def positions_dir(self) -> Path:
        """Directory for position-level CSV files."""
        return self.base_dir / "csv" / "positions"

    @property
    def strategies_dir(self) -> Path:
        """Directory for strategy-level CSV files."""
        return self.base_dir / "csv" / "strategies"

    @property
    def trade_history_dir(self) -> Path:
        """Directory for JSON trade history files."""
        return self.base_dir / "json" / "trade_history"

    @property
    def trade_history_csv_dir(self) -> Path:
        """Directory for exported trade history CSV files."""
        return self.base_dir / "csv" / "trade_history"

    def get_price_data_file(self, ticker: str, timeframe: str = "D") -> Path:
        """Get price data file path for any ticker and timeframe."""
        return self.price_data_dir / f"{ticker}_{timeframe}.csv"

    def get_portfolio_file(self, portfolio_name: str) -> Path:
        """Get portfolio positions file path."""
        return self.positions_dir / resolve_portfolio_path(portfolio_name)

    def ensure_directories(self):
        """Create all required directories if they don't exist."""
        for directory in [
            self.price_data_dir,
            self.positions_dir,
            self.strategies_dir,
            self.trade_history_dir,
            self.trade_history_csv_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


# Global configuration instance
_config = None


def get_config() -> TradingSystemConfig:
    """Get or create global configuration instance."""
    global _config
    if _config is None:
        _config = TradingSystemConfig()
    return _config


def set_config(config: TradingSystemConfig):
    """Set global configuration instance."""
    global _config
    _config = config


def validate_ticker(ticker: str) -> bool:
    """Validate ticker symbol format."""
    if not ticker or not isinstance(ticker, str):
        return False
    # Basic validation - alphanumeric with optional separators
    return ticker.replace("-", "").replace(".", "").replace("_", "").isalnum()


def validate_strategy_type(strategy_type: str) -> bool:
    """Validate strategy type."""
    valid_strategies = ["SMA", "EMA", "MACD", "RSI", "BOLLINGER", "STOCHASTIC"]
    return strategy_type.upper() in valid_strategies


def validate_date_string(date_str: str) -> bool:
    """Validate date string format."""
    try:
        if " " in date_str:
            # Try with timestamp
            date_part = date_str.split(" ")[0]
            if len(date_part) == 8 and date_part.isdigit():
                datetime.strptime(date_str, "%Y%m%d %H:%M:%S")
            else:
                datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        else:
            # Try YYYYMMDD format first (new convention), then YYYY-MM-DD (old format)
            if len(date_str) == 8 and date_str.isdigit():
                datetime.strptime(date_str, "%Y%m%d")
            else:
                datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def generate_position_uuid(
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    signal_window: int,
    entry_date: str,
) -> str:
    """Generate unique position identifier with validation."""
    # Validate inputs
    if not validate_ticker(ticker):
        raise ValueError(f"Invalid ticker: {ticker}")
    if not validate_strategy_type(strategy_type):
        raise ValueError(f"Invalid strategy type: {strategy_type}")
    if not validate_date_string(entry_date):
        raise ValueError(f"Invalid entry date: {entry_date}")

    # Use centralized UUID generation
    return _generate_position_uuid(
        ticker=ticker,
        strategy_type=strategy_type,
        short_window=short_window,
        long_window=long_window,
        signal_window=signal_window,
        entry_date=entry_date,
    )


def calculate_mfe_mae(
    ticker: str,
    entry_date: str,
    exit_date: str,
    entry_price: float,
    direction: str = "Long",
    timeframe: str = "D",
    config: TradingSystemConfig = None,
) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
    """Calculate Max Favourable Excursion and Max Adverse Excursion using price data.

    Args:
        ticker: Stock/asset ticker symbol
        entry_date: Position entry date (YYYY-MM-DD or datetime string)
        exit_date: Position exit date (YYYY-MM-DD or datetime string, empty for open positions)
        entry_price: Entry price for position
        direction: Position direction ('Long' or 'Short')
        timeframe: Price data timeframe ('D' for daily, 'H' for hourly, etc.)
        config: Trading system configuration (uses global if None)

    Returns:
        tuple: (mfe, mae, mfe_mae_ratio, exit_efficiency)
    """

    if config is None:
        config = get_config()

    # Validate inputs
    if not validate_ticker(ticker):
        logger.error(f"Invalid ticker: {ticker}")
        return None, None, None, None

    if not validate_date_string(entry_date):
        logger.error(f"Invalid entry date: {entry_date}")
        return None, None, None, None

    if entry_price <= 0:
        logger.error(f"Invalid entry price: {entry_price}")
        return None, None, None, None

    try:
        # Load price data using configuration
        price_file = config.get_price_data_file(ticker, timeframe)
        if not price_file.exists():
            logger.warning(f"Price data not found for {ticker} at {price_file}")
            return None, None, None, None

        # Read price data
        df = pd.read_csv(price_file)
        df["Date"] = pd.to_datetime(df["Date"])

        # Convert dates with validation
        try:
            entry_dt = pd.to_datetime(entry_date.split(" ")[0])
        except (ValueError, AttributeError):
            logger.error(f"Cannot parse entry date: {entry_date}")
            return None, None, None, None

        exit_dt = pd.Timestamp.now()
        if exit_date and exit_date.strip():
            try:
                exit_dt = pd.to_datetime(exit_date.split(" ")[0])
            except (ValueError, AttributeError):
                logger.warning(
                    f"Cannot parse exit date: {exit_date}, using current date"
                )

        # Filter to position period
        position_df = df[(df["Date"] >= entry_dt) & (df["Date"] <= exit_dt)].copy()

        if position_df.empty:
            logger.warning(
                f"No price data found for {ticker} between {entry_date} and {exit_date}"
            )
            return None, None, None, None

        # Use centralized MFE/MAE calculator
        calculator = get_mfe_mae_calculator(logger)
        mfe, mae = calculator.calculate_from_ohlc(
            entry_price=entry_price,
            ohlc_data=position_df,
            direction=direction,
            high_col="High",
            low_col="Low",
        )

        # Calculate ratios with validation
        mfe_mae_ratio = mfe / mae if mae != 0 else None

        return mfe, mae, mfe_mae_ratio, None  # Exit efficiency calculated separately

    except Exception as e:
        logger.error(f"Error calculating MFE/MAE for {ticker}: {e}")
        return None, None, None, None


def assess_trade_quality(
    mfe: float, mae: float, exit_efficiency: float, return_pct: float = None
) -> str:
    """Assess trade quality based on MFE/MAE and exit efficiency metrics."""

    if mfe is None or mae is None:
        return ""

    risk_reward_ratio = mfe / mae if mae > 0 else float("inf")

    # Handle edge cases with poor risk/reward setups
    if mfe < 0.02 and mae > 0.05:  # MFE < 2%, MAE > 5%
        return "Poor Setup - High Risk, Low Reward"
    elif return_pct is not None and return_pct < 0 and abs(return_pct) > mfe:
        return "Failed to Capture Upside"
    elif risk_reward_ratio >= 3.0 and (
        exit_efficiency is None or exit_efficiency >= 0.8
    ):
        return "Excellent"
    elif risk_reward_ratio >= 2.0 and (
        exit_efficiency is None or exit_efficiency >= 0.6
    ):
        return "Excellent"
    elif risk_reward_ratio >= 1.5 and (
        exit_efficiency is None or exit_efficiency >= 0.4
    ):
        return "Good"
    else:
        return "Poor"


def verify_entry_signal(
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    entry_date: str,
    timeframe: str = "D",
    config: TradingSystemConfig = None,
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Verify if an entry signal actually occurred on the specified date for the given strategy.

    Args:
        ticker: Stock/asset ticker symbol
        strategy_type: Strategy type ('SMA', 'EMA', 'MACD', etc.)
        short_window: Short period for moving average
        long_window: Long period for moving average
        entry_date: Date to verify signal occurred (YYYY-MM-DD)
        timeframe: Price data timeframe ('D' for daily, 'H' for hourly, etc.)
        config: Trading system configuration (uses global if None)

    Returns:
        tuple: (signal_verified, verification_message, signal_details)
    """

    if config is None:
        config = get_config()

    # Validate inputs
    if not validate_ticker(ticker):
        return False, f"Invalid ticker: {ticker}", None

    if not validate_strategy_type(strategy_type):
        return False, f"Invalid strategy type: {strategy_type}", None

    if not validate_date_string(entry_date):
        return False, f"Invalid entry date: {entry_date}", None

    try:
        # Load price data using configuration
        price_file = config.get_price_data_file(ticker, timeframe)
        if not price_file.exists():
            return False, f"Price data not found for {ticker} at {price_file}", None

        # Read price data
        df = pd.read_csv(price_file)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")

        # Convert entry date
        try:
            entry_dt = pd.to_datetime(entry_date.split(" ")[0])
        except (ValueError, AttributeError):
            return False, f"Cannot parse entry date: {entry_date}", None

        # Calculate moving averages based on strategy type
        if strategy_type.upper() == "SMA":
            df[f"MA_{short_window}"] = df["Close"].rolling(window=short_window).mean()
            df[f"MA_{long_window}"] = df["Close"].rolling(window=long_window).mean()
        elif strategy_type.upper() == "EMA":
            df[f"MA_{short_window}"] = df["Close"].ewm(span=short_window).mean()
            df[f"MA_{long_window}"] = df["Close"].ewm(span=long_window).mean()
        else:
            return (
                False,
                f"Strategy type {strategy_type} not supported for verification",
                None,
            )

        # Find the entry date row
        entry_row = df[df["Date"] == entry_dt]
        if entry_row.empty:
            return False, f"No price data found for {ticker} on {entry_date}", None

        entry_idx = entry_row.index[0]

        # Need at least one previous day for crossover detection
        if entry_idx == 0:
            return (
                False,
                f"Insufficient data for crossover detection on {entry_date}",
                None,
            )

        # Get current and previous values
        current_short = entry_row[f"MA_{short_window}"].iloc[0]
        current_long = entry_row[f"MA_{long_window}"].iloc[0]
        prev_short = df.loc[entry_idx - 1, f"MA_{short_window}"]
        prev_long = df.loc[entry_idx - 1, f"MA_{long_window}"]

        # Check if values are valid (not NaN)
        if (
            pd.isna(current_short)
            or pd.isna(current_long)
            or pd.isna(prev_short)
            or pd.isna(prev_long)
        ):
            return (
                False,
                f"Insufficient moving average data for {entry_date} (need at least {max(short_window, long_window)} days)",
                None,
            )

        # Check for bullish crossover (short MA crossing above long MA)
        bullish_crossover = (current_short > current_long) and (prev_short <= prev_long)

        # Check for bearish crossover (short MA crossing below long MA)
        bearish_crossover = (current_short < current_long) and (prev_short >= prev_long)

        signal_details = {
            "date": entry_date,
            "current_short_ma": float(current_short),
            "current_long_ma": float(current_long),
            "previous_short_ma": float(prev_short),
            "previous_long_ma": float(prev_long),
            "close_price": float(entry_row["Close"].iloc[0]),
            "bullish_crossover": bullish_crossover,
            "bearish_crossover": bearish_crossover,
            "ma_spread": float(current_short - current_long),
            "prev_ma_spread": float(prev_short - prev_long),
        }

        if bullish_crossover:
            verification_msg = f"✓ VERIFIED: Bullish crossover on {entry_date} - {strategy_type}{short_window} (${current_short:.2f}) crossed above {strategy_type}{long_window} (${current_long:.2f})"
            return True, verification_msg, signal_details
        elif bearish_crossover:
            verification_msg = f"✓ VERIFIED: Bearish crossover on {entry_date} - {strategy_type}{short_window} (${current_short:.2f}) crossed below {strategy_type}{long_window} (${current_long:.2f})"
            return True, verification_msg, signal_details
        else:
            # No crossover detected
            if current_short > current_long:
                verification_msg = f"✗ NO SIGNAL: {strategy_type}{short_window} (${current_short:.2f}) was already above {strategy_type}{long_window} (${current_long:.2f}) on {entry_date}"
            else:
                verification_msg = f"✗ NO SIGNAL: {strategy_type}{short_window} (${current_short:.2f}) was below {strategy_type}{long_window} (${current_long:.2f}) on {entry_date} with no crossover"

            return False, verification_msg, signal_details

    except Exception as e:
        return False, f"Error verifying signal for {ticker}: {e}", None


def estimate_strategy_entry_date(
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    timeframe: str = "D",
    config: TradingSystemConfig = None,
) -> Tuple[Optional[str], Optional[float]]:
    """Estimate entry date and price for a strategy by finding recent crossover signals.

    Args:
        ticker: Stock/asset ticker symbol
        strategy_type: Strategy type ('SMA', 'EMA', 'MACD', etc.)
        short_window: Short period for moving average
        long_window: Long period for moving average
        timeframe: Price data timeframe ('D' for daily, 'H' for hourly, etc.)
        config: Trading system configuration (uses global if None)

    Returns:
        tuple: (entry_date, entry_price) or (None, None) if unable to estimate
    """

    if config is None:
        config = get_config()

    # Validate inputs
    if not validate_ticker(ticker):
        logger.error(f"Invalid ticker: {ticker}")
        return None, None

    if not validate_strategy_type(strategy_type):
        logger.error(f"Invalid strategy type: {strategy_type}")
        return None, None

    try:
        # Load price data using configuration
        price_file = config.get_price_data_file(ticker, timeframe)
        if not price_file.exists():
            logger.warning(f"Price data not found for {ticker} at {price_file}")
            return None, None

        # Read price data
        df = pd.read_csv(price_file)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")

        # Calculate moving averages based on strategy type
        if strategy_type.upper() == "SMA":
            df[f"MA_{short_window}"] = df["Close"].rolling(window=short_window).mean()
            df[f"MA_{long_window}"] = df["Close"].rolling(window=long_window).mean()
        elif strategy_type.upper() == "EMA":
            df[f"MA_{short_window}"] = df["Close"].ewm(span=short_window).mean()
            df[f"MA_{long_window}"] = df["Close"].ewm(span=long_window).mean()
        else:
            logger.warning(
                f"Strategy type {strategy_type} not supported for estimation"
            )
            return None, None

        # Find crossover signals (short MA crossing above long MA for long entry)
        df["Signal"] = (df[f"MA_{short_window}"] > df[f"MA_{long_window}"]) & (
            df[f"MA_{short_window}"].shift(1) <= df[f"MA_{long_window}"].shift(1)
        )

        # Get most recent signal within last 200 days
        recent_signals = df[df["Signal"] == True].tail(5)  # Last 5 signals

        if recent_signals.empty:
            # No signals found, estimate based on current position being profitable
            current_date = pd.Timestamp.now()
            estimate_days_ago = 60  # Estimate 60 days ago
            entry_date = current_date - pd.Timedelta(days=estimate_days_ago)

            # Find closest date in price data
            closest_idx = df["Date"].searchsorted(entry_date)
            if closest_idx < len(df):
                entry_row = df.iloc[closest_idx]
                return entry_row["Date"].strftime("%Y%m%d"), entry_row["Close"]
            else:
                return None, None

        # Use the most recent signal
        entry_row = recent_signals.iloc[-1]
        entry_date = entry_row["Date"].strftime("%Y%m%d")
        entry_price = entry_row["Close"]

        return entry_date, entry_price

    except Exception as e:
        logger.error(f"Error estimating entry for {ticker} {strategy_type}: {e}")
        return None, None


def create_position_record(
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    signal_window: int = 0,
    entry_date: str = None,
    entry_price: float = None,
    exit_date: str = None,
    exit_price: float = None,
    position_size: float = 1.0,
    direction: str = "Long",
    config: TradingSystemConfig = None,
) -> Dict[str, Any]:
    """Create a standardized position record with all required fields.

    Args:
        ticker: Stock/asset ticker symbol
        strategy_type: Strategy type ('SMA', 'EMA', etc.)
        short_window: Short period for strategy
        long_window: Long period for strategy
        signal_window: Signal window (default 0)
        entry_date: Entry date (estimated if None)
        entry_price: Entry price (estimated if None)
        exit_date: Exit date (None for open positions)
        exit_price: Exit price (None for open positions)
        position_size: Position size (default 1.0)
        direction: Position direction ('Long' or 'Short')
        config: Trading system configuration

    Returns:
        Dict: Complete position record
    """

    if config is None:
        config = get_config()

    # Estimate entry date/price if not provided
    if entry_date is None or entry_price is None:
        est_date, est_price = estimate_strategy_entry_date(
            ticker, strategy_type, short_window, long_window, config=config
        )
        entry_date = entry_date or est_date
        entry_price = entry_price or est_price

    if entry_date is None or entry_price is None:
        raise ValueError(
            f"Cannot determine entry date/price for {ticker} {strategy_type}"
        )

    # Generate position UUID
    position_uuid = generate_position_uuid(
        ticker, strategy_type, short_window, long_window, signal_window, entry_date
    )

    # Calculate MFE/MAE
    mfe, mae, mfe_mae_ratio, _ = calculate_mfe_mae(
        ticker,
        f"{entry_date} 00:00:00",
        exit_date or "",
        entry_price,
        direction,
        config=config,
    )

    # Calculate days since entry
    days_since_entry = None
    if entry_date:
        try:
            # Try YYYYMMDD format first (new convention), then YYYY-MM-DD (old format)
            if len(entry_date) == 8 and entry_date.isdigit():
                entry_dt = datetime.strptime(entry_date, "%Y%m%d")
            else:
                entry_dt = datetime.strptime(entry_date, "%Y-%m-%d")
            days_since_entry = (datetime.now() - entry_dt).days
        except ValueError:
            logger.warning(
                f"Cannot parse entry date for days calculation: {entry_date}"
            )

    # Calculate P&L and return for closed positions
    pnl = None
    return_pct = None
    exit_efficiency = None

    if exit_date and exit_price:
        if direction.upper() == "LONG":
            pnl = (exit_price - entry_price) * position_size
            return_pct = (exit_price - entry_price) / entry_price
        else:  # Short position
            pnl = (entry_price - exit_price) * position_size
            return_pct = (entry_price - exit_price) / entry_price

        # Calculate exit efficiency
        if mfe and mfe > 0:
            exit_efficiency = return_pct / mfe

    # Assess trade quality
    trade_quality = assess_trade_quality(mfe, mae, exit_efficiency, return_pct)

    # Create position record with standardized precision
    position = {
        "Position_UUID": position_uuid,
        "Ticker": ticker.upper(),
        "Strategy_Type": strategy_type.upper(),
        "Short_Window": short_window,
        "Long_Window": long_window,
        "Signal_Window": signal_window,
        "Entry_Timestamp": f"{entry_date} 00:00:00",
        "Exit_Timestamp": f"{exit_date} 00:00:00" if exit_date else None,
        "Avg_Entry_Price": entry_price,
        "Avg_Exit_Price": exit_price,
        "Position_Size": position_size,
        "Direction": direction.title(),
        "PnL": round(pnl, 6) if pnl is not None else None,
        "Return": round(return_pct, 6) if return_pct is not None else None,
        "Duration_Days": None,  # Could be calculated
        "Trade_Type": direction.title(),
        "Status": "Closed" if exit_date else "Open",
        "Max_Favourable_Excursion": round(mfe, 6) if mfe is not None else None,
        "Max_Adverse_Excursion": round(mae, 6) if mae is not None else None,
        "MFE_MAE_Ratio": round(mfe_mae_ratio, 6) if mfe_mae_ratio is not None else None,
        "Exit_Efficiency": round(exit_efficiency, 6)
        if exit_efficiency is not None
        else None,
        "Days_Since_Entry": days_since_entry if not exit_date else None,
        "Current_Unrealized_PnL": None,
        "Current_Excursion_Status": "Open" if not exit_date else None,
        "Exit_Efficiency_Fixed": round(exit_efficiency, 6)
        if exit_efficiency is not None
        else None,
        "Trade_Quality": trade_quality,
    }

    return position


def add_position_to_portfolio(
    ticker: str,
    strategy_type: str,
    short_window: int,
    long_window: int,
    signal_window: int = 0,
    entry_date: str = None,
    entry_price: float = None,
    exit_date: str = None,
    exit_price: float = None,
    position_size: float = 1.0,
    direction: str = "Long",
    portfolio_name: str = "live_signals",
    verify_signal: bool = True,
    config: TradingSystemConfig = None,
) -> str:
    """Add a position to an existing portfolio CSV file.

    Args:
        ticker: Stock/asset ticker symbol
        strategy_type: Strategy type ('SMA', 'EMA', etc.)
        short_window: Short period for strategy
        long_window: Long period for strategy
        signal_window: Signal window (default 0)
        entry_date: Entry date (estimated if None)
        entry_price: Entry price (estimated if None)
        exit_date: Exit date (None for open positions)
        exit_price: Exit price (None for open positions)
        position_size: Position size (default 1.0)
        direction: Position direction ('Long' or 'Short')
        portfolio_name: Name of portfolio to add to
        verify_signal: Whether to verify entry signal occurred on entry date (default True)
        config: Trading system configuration

    Returns:
        str: Position UUID of added position

    Raises:
        ValueError: If signal verification fails and verify_signal is True
    """

    if config is None:
        config = get_config()

    # Ensure directories exist
    config.ensure_directories()

    # Verify signal if requested and entry_date is provided
    if verify_signal and entry_date and strategy_type.upper() in ["SMA", "EMA"]:
        signal_verified, verification_msg, signal_details = verify_entry_signal(
            ticker=ticker,
            strategy_type=strategy_type,
            short_window=short_window,
            long_window=long_window,
            entry_date=entry_date,
            config=config,
        )

        if not signal_verified:
            raise ValueError(f"Signal verification failed: {verification_msg}")
        else:
            logger.info(f"Signal verified: {verification_msg}")

    # Create position record
    position = create_position_record(
        ticker=ticker,
        strategy_type=strategy_type,
        short_window=short_window,
        long_window=long_window,
        signal_window=signal_window,
        entry_date=entry_date,
        entry_price=entry_price,
        exit_date=exit_date,
        exit_price=exit_price,
        position_size=position_size,
        direction=direction,
        config=config,
    )

    # Get portfolio file path
    portfolio_file = config.get_portfolio_file(portfolio_name)

    # Load existing portfolio or create new one
    if portfolio_file.exists():
        df = pd.read_csv(portfolio_file)

        # Check if position already exists
        existing_uuid = position["Position_UUID"]
        if existing_uuid in df["Position_UUID"].values:
            logger.warning(
                f"Position {existing_uuid} already exists in {portfolio_name}"
            )
            return existing_uuid

        # Add new position
        new_df = pd.concat([df, pd.DataFrame([position])], ignore_index=True)
    else:
        # Create new portfolio file
        new_df = pd.DataFrame([position])

    # Save updated portfolio
    new_df.to_csv(portfolio_file, index=False)

    logger.info(f"Added position {position['Position_UUID']} to {portfolio_name}")
    return position["Position_UUID"]


def bulk_add_positions_from_strategy_csv(
    strategy_csv_path: str, portfolio_name: str, config: TradingSystemConfig = None
) -> List[str]:
    """Bulk add positions from a strategy CSV file to a portfolio.

    Args:
        strategy_csv_path: Path to strategy CSV file
        portfolio_name: Name of target portfolio
        config: Trading system configuration

    Returns:
        List[str]: List of position UUIDs added
    """

    if config is None:
        config = get_config()

    if not Path(strategy_csv_path).exists():
        raise FileNotFoundError(f"Strategy CSV not found: {strategy_csv_path}")

    # Read strategy data
    df = pd.read_csv(strategy_csv_path)
    added_positions = []

    for _, row in df.iterrows():
        if pd.isna(row["Ticker"]) or row["Ticker"] == "":
            continue

        # Skip if no open trades
        if row.get("Total Open Trades", 0) == 0:
            continue

        try:
            position_uuid = add_position_to_portfolio(
                ticker=row["Ticker"],
                strategy_type=row["Strategy Type"],
                short_window=int(row["Short Window"]),
                long_window=int(row["Long Window"]),
                signal_window=int(row.get("Signal Window", 0)),
                portfolio_name=portfolio_name,
                config=config,
            )
            added_positions.append(position_uuid)

        except Exception as e:
            logger.error(f"Failed to add position for {row['Ticker']}: {e}")
            continue

    logger.info(f"Added {len(added_positions)} positions to {portfolio_name}")
    return added_positions


# Convenience functions for common operations
def add_qcom_position(
    entry_date: str = "20250624", portfolio_name: str = "live_signals"
):
    """Add QCOM SMA 49/66 position to portfolio."""
    return add_position_to_portfolio(
        ticker="QCOM",
        strategy_type="SMA",
        short_window=49,
        long_window=66,
        entry_date=entry_date,
        portfolio_name=portfolio_name,
    )


def create_new_portfolio_from_strategy(strategy_name: str, portfolio_name: str = None):
    """Create a new portfolio from an existing strategy CSV."""
    if portfolio_name is None:
        portfolio_name = strategy_name

    config = get_config()
    strategy_file = config.strategies_dir / f"{strategy_name}.csv"

    return bulk_add_positions_from_strategy_csv(
        str(strategy_file), portfolio_name, config
    )


def main():
    """Main CLI entry point for generalized trade history exporter."""
    import argparse
    import sys
    import warnings

    # Show deprecation warning for direct script usage
    warnings.warn(
        "\n"
        "⚠️  DEPRECATION WARNING: Direct execution of this script is deprecated.\n"
        "   Use the unified CLI interface instead:\n"
        "   \n"
        "   Replace: python -m app.tools.generalized_trade_history_exporter --update-open-positions --portfolio live_signals\n"
        "   With:    python -m app.cli trade-history update --portfolio live_signals\n"
        "   \n"
        "   For more information: python -m app.cli trade-history --help\n"
        "   \n"
        "   This script will be removed in a future version.\n",
        DeprecationWarning,
        stacklevel=2,
    )

    parser = argparse.ArgumentParser(
        description="Generalized Trade History Exporter - Add positions to any portfolio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add QCOM position
  python %(prog)s --add-qcom --entry-date 20250624 --portfolio live_signals

  # Add custom position with signal verification
  python %(prog)s --add-position --ticker AAPL --strategy SMA --short-window 20 --long-window 50 --entry-date 20250101 --portfolio my_portfolio

  # Add position without signal verification
  python %(prog)s --add-position --ticker AAPL --strategy SMA --short-window 20 --long-window 50 --entry-date 20250101 --portfolio my_portfolio --no-verify-signal

  # Quick add position
  python %(prog)s --quick-add --ticker MSFT --strategy EMA --short 12 --long 26 --portfolio tech_stocks

  # Verify entry signal occurred on specific date
  python %(prog)s --verify-signal --ticker QCOM --strategy SMA --short-window 49 --long-window 66 --entry-date 20250624

  # Bulk add from CSV
  python %(prog)s --bulk-add --strategy-csv csv/strategies/signals.csv --portfolio new_portfolio

  # Calculate MFE/MAE
  python %(prog)s --calculate-mfe-mae --ticker AAPL --entry-date 20250101 --exit-date 20250201 --entry-price 150.00
        """,
    )

    # Configuration options
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "--base-dir", type=str, help="Base directory for trading system"
    )
    config_group.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    config_group.add_argument(
        "--dry-run", action="store_true", help="Dry run - no changes made"
    )
    config_group.add_argument(
        "--validate-config", action="store_true", help="Validate configuration and exit"
    )

    # Main operations
    operations = parser.add_mutually_exclusive_group(required=True)
    operations.add_argument(
        "--add-qcom", action="store_true", help="Add QCOM SMA 49/66 position"
    )
    operations.add_argument(
        "--add-position", action="store_true", help="Add custom position"
    )
    operations.add_argument(
        "--quick-add",
        action="store_true",
        help="Quick add position with minimal params",
    )
    operations.add_argument(
        "--bulk-add", action="store_true", help="Bulk add from strategy CSV"
    )
    operations.add_argument(
        "--create-position", action="store_true", help="Create detailed position record"
    )
    operations.add_argument(
        "--calculate-mfe-mae", action="store_true", help="Calculate MFE/MAE metrics"
    )
    operations.add_argument(
        "--estimate-entry", action="store_true", help="Estimate entry date/price"
    )
    operations.add_argument(
        "--verify-signal",
        action="store_true",
        help="Verify entry signal occurred on specified date",
    )
    operations.add_argument(
        "--update-open-positions",
        action="store_true",
        help="Update dynamic metrics for open positions in portfolio",
    )

    # Position parameters
    position_group = parser.add_argument_group("Position Parameters")
    position_group.add_argument(
        "--ticker", type=str, help="Ticker symbol (e.g., AAPL, BTC-USD)"
    )
    position_group.add_argument(
        "--strategy", type=str, help="Strategy type (SMA, EMA, MACD, RSI)"
    )
    position_group.add_argument(
        "--short-window", "--short", type=int, help="Short window period"
    )
    position_group.add_argument(
        "--long-window", "--long", type=int, help="Long window period"
    )
    position_group.add_argument(
        "--signal-window", type=int, default=0, help="Signal window period"
    )
    position_group.add_argument(
        "--entry-date", type=str, help="Entry date (YYYY-MM-DD)"
    )
    position_group.add_argument("--entry-price", type=float, help="Entry price")
    position_group.add_argument("--exit-date", type=str, help="Exit date (YYYY-MM-DD)")
    position_group.add_argument("--exit-price", type=float, help="Exit price")
    position_group.add_argument(
        "--position-size", type=float, default=1.0, help="Position size"
    )
    position_group.add_argument(
        "--direction",
        type=str,
        default="Long",
        choices=["Long", "Short"],
        help="Position direction",
    )
    position_group.add_argument(
        "--portfolio", type=str, default="live_signals", help="Portfolio name"
    )
    position_group.add_argument(
        "--timeframe",
        type=str,
        default="D",
        help="Price data timeframe (D, H, 5m, etc.)",
    )
    position_group.add_argument(
        "--no-verify-signal", action="store_true", help="Skip entry signal verification"
    )

    # Bulk operations
    bulk_group = parser.add_argument_group("Bulk Operations")
    bulk_group.add_argument(
        "--strategy-csv", type=str, help="Path to strategy CSV file"
    )

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

    logger = logging.getLogger(__name__)

    try:
        # Set up configuration
        if args.base_dir:
            config = TradingSystemConfig(base_dir=args.base_dir)
            set_config(config)
            config.ensure_directories()
            logger.info(f"Using base directory: {config.base_dir}")

        # Validate configuration
        if args.validate_config:
            config = get_config()
            logger.info(f"Configuration valid:")
            logger.info(f"  Base dir: {config.base_dir}")
            logger.info(f"  Price data: {config.price_data_dir}")
            logger.info(f"  Positions: {config.positions_dir}")
            return 0

        # Handle operations
        if args.add_qcom:
            entry_date = args.entry_date or "20250624"
            portfolio = args.portfolio or "live_signals"

            if args.dry_run:
                logger.info(
                    f"DRY RUN: Would add QCOM SMA 49/66 position (entry: {entry_date}, portfolio: {portfolio})"
                )
                return 0

            uuid = add_qcom_position(entry_date=entry_date, portfolio_name=portfolio)
            print(f"Added QCOM position: {uuid}")

        elif args.add_position:
            if not all(
                [args.ticker, args.strategy, args.short_window, args.long_window]
            ):
                logger.error(
                    "Missing required arguments: --ticker, --strategy, --short-window, --long-window"
                )
                return 1

            if args.dry_run:
                logger.info(
                    f"DRY RUN: Would add {args.ticker} {args.strategy} {args.short_window}/{args.long_window} to {args.portfolio}"
                )
                return 0

            uuid = add_position_to_portfolio(
                ticker=args.ticker,
                strategy_type=args.strategy,
                short_window=args.short_window,
                long_window=args.long_window,
                signal_window=args.signal_window,
                entry_date=args.entry_date,
                entry_price=args.entry_price,
                exit_date=args.exit_date,
                exit_price=args.exit_price,
                position_size=args.position_size,
                direction=args.direction,
                portfolio_name=args.portfolio,
                verify_signal=not args.no_verify_signal,
            )
            print(f"Added position: {uuid}")

        elif args.quick_add:
            if not all(
                [args.ticker, args.strategy, args.short_window, args.long_window]
            ):
                logger.error(
                    "Missing required arguments: --ticker, --strategy, --short, --long"
                )
                return 1

            if args.dry_run:
                logger.info(
                    f"DRY RUN: Would quick-add {args.ticker} {args.strategy} {args.short_window}/{args.long_window} to {args.portfolio}"
                )
                return 0

            uuid = add_position_to_portfolio(
                ticker=args.ticker,
                strategy_type=args.strategy,
                short_window=args.short_window,
                long_window=args.long_window,
                portfolio_name=args.portfolio,
                verify_signal=not args.no_verify_signal,
            )
            print(f"Quick added position: {uuid}")

        elif args.bulk_add:
            if not args.strategy_csv:
                logger.error("Missing required argument: --strategy-csv")
                return 1

            if args.dry_run:
                logger.info(
                    f"DRY RUN: Would bulk add from {args.strategy_csv} to {args.portfolio}"
                )
                return 0

            uuids = bulk_add_positions_from_strategy_csv(
                args.strategy_csv, args.portfolio
            )
            print(f"Bulk added {len(uuids)} positions to {args.portfolio}")
            for uuid in uuids:
                print(f"  {uuid}")

        elif args.create_position:
            if not all(
                [args.ticker, args.strategy, args.short_window, args.long_window]
            ):
                logger.error(
                    "Missing required arguments: --ticker, --strategy, --short-window, --long-window"
                )
                return 1

            if args.dry_run:
                logger.info(
                    f"DRY RUN: Would create detailed position for {args.ticker}"
                )
                return 0

            position = create_position_record(
                ticker=args.ticker,
                strategy_type=args.strategy,
                short_window=args.short_window,
                long_window=args.long_window,
                signal_window=args.signal_window,
                entry_date=args.entry_date,
                entry_price=args.entry_price,
                exit_date=args.exit_date,
                exit_price=args.exit_price,
                position_size=args.position_size,
                direction=args.direction,
            )
            print("Created position record:")
            for key, value in position.items():
                if value is not None:
                    print(f"  {key}: {value}")

        elif args.calculate_mfe_mae:
            if not all([args.ticker, args.entry_date, args.entry_price]):
                logger.error(
                    "Missing required arguments: --ticker, --entry-date, --entry-price"
                )
                return 1

            mfe, mae, ratio, exit_eff = calculate_mfe_mae(
                ticker=args.ticker,
                entry_date=args.entry_date,
                exit_date=args.exit_date or "",
                entry_price=args.entry_price,
                direction=args.direction,
                timeframe=args.timeframe,
            )

            print(f"MFE/MAE Analysis for {args.ticker}:")
            print(
                f"  Max Favorable Excursion: {mfe:.4f} ({mfe*100:.2f}%)"
                if mfe
                else "  MFE: N/A"
            )
            print(
                f"  Max Adverse Excursion: {mae:.4f} ({mae*100:.2f}%)"
                if mae
                else "  MAE: N/A"
            )
            print(f"  MFE/MAE Ratio: {ratio:.2f}" if ratio else "  Ratio: N/A")

            if mfe and mae:
                quality = assess_trade_quality(mfe, mae, exit_eff)
                print(f"  Trade Quality: {quality}")

        elif args.estimate_entry:
            if not all(
                [args.ticker, args.strategy, args.short_window, args.long_window]
            ):
                logger.error(
                    "Missing required arguments: --ticker, --strategy, --short-window, --long-window"
                )
                return 1

            entry_date, entry_price = estimate_strategy_entry_date(
                args.ticker,
                args.strategy,
                args.short_window,
                args.long_window,
                args.timeframe,
            )

            if entry_date and entry_price:
                print(
                    f"Estimated entry for {args.ticker} {args.strategy} {args.short_window}/{args.long_window}:"
                )
                print(f"  Entry Date: {entry_date}")
                print(f"  Entry Price: ${entry_price:.2f}")
            else:
                print(f"Could not estimate entry for {args.ticker}")
                return 1

        elif args.verify_signal:
            if not all(
                [
                    args.ticker,
                    args.strategy,
                    args.short_window,
                    args.long_window,
                    args.entry_date,
                ]
            ):
                logger.error(
                    "Missing required arguments: --ticker, --strategy, --short-window, --long-window, --entry-date"
                )
                return 1

            signal_verified, verification_msg, signal_details = verify_entry_signal(
                ticker=args.ticker,
                strategy_type=args.strategy,
                short_window=args.short_window,
                long_window=args.long_window,
                entry_date=args.entry_date,
                timeframe=args.timeframe,
            )

            print(
                f"Signal Verification for {args.ticker} {args.strategy} {args.short_window}/{args.long_window} on {args.entry_date}:"
            )
            print(f"  {verification_msg}")

            if signal_details:
                print(f"\nSignal Details:")
                print(f"  Close Price: ${signal_details['close_price']:.2f}")
                print(
                    f"  {args.strategy}{args.short_window}: ${signal_details['current_short_ma']:.2f} (prev: ${signal_details['previous_short_ma']:.2f})"
                )
                print(
                    f"  {args.strategy}{args.long_window}: ${signal_details['current_long_ma']:.2f} (prev: ${signal_details['previous_long_ma']:.2f})"
                )
                print(
                    f"  MA Spread: ${signal_details['ma_spread']:.2f} (prev: ${signal_details['prev_ma_spread']:.2f})"
                )

                if signal_details["bullish_crossover"]:
                    print(f"  Signal Type: Bullish Crossover (Long Entry)")
                elif signal_details["bearish_crossover"]:
                    print(f"  Signal Type: Bearish Crossover (Short Entry)")
                else:
                    print(f"  Signal Type: No Crossover Detected")

            # Return exit code based on verification result
            return 0 if signal_verified else 1

        elif args.update_open_positions:
            if not args.portfolio:
                logger.error("Missing required argument: --portfolio")
                return 1

            # Get or set up configuration
            config = get_config()
            if config is None:
                config = TradingSystemConfig()
                set_config(config)

            # Import the update logic used in the successful direct execution
            import numpy as np

            def read_price_data_fixed(ticker):
                try:
                    price_file = config.price_data_dir / f"{ticker}_D.csv"
                    if not price_file.exists():
                        return None

                    with open(price_file, "r") as f:
                        lines = f.readlines()

                    data_start = 0
                    for i, line in enumerate(lines):
                        if line.startswith("20"):
                            data_start = i
                            break

                    if data_start == 0:
                        return None

                    df = pd.read_csv(
                        price_file,
                        skiprows=data_start,
                        header=None,
                        names=["Date", "Close", "High", "Low", "Open", "Volume"],
                    )
                    df["Date"] = pd.to_datetime(df["Date"])
                    df.set_index("Date", inplace=True)
                    return df

                except Exception as e:
                    if args.verbose:
                        print(f"Error reading {ticker}: {str(e)}")
                    return None

            def calculate_mfe_mae_fixed(
                ticker, entry_date, entry_price, direction="Long"
            ):
                try:
                    price_data = read_price_data_fixed(ticker)
                    if price_data is None:
                        return None, None, None

                    entry_date = pd.to_datetime(entry_date)

                    if entry_date < price_data.index.min():
                        if args.verbose:
                            print(
                                f"   📅 Entry date {entry_date.date()} before available data, using {price_data.index.min().date()}"
                            )
                        entry_date = price_data.index.min()

                    position_data = price_data[entry_date:]

                    if position_data.empty:
                        return None, None, None

                    # Use centralized MFE/MAE calculator
                    calculator = get_mfe_mae_calculator()
                    mfe, mae = calculator.calculate_from_ohlc(
                        entry_price=entry_price,
                        ohlc_data=position_data,
                        direction=direction,
                        high_col="High",
                        low_col="Low",
                    )

                    current_price = position_data["Close"].iloc[-1]
                    if direction.upper() == "LONG":
                        current_excursion = (current_price - entry_price) / entry_price
                    else:
                        current_excursion = (entry_price - current_price) / entry_price

                    return mfe, mae, current_excursion

                except Exception as e:
                    if args.verbose:
                        print(f"Error calculating MFE/MAE for {ticker}: {str(e)}")
                    return None, None, None

            # Main update process
            portfolio_file = config.positions_dir / f"{args.portfolio}.csv"
            if not portfolio_file.exists():
                logger.error(f"Portfolio file not found: {portfolio_file}")
                return 1

            df = pd.read_csv(portfolio_file)
            open_positions = df[df["Status"] == "Open"].copy()

            print(
                f"🔄 Updating dynamic metrics for {len(open_positions)} open positions..."
            )

            updated_count = 0

            for idx, position in open_positions.iterrows():
                ticker = position["Ticker"]
                entry_date = position["Entry_Timestamp"]
                entry_price = position["Avg_Entry_Price"]
                direction = position.get("Direction", "Long")

                if args.verbose:
                    print(
                        f"📊 Processing {ticker} - Entry: {entry_date} @ ${entry_price:.2f}"
                    )

                entry_dt = pd.to_datetime(entry_date)
                days_since_entry = (datetime.now() - entry_dt).days

                mfe, mae, current_excursion = calculate_mfe_mae_fixed(
                    ticker, entry_date, entry_price, direction
                )

                if mfe is not None and mae is not None:
                    df.loc[idx, "Days_Since_Entry"] = days_since_entry
                    df.loc[idx, "Max_Favourable_Excursion"] = mfe
                    df.loc[idx, "Max_Adverse_Excursion"] = mae
                    df.loc[idx, "Current_Unrealized_PnL"] = current_excursion

                    if mae > 0:
                        df.loc[idx, "MFE_MAE_Ratio"] = mfe / mae
                    else:
                        df.loc[idx, "MFE_MAE_Ratio"] = float("inf") if mfe > 0 else 0

                    if current_excursion > 0:
                        df.loc[idx, "Current_Excursion_Status"] = "Favorable"
                    elif current_excursion < 0:
                        df.loc[idx, "Current_Excursion_Status"] = "Adverse"
                    else:
                        df.loc[idx, "Current_Excursion_Status"] = "Neutral"

                    risk_reward_ratio = mfe / mae if mae > 0 else float("inf")

                    # Debug print for trade quality assessment
                    if args.verbose:
                        print(
                            f"   DEBUG: {ticker} - MFE: {mfe:.6f}, MAE: {mae:.6f}, Risk/Reward: {risk_reward_ratio:.2f}"
                        )

                    if mfe < 0.02 and mae > 0.05:
                        trade_quality = "Poor Setup - High Risk, Low Reward"
                        if args.verbose:
                            print(
                                f"   DEBUG: {ticker} - Condition 1 met (MFE < 0.02 and MAE > 0.05)"
                            )
                    elif risk_reward_ratio >= 3.0:
                        trade_quality = "Excellent"
                        if args.verbose:
                            print(
                                f"   DEBUG: {ticker} - Condition 2 met (Risk/Reward >= 3.0)"
                            )
                    elif risk_reward_ratio >= 2.0:
                        trade_quality = "Excellent"
                        if args.verbose:
                            print(
                                f"   DEBUG: {ticker} - Condition 3 met (Risk/Reward >= 2.0)"
                            )
                    elif risk_reward_ratio >= 1.5:
                        trade_quality = "Good"
                        if args.verbose:
                            print(
                                f"   DEBUG: {ticker} - Condition 4 met (Risk/Reward >= 1.5)"
                            )
                    else:
                        trade_quality = "Poor"
                        if args.verbose:
                            print(f"   DEBUG: {ticker} - Default condition met (Poor)")

                    if args.verbose:
                        print(
                            f"   DEBUG: {ticker} - Final trade quality: {trade_quality}"
                        )

                    df.loc[idx, "Trade_Quality"] = trade_quality

                    if args.verbose:
                        print(
                            f"   ✅ MFE: {mfe:.4f}, MAE: {mae:.4f}, Current P&L: {current_excursion:.4f}, Quality: {trade_quality}"
                        )
                    updated_count += 1
                else:
                    if args.verbose:
                        print(f"   ⚠️  Could not calculate metrics for {ticker}")

            if not args.dry_run:
                df.to_csv(portfolio_file, index=False)
                print(
                    f"✅ DYNAMIC METRICS UPDATED: {updated_count} positions in {args.portfolio}"
                )
            else:
                print(
                    f"🔍 DRY RUN: Would update {updated_count} positions in {args.portfolio}"
                )

            return 0

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            logger.exception("Full error details:")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
