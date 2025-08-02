"""
Trade History Service

Focused service for trade history operations including updating open positions,
calculating MFE/MAE metrics, and position management.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from app.cli.utils import resolve_portfolio_path
from app.tools.utils.mfe_mae_calculator import get_mfe_mae_calculator


class TradeHistoryService:
    """
    Service for trade history operations.

    This service handles:
    - Updating open positions with current market data
    - Calculating MFE/MAE metrics
    - Updating trade quality assessments
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        base_dir: Optional[Path] = None,
    ):
        """Initialize the service."""
        self.logger = logger or logging.getLogger(__name__)
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

    def update_open_positions(
        self,
        portfolio_name: str,
        dry_run: bool = False,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Update dynamic metrics for open positions in a portfolio.

        Args:
            portfolio_name: Name of the portfolio to update
            dry_run: If True, preview changes without saving
            verbose: Enable verbose logging

        Returns:
            Dict containing update results and statistics
        """
        try:
            # Get portfolio file path
            portfolio_file = (
                self.base_dir
                / "data"
                / "raw"
                / "positions"
                / resolve_portfolio_path(portfolio_name)
            )

            if not portfolio_file.exists():
                raise FileNotFoundError(f"Portfolio file not found: {portfolio_file}")

            # Load portfolio data
            df = pd.read_csv(portfolio_file)
            open_positions = df[df["Status"] == "Open"].copy()

            if open_positions.empty:
                return {
                    "success": True,
                    "message": f"No open positions found in {portfolio_name}",
                    "updated_count": 0,
                    "total_positions": len(df),
                }

            self.logger.info(
                f"Updating dynamic metrics for {len(open_positions)} open positions..."
            )

            updated_count = 0
            errors = []

            for idx, position in open_positions.iterrows():
                try:
                    ticker = position["Ticker"]
                    entry_date = position["Entry_Timestamp"]
                    entry_price = position["Avg_Entry_Price"]
                    direction = position.get("Direction", "Long")

                    if verbose:
                        self.logger.info(
                            f"Processing {ticker} - Entry: {entry_date} @ ${entry_price:.2f}"
                        )

                    # Calculate days since entry
                    entry_dt = pd.to_datetime(entry_date)
                    days_since_entry = (datetime.now() - entry_dt).days

                    # Calculate MFE/MAE metrics
                    (
                        mfe,
                        mae,
                        current_excursion,
                        error_msg,
                    ) = self._calculate_position_metrics(
                        ticker, entry_date, entry_price, direction, verbose
                    )

                    if mfe is not None and mae is not None:
                        # Update position metrics
                        df.loc[idx, "Days_Since_Entry"] = days_since_entry
                        df.loc[idx, "Max_Favourable_Excursion"] = mfe
                        df.loc[idx, "Max_Adverse_Excursion"] = mae
                        df.loc[idx, "Current_Unrealized_PnL"] = current_excursion

                        # Calculate MFE/MAE ratio
                        if mae > 0:
                            df.loc[idx, "MFE_MAE_Ratio"] = mfe / mae
                        else:
                            df.loc[idx, "MFE_MAE_Ratio"] = (
                                float("inf") if mfe > 0 else 0
                            )

                        # Update excursion status
                        if current_excursion > 0:
                            df.loc[idx, "Current_Excursion_Status"] = "Favorable"
                        elif current_excursion < 0:
                            df.loc[idx, "Current_Excursion_Status"] = "Adverse"
                        else:
                            df.loc[idx, "Current_Excursion_Status"] = "Neutral"

                        # Assess trade quality
                        trade_quality = self._assess_trade_quality(
                            mfe, mae, verbose, ticker
                        )
                        df.loc[idx, "Trade_Quality"] = trade_quality

                        if verbose:
                            self.logger.info(
                                f"   ✅ MFE: {mfe:.4f}, MAE: {mae:.4f}, "
                                f"Current P&L: {current_excursion:.4f}, Quality: {trade_quality}"
                            )

                        updated_count += 1
                    else:
                        if error_msg:
                            full_error_msg = (
                                f"Could not calculate metrics for {ticker}: {error_msg}"
                            )
                        else:
                            full_error_msg = f"Could not calculate metrics for {ticker}"
                        errors.append(full_error_msg)
                        if verbose:
                            self.logger.warning(f"   ⚠️  {full_error_msg}")

                except Exception as e:
                    error_msg = f"Error processing {ticker}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            # Save results if not dry run
            if not dry_run:
                df.to_csv(portfolio_file, index=False)
                message = f"DYNAMIC METRICS UPDATED: {updated_count} positions in {portfolio_name}"
            else:
                message = f"DRY RUN: Would update {updated_count} positions in {portfolio_name}"

            return {
                "success": True,
                "message": message,
                "updated_count": updated_count,
                "total_positions": len(df),
                "open_positions": len(open_positions),
                "errors": errors,
                "dry_run": dry_run,
            }

        except Exception as e:
            self.logger.error(f"Failed to update open positions: {str(e)}")
            return {
                "success": False,
                "message": f"Update failed: {str(e)}",
                "updated_count": 0,
                "errors": [str(e)],
            }

    def update_all_positions(
        self,
        portfolio_name: str,
        dry_run: bool = False,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Update dynamic metrics for ALL positions in a portfolio (both open and closed).

        This is the comprehensive refresh mode that recalculates MFE/MAE metrics,
        P&L, and all dynamic fields for every position in the portfolio using
        the latest price data.

        Args:
            portfolio_name: Name of the portfolio to update
            dry_run: If True, preview changes without saving
            verbose: Enable verbose logging

        Returns:
            Dict containing update results and statistics
        """
        try:
            # Get portfolio file path
            portfolio_file = (
                self.base_dir
                / "data"
                / "raw"
                / "positions"
                / resolve_portfolio_path(portfolio_name)
            )

            if not portfolio_file.exists():
                raise FileNotFoundError(f"Portfolio file not found: {portfolio_file}")

            # Load portfolio data - process ALL positions
            df = pd.read_csv(portfolio_file)

            if df.empty:
                return {
                    "success": True,
                    "message": f"Portfolio {portfolio_name} is empty",
                    "updated_count": 0,
                    "total_positions": 0,
                }

            self.logger.info(
                f"Refreshing ALL positions: {len(df)} total positions in {portfolio_name}..."
            )

            updated_count = 0
            errors = []

            # First, calculate the earliest date needed and force refresh price data
            unique_tickers = df["Ticker"].unique()
            # Handle mixed date formats using 'mixed' format
            earliest_date = pd.to_datetime(df["Entry_Timestamp"], format="mixed").min()

            if verbose:
                self.logger.info(
                    f"Force refreshing price data for {len(unique_tickers)} tickers..."
                )
                self.logger.info(f"Earliest position date: {earliest_date.date()}")

            # Download fresh price data with appropriate historical coverage
            self._refresh_price_data(unique_tickers, earliest_date, verbose)

            # Process ALL positions (both open and closed)
            for idx, position in df.iterrows():
                try:
                    ticker = position["Ticker"]
                    entry_date = position["Entry_Timestamp"]
                    entry_price = position["Avg_Entry_Price"]
                    direction = position.get("Direction", "Long")
                    status = position.get("Status", "Unknown")

                    if verbose:
                        self.logger.info(
                            f"Processing {ticker} ({status}) - Entry: {entry_date} @ ${entry_price:.2f}"
                        )

                    # Calculate days since entry - handle mixed date formats
                    entry_dt = pd.to_datetime(entry_date, format="mixed")
                    days_since_entry = (datetime.now() - entry_dt).days

                    # For closed positions, use exit date if available
                    if status == "Closed" and pd.notna(position.get("Exit_Timestamp")):
                        exit_dt = pd.to_datetime(
                            position["Exit_Timestamp"], format="mixed"
                        )
                        actual_duration = (exit_dt - entry_dt).days
                        exit_date = position["Exit_Timestamp"]
                    else:
                        actual_duration = days_since_entry
                        exit_date = None

                    # Calculate MFE/MAE metrics (works for both open and closed positions)
                    (
                        mfe,
                        mae,
                        current_excursion,
                        error_msg,
                    ) = self._calculate_position_metrics_comprehensive(
                        ticker, entry_date, entry_price, direction, exit_date, verbose
                    )

                    if mfe is not None and mae is not None:
                        # Update position metrics
                        df.loc[idx, "Days_Since_Entry"] = days_since_entry
                        df.loc[idx, "Max_Favourable_Excursion"] = mfe
                        df.loc[idx, "Max_Adverse_Excursion"] = mae

                        # Calculate MFE/MAE ratio
                        if mae > 0:
                            df.loc[idx, "MFE_MAE_Ratio"] = mfe / mae
                        else:
                            df.loc[idx, "MFE_MAE_Ratio"] = (
                                float("inf") if mfe > 0 else 0
                            )

                        # Update excursion status and current P&L
                        if status == "Open":
                            df.loc[idx, "Current_Unrealized_PnL"] = current_excursion
                            if current_excursion > 0:
                                df.loc[idx, "Current_Excursion_Status"] = "Favorable"
                            elif current_excursion < 0:
                                df.loc[idx, "Current_Excursion_Status"] = "Adverse"
                            else:
                                df.loc[idx, "Current_Excursion_Status"] = "Neutral"
                        else:
                            # For closed positions, use the actual return
                            if pd.notna(position.get("Return")):
                                df.loc[idx, "Current_Unrealized_PnL"] = position[
                                    "Return"
                                ]
                                if position["Return"] > 0:
                                    df.loc[
                                        idx, "Current_Excursion_Status"
                                    ] = "Favorable"
                                elif position["Return"] < 0:
                                    df.loc[idx, "Current_Excursion_Status"] = "Adverse"
                                else:
                                    df.loc[idx, "Current_Excursion_Status"] = "Neutral"

                        # Calculate exit efficiency for positions with MFE
                        if mfe > 0 and pd.notna(position.get("Return")):
                            exit_efficiency = position["Return"] / mfe
                            df.loc[idx, "Exit_Efficiency_Fixed"] = round(
                                exit_efficiency, 4
                            )

                        # Assess trade quality
                        trade_quality = self._assess_trade_quality(
                            mfe, mae, verbose, ticker
                        )
                        df.loc[idx, "Trade_Quality"] = trade_quality

                        if verbose:
                            self.logger.info(
                                f"   ✅ MFE: {mfe:.4f}, MAE: {mae:.4f}, "
                                f"Quality: {trade_quality}"
                            )

                        updated_count += 1
                    else:
                        if error_msg:
                            full_error_msg = (
                                f"Could not calculate metrics for {ticker}: {error_msg}"
                            )
                        else:
                            full_error_msg = f"Could not calculate metrics for {ticker}"
                        errors.append(full_error_msg)
                        if verbose:
                            self.logger.warning(f"   ⚠️  {full_error_msg}")

                except Exception as e:
                    error_msg = f"Error processing {ticker}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            # Save results if not dry run
            if not dry_run:
                df.to_csv(portfolio_file, index=False)
                message = f"COMPREHENSIVE REFRESH COMPLETE: {updated_count} positions refreshed in {portfolio_name}"
            else:
                message = f"DRY RUN: Would refresh {updated_count} positions in {portfolio_name}"

            return {
                "success": True,
                "message": message,
                "updated_count": updated_count,
                "total_positions": len(df),
                "open_positions": len(df[df["Status"] == "Open"]),
                "closed_positions": len(df[df["Status"] == "Closed"]),
                "errors": errors,
                "dry_run": dry_run,
                "refresh_mode": True,
            }

        except Exception as e:
            self.logger.error(f"Failed to refresh all positions: {str(e)}")
            return {
                "success": False,
                "message": f"Refresh failed: {str(e)}",
                "updated_count": 0,
                "errors": [str(e)],
                "refresh_mode": True,
            }

    def _refresh_price_data(
        self, tickers: list, earliest_date: Optional[str] = None, verbose: bool = False
    ) -> None:
        """
        Force refresh price data for the given tickers.

        Downloads fresh price data from yfinance to ensure calculations
        use the most current market data available.

        Args:
            tickers: List of ticker symbols to download
            earliest_date: Earliest date needed for position calculations
            verbose: Enable verbose logging
        """
        try:
            from datetime import datetime, timedelta

            import yfinance as yf

            # Calculate appropriate period based on earliest date
            if earliest_date:
                earliest_dt = pd.to_datetime(earliest_date)
                days_back = (
                    datetime.now() - earliest_dt
                ).days + 30  # Add 30-day buffer

                # Cap at reasonable maximum (yfinance limits)
                max_days = min(days_back, 730)  # Max 2 years for daily data
                period_str = f"{max_days}d"

                if verbose:
                    self.logger.info(
                        f"   📅 Downloading {max_days} days of historical data (from {earliest_dt.date()})"
                    )
            else:
                # Default to downloading significant history
                period_str = "1y"  # 1 year of data
                if verbose:
                    self.logger.info(f"   📅 Downloading 1 year of historical data")

            for ticker in tickers:
                try:
                    if verbose:
                        self.logger.info(
                            f"   📈 Downloading price data for {ticker} (period: {period_str})..."
                        )

                    # Download appropriate historical period
                    data = yf.download(ticker, period=period_str, progress=False)

                    if not data.empty:
                        # Reset index to have Date as column
                        data.reset_index(inplace=True)

                        # Save to price data file
                        price_file = (
                            self.base_dir
                            / "data"
                            / "raw"
                            / "prices"
                            / f"{ticker}_D.csv"
                        )
                        price_file.parent.mkdir(parents=True, exist_ok=True)
                        data.to_csv(price_file, index=False)

                        # Show data coverage info
                        date_range = f"{data['Date'].min().date()} to {data['Date'].max().date()}"
                        if verbose:
                            self.logger.info(
                                f"   ✅ Updated {ticker}: {len(data)} days ({date_range})"
                            )
                    else:
                        if verbose:
                            self.logger.warning(
                                f"   ⚠️  No data available for {ticker}"
                            )

                except Exception as e:
                    if verbose:
                        self.logger.warning(
                            f"   ❌ Failed to update price data for {ticker}: {str(e)}"
                        )

        except ImportError:
            self.logger.warning("yfinance not available - skipping price data refresh")
        except Exception as e:
            self.logger.error(f"Error refreshing price data: {str(e)}")

    def _calculate_position_metrics_comprehensive(
        self,
        ticker: str,
        entry_date: str,
        entry_price: float,
        direction: str = "Long",
        exit_date: Optional[str] = None,
        verbose: bool = False,
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[str]]:
        """
        Calculate MFE, MAE, and current excursion for both open and closed positions.

        This method handles both open positions (no exit_date) and closed positions
        (with exit_date) to provide comprehensive metrics calculation.

        Returns:
            tuple: (mfe, mae, current_excursion, error_message)
        """
        try:
            price_data, error_msg = self._read_prices(ticker)

            if price_data is None:
                return None, None, None, error_msg

            entry_date = pd.to_datetime(entry_date, format="mixed")

            # Handle entry date before data starts
            if entry_date < price_data.index.min():
                if verbose:
                    self.logger.info(
                        f"   📅 Entry date {entry_date.date()} before available data, "
                        f"using {price_data.index.min().date()}"
                    )
                entry_date = price_data.index.min()

            # For closed positions, limit data to exit date
            if exit_date:
                exit_date = pd.to_datetime(
                    exit_date, format="mixed"
                ).date()  # Convert to date only
                entry_date_only = entry_date.date()  # Convert to date only
                # Filter by date comparison
                position_data = price_data[
                    (price_data.index.date >= entry_date_only)
                    & (price_data.index.date <= exit_date)
                ]
            else:
                # For open positions, use all data from entry to present
                position_data = price_data[entry_date:]

            if position_data.empty:
                # Enhanced error message with specific date ranges
                available_range = f"{price_data.index.min().date()} to {price_data.index.max().date()}"
                if exit_date:
                    needed_range = f"{entry_date.date()} to {exit_date}"
                else:
                    needed_range = f"{entry_date.date()} to present"

                return (
                    None,
                    None,
                    None,
                    f"Price data insufficient for {ticker}. Available: {available_range}, Needed: {needed_range}",
                )

            # Use centralized MFE/MAE calculator
            calculator = get_mfe_mae_calculator()
            mfe, mae = calculator.calculate_from_ohlc(
                entry_price=entry_price,
                ohlc_data=position_data,
                direction=direction,
                high_col="High",
                low_col="Low",
            )

            # Calculate current excursion (or final excursion for closed positions)
            current_price = position_data["Close"].iloc[-1]
            if direction.upper() == "LONG":
                current_excursion = (current_price - entry_price) / entry_price
            else:
                current_excursion = (entry_price - current_price) / entry_price

            return mfe, mae, current_excursion, None

        except Exception as e:
            error_msg = (
                f"Error calculating comprehensive MFE/MAE for {ticker}: {str(e)}"
            )
            if verbose:
                self.logger.error(error_msg)
            return None, None, None, error_msg

    def _read_prices(self, ticker: str) -> tuple[Optional[pd.DataFrame], Optional[str]]:
        """Read price data for a ticker.

        Returns:
            tuple: (DataFrame, error_message) - DataFrame is None if error occurred
        """
        try:
            price_file = self.base_dir / "data" / "raw" / "prices" / f"{ticker}_D.csv"

            if not price_file.exists():
                return (
                    None,
                    f"Price data file not found: data/raw/prices/{ticker}_D.csv",
                )

            # Skip row 1 (index 1) which contains ticker symbols instead of data
            df = pd.read_csv(price_file, skiprows=[1])

            if df.empty:
                return None, f"Price data file is empty: data/raw/prices/{ticker}_D.csv"

            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)

            required_columns = ["Close", "High", "Low", "Open", "Volume"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return (
                    None,
                    f"Missing required columns in price data: {', '.join(missing_columns)}",
                )

            return df, None

        except Exception as e:
            return None, f"Error reading price data file: {str(e)}"

    def _calculate_position_metrics(
        self,
        ticker: str,
        entry_date: str,
        entry_price: float,
        direction: str = "Long",
        verbose: bool = False,
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[str]]:
        """Calculate MFE, MAE, and current excursion for a position.

        Returns:
            tuple: (mfe, mae, current_excursion, error_message)
        """
        try:
            price_data, error_msg = self._read_prices(ticker)

            if price_data is None:
                return None, None, None, error_msg

            entry_date = pd.to_datetime(entry_date, format="mixed")

            # Handle entry date before data starts
            if entry_date < price_data.index.min():
                if verbose:
                    self.logger.info(
                        f"   📅 Entry date {entry_date.date()} before available data, "
                        f"using {price_data.index.min().date()}"
                    )
                entry_date = price_data.index.min()

            position_data = price_data[entry_date:]

            if position_data.empty:
                return (
                    None,
                    None,
                    None,
                    f"No price data available for {ticker} after entry date {entry_date.date()}",
                )

            # Use centralized MFE/MAE calculator
            calculator = get_mfe_mae_calculator()
            mfe, mae = calculator.calculate_from_ohlc(
                entry_price=entry_price,
                ohlc_data=position_data,
                direction=direction,
                high_col="High",
                low_col="Low",
            )

            # Calculate current excursion
            current_price = position_data["Close"].iloc[-1]
            if direction.upper() == "LONG":
                current_excursion = (current_price - entry_price) / entry_price
            else:
                current_excursion = (entry_price - current_price) / entry_price

            return mfe, mae, current_excursion, None

        except Exception as e:
            error_msg = f"Error calculating MFE/MAE for {ticker}: {str(e)}"
            if verbose:
                self.logger.error(error_msg)
            return None, None, None, error_msg

    def _assess_trade_quality(
        self,
        mfe: float,
        mae: float,
        verbose: bool = False,
        ticker: str = "",
    ) -> str:
        """Assess trade quality based on MFE/MAE metrics."""
        risk_reward_ratio = mfe / mae if mae > 0 else float("inf")

        if verbose:
            self.logger.debug(
                f"   DEBUG: {ticker} - MFE: {mfe:.6f}, MAE: {mae:.6f}, "
                f"Risk/Reward: {risk_reward_ratio:.2f}"
            )

        if mfe < 0.02 and mae > 0.05:
            trade_quality = "Poor Setup - High Risk, Low Reward"
            if verbose:
                self.logger.debug(
                    f"   DEBUG: {ticker} - Condition 1 met (MFE < 0.02 and MAE > 0.05)"
                )
        elif risk_reward_ratio >= 3.0:
            trade_quality = "Excellent"
            if verbose:
                self.logger.debug(
                    f"   DEBUG: {ticker} - Condition 2 met (Risk/Reward >= 3.0)"
                )
        elif risk_reward_ratio >= 2.0:
            trade_quality = "Excellent"
            if verbose:
                self.logger.debug(
                    f"   DEBUG: {ticker} - Condition 3 met (Risk/Reward >= 2.0)"
                )
        elif risk_reward_ratio >= 1.5:
            trade_quality = "Good"
            if verbose:
                self.logger.debug(
                    f"   DEBUG: {ticker} - Condition 4 met (Risk/Reward >= 1.5)"
                )
        else:
            trade_quality = "Poor"
            if verbose:
                self.logger.debug(f"   DEBUG: {ticker} - Default condition met (Poor)")

        if verbose:
            self.logger.debug(
                f"   DEBUG: {ticker} - Final trade quality: {trade_quality}"
            )

        return trade_quality
