"""
Trade History Service

Focused service for trade history operations including updating open positions,
calculating MFE/MAE metrics, and position management with comprehensive refresh
capabilities using centralized PositionCalculator.

This service now delegates core position operations to the unified PositionService
while maintaining its existing interface for backward compatibility.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.cli.utils import resolve_portfolio_path
from app.services import PositionService
from app.services.position_service import TradingSystemConfig
from app.tools.position_calculator import get_position_calculator
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

        # Create unified PositionService for delegation
        config = TradingSystemConfig(str(self.base_dir))
        self.position_service = PositionService(config, self.logger)

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
        validate_calculations: bool = True,
        auto_fix_errors: bool = True,
    ) -> Dict[str, Any]:
        """
        Comprehensive refresh of ALL positions using centralized PositionCalculator.

        This method recalculates ALL derived fields including P&L, Return, MFE/MAE,
        Exit Efficiency, and Trade Quality with standardized precision. It also
        validates calculations and auto-fixes any inconsistencies found.

        Args:
            portfolio_name: Name of the portfolio to update
            dry_run: If True, preview changes without saving
            verbose: Enable verbose logging
            validate_calculations: If True, validate all calculations for consistency
            auto_fix_errors: If True, auto-fix calculation errors found during validation

        Returns:
            Dict containing update results, validation info, and statistics
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
                f"COMPREHENSIVE REFRESH: {len(df)} total positions in {portfolio_name}..."
            )

            # Initialize PositionCalculator
            calculator = get_position_calculator(self.logger)

            updated_count = 0
            validation_errors = []
            calculation_fixes = []
            errors = []

            # First, refresh price data for all tickers
            unique_tickers = df["Ticker"].unique()
            earliest_date = pd.to_datetime(df["Entry_Timestamp"], format="mixed").min()

            if verbose:
                self.logger.info(
                    f"🔄 Refreshing price data for {len(unique_tickers)} tickers..."
                )

            self._refresh_price_data(unique_tickers, earliest_date, verbose)

            # Process ALL positions with comprehensive refresh
            for idx, position in df.iterrows():
                try:
                    ticker = position["Ticker"]
                    entry_date = position["Entry_Timestamp"]
                    entry_price = position["Avg_Entry_Price"]
                    exit_price = position.get("Avg_Exit_Price")
                    position_size = position.get("Position_Size", 1.0)
                    direction = position.get("Direction", "Long")
                    status = position.get("Status", "Unknown")

                    if verbose:
                        self.logger.info(
                            f"🔍 Processing {ticker} ({status}) - Entry: {entry_date} @ ${entry_price:.2f}"
                        )

                    # Convert position to dictionary for PositionCalculator
                    position_data = position.to_dict()

                    # Step 1: Calculate updated MFE/MAE using fresh price data
                    exit_date = (
                        position.get("Exit_Timestamp") if status == "Closed" else None
                    )
                    (
                        updated_mfe,
                        updated_mae,
                        current_excursion,
                        mfe_mae_error,
                    ) = self._calculate_position_metrics_comprehensive(
                        ticker, entry_date, entry_price, direction, exit_date, verbose
                    )

                    # Step 2: Use PositionCalculator for comprehensive refresh
                    if updated_mfe is not None and updated_mae is not None:
                        refresh_result = calculator.comprehensive_position_refresh(
                            position_data=position_data,
                            mfe=updated_mfe,
                            mae=updated_mae,
                            current_excursion=current_excursion,
                        )

                        # Apply all refreshed data
                        refreshed_data = refresh_result["data"]
                        changes = refresh_result["changes"]
                        validation_result = refresh_result["validation"]

                        # Update DataFrame with refreshed values
                        for field, value in refreshed_data.items():
                            if field in df.columns:
                                df.loc[idx, field] = value

                        # Track changes made
                        if changes and verbose:
                            self.logger.info(f"   📝 Changes made to {ticker}:")
                            for change in changes:
                                self.logger.info(f"      • {change}")
                                calculation_fixes.append(f"{ticker}: {change}")

                        # Track validation results
                        if not validation_result.get("valid", True):
                            validation_errors.extend(
                                [
                                    f"{ticker}: {error}"
                                    for error in validation_result.get("errors", [])
                                ]
                            )
                            if verbose:
                                self.logger.warning(
                                    f"   ⚠️  Validation issues found for {ticker}"
                                )

                        # Success
                        updated_count += 1

                        if verbose:
                            self.logger.info(
                                f"   ✅ Updated: MFE {updated_mfe:.4f}, MAE {updated_mae:.4f}, "
                                f"Quality: {refreshed_data.get('Trade_Quality', 'Unknown')}"
                            )

                    else:
                        # Could not calculate MFE/MAE - still try to refresh other calculations
                        if exit_price is not None:
                            # At least recalculate P&L and Return using PositionCalculator
                            try:
                                refresh_result = (
                                    calculator.comprehensive_position_refresh(
                                        position_data=position_data
                                    )
                                )

                                refreshed_data = refresh_result["data"]
                                changes = refresh_result["changes"]

                                # Update basic calculations
                                for field in ["PnL", "Return", "Days_Since_Entry"]:
                                    if field in refreshed_data and field in df.columns:
                                        df.loc[idx, field] = refreshed_data[field]

                                if changes and verbose:
                                    self.logger.info(
                                        f"   📝 Basic refresh for {ticker}:"
                                    )
                                    for change in changes:
                                        self.logger.info(f"      • {change}")

                                updated_count += 1

                            except Exception as calc_error:
                                error_msg = f"Basic calculation refresh failed for {ticker}: {str(calc_error)}"
                                errors.append(error_msg)
                                if verbose:
                                    self.logger.warning(f"   ⚠️  {error_msg}")
                        else:
                            # No exit price and no MFE/MAE - record error
                            error_msg = f"Insufficient data for {ticker}: {mfe_mae_error or 'No exit price available'}"
                            errors.append(error_msg)
                            if verbose:
                                self.logger.warning(f"   ❌ {error_msg}")

                except Exception as e:
                    error_msg = f"Error processing {ticker}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            # Step 3: Final validation pass if requested
            if validate_calculations and not dry_run:
                self.logger.info("🔍 Running final validation pass...")
                final_validation_results = self._validate_all_calculations(df, verbose)
                validation_errors.extend(final_validation_results.get("errors", []))

            # Save results if not dry run
            if not dry_run:
                df.to_csv(portfolio_file, index=False)
                message = f"COMPREHENSIVE REFRESH COMPLETE: {updated_count}/{len(df)} positions refreshed"
            else:
                message = f"DRY RUN: Would refresh {updated_count}/{len(df)} positions"

            # Prepare detailed results
            result = {
                "success": True,
                "message": message,
                "updated_count": updated_count,
                "total_positions": len(df),
                "open_positions": len(df[df["Status"] == "Open"]),
                "closed_positions": len(df[df["Status"] == "Closed"]),
                "errors": errors,
                "dry_run": dry_run,
                "refresh_mode": "comprehensive",
                "validation_enabled": validate_calculations,
                "calculation_fixes": calculation_fixes,
                "validation_errors": validation_errors,
            }

            if verbose:
                self.logger.info(
                    f"📊 Summary: {updated_count} updated, {len(errors)} errors, {len(calculation_fixes)} fixes"
                )

            return result

        except Exception as e:
            self.logger.error(f"Failed to refresh all positions: {str(e)}")
            return {
                "success": False,
                "message": f"Comprehensive refresh failed: {str(e)}",
                "updated_count": 0,
                "errors": [str(e)],
                "refresh_mode": "comprehensive",
            }

    def _validate_all_calculations(
        self, df: pd.DataFrame, verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Validate calculations for all positions in the DataFrame.

        Args:
            df: DataFrame containing position data
            verbose: Enable verbose logging

        Returns:
            Dict containing validation results
        """
        try:
            calculator = get_position_calculator(self.logger)
            validation_errors = []
            validation_warnings = []
            corrected_count = 0

            if verbose:
                self.logger.info(
                    f"🔍 Validating calculations for {len(df)} positions..."
                )

            for idx, position in df.iterrows():
                try:
                    position_data = position.to_dict()
                    ticker = position.get("Ticker", "Unknown")

                    validation_result = calculator.validate_calculation_consistency(
                        position_data, tolerance_pnl=0.01, tolerance_return=0.0001
                    )

                    if not validation_result.get("valid", True):
                        # Record validation errors
                        for error in validation_result.get("errors", []):
                            error_msg = f"{ticker}: {error['field']} - Expected {error['expected']}, Got {error['actual']}"
                            validation_errors.append(error_msg)

                            if verbose:
                                self.logger.warning(f"   ❌ {error_msg}")

                        # Apply corrections if available
                        corrected_values = validation_result.get("corrected_values", {})
                        if corrected_values:
                            for field, corrected_value in corrected_values.items():
                                if field in df.columns:
                                    old_value = df.loc[idx, field]
                                    df.loc[idx, field] = corrected_value
                                    corrected_count += 1

                                    if verbose:
                                        self.logger.info(
                                            f"   🔧 Auto-corrected {ticker}.{field}: {old_value} → {corrected_value}"
                                        )

                    # Record validation warnings
                    for warning in validation_result.get("warnings", []):
                        warning_msg = f"{ticker}: {warning['field'] if isinstance(warning, dict) else warning}"
                        validation_warnings.append(warning_msg)

                        if verbose:
                            self.logger.info(f"   ⚠️  {warning_msg}")

                except Exception as e:
                    error_msg = f"Validation error for {ticker}: {str(e)}"
                    validation_errors.append(error_msg)
                    if verbose:
                        self.logger.error(f"   ❌ {error_msg}")

            return {
                "success": True,
                "errors": validation_errors,
                "warnings": validation_warnings,
                "corrected_count": corrected_count,
                "total_validated": len(df),
            }

        except Exception as e:
            self.logger.error(f"Failed to validate calculations: {str(e)}")
            return {
                "success": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": [],
                "corrected_count": 0,
                "total_validated": 0,
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
        final_return: Optional[float] = None,
    ) -> str:
        """Assess trade quality using centralized PositionCalculator."""
        try:
            calculator = get_position_calculator(self.logger)
            trade_quality = calculator.assess_trade_quality(mfe, mae, final_return)

            if verbose:
                risk_reward_ratio = calculator.calculate_mfe_mae_ratio(mfe, mae)
                self.logger.debug(
                    f"   DEBUG: {ticker} - MFE: {mfe:.6f}, MAE: {mae:.6f}, "
                    f"Risk/Reward: {risk_reward_ratio:.2f}, Quality: {trade_quality}"
                )

            return trade_quality

        except Exception as e:
            self.logger.error(f"Error assessing trade quality for {ticker}: {str(e)}")
            return "Unknown"

    # Delegation methods to PositionService for unified operations

    def add_position_to_portfolio(
        self,
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
    ) -> str:
        """Delegate position addition to unified PositionService."""
        return self.position_service.add_position_to_portfolio(
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
            portfolio_name=portfolio_name,
            verify_signal=verify_signal,
        )

    def close_position(
        self,
        position_uuid: str,
        portfolio_name: str,
        exit_price: float,
        exit_date: str = None,
    ) -> Dict[str, Any]:
        """Delegate position closing to unified PositionService."""
        return self.position_service.close_position(
            position_uuid=position_uuid,
            portfolio_name=portfolio_name,
            exit_price=exit_price,
            exit_date=exit_date,
        )

    def list_positions(
        self, portfolio_name: str, status_filter: str = None
    ) -> List[Dict[str, Any]]:
        """Delegate position listing to unified PositionService."""
        return self.position_service.list_positions(portfolio_name, status_filter)

    def get_position(self, position_uuid: str, portfolio_name: str) -> Dict[str, Any]:
        """Delegate position retrieval to unified PositionService."""
        return self.position_service.get_position(position_uuid, portfolio_name)
