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

            df = pd.read_csv(price_file)

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

            if prices is None:
                return None, None, None, error_msg

            entry_date = pd.to_datetime(entry_date)

            # Handle entry date before data starts
            if entry_date < prices.index.min():
                if verbose:
                    self.logger.info(
                        f"   📅 Entry date {entry_date.date()} before available data, "
                        f"using {prices.index.min().date()}"
                    )
                entry_date = prices.index.min()

            position_data = prices[entry_date:]

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
