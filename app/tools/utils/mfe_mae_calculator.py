"""
MFE/MAE Calculator Utility

Centralized calculation of Maximum Favorable Excursion (MFE) and Maximum Adverse Excursion (MAE)
for consistent calculations across the entire trading system codebase.
"""

import logging

import numpy as np
import pandas as pd


class MFEMAECalculator:
    """
    Centralized calculator for Maximum Favorable Excursion (MFE) and Maximum Adverse Excursion (MAE).

    Provides consistent calculations across all trade analysis components with validation
    and error handling for various data formats.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the MFE/MAE calculator

        Args:
            logger: Logger instance for operations
        """
        self.logger = logger or logging.getLogger(__name__)

    def calculate_from_trades(
        self,
        trades_df: pd.DataFrame,
        entry_price_col: str = "entry_price",
        exit_price_col: str = "exit_price",
        direction_col: str = "direction",
        return_col: str = "return_pct",
    ) -> pd.DataFrame:
        """
        Calculate MFE/MAE from trade data with entry/exit prices

        Args:
            trades_df: DataFrame containing trade data
            entry_price_col: Column name for entry price
            exit_price_col: Column name for exit price
            direction_col: Column name for trade direction (Long/Short)
            return_col: Column name for return percentage

        Returns:
            DataFrame with mfe and mae columns added
        """
        df = trades_df.copy()

        try:
            # Ensure required columns exist
            required_cols = [entry_price_col, direction_col, return_col]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                self.logger.warning(f"Missing required columns: {missing_cols}")
                return self._add_default_mfe_mae(df)

            # Convert columns to numeric
            df[return_col] = pd.to_numeric(df[return_col], errors="coerce").fillna(0.0)

            # Calculate MFE/MAE based on direction and return
            df["mfe"] = df.apply(
                lambda row: self._calculate_mfe_single_trade(
                    row[return_col], row[direction_col],
                ),
                axis=1,
            )

            df["mae"] = df.apply(
                lambda row: self._calculate_mae_single_trade(
                    row[return_col], row[direction_col],
                ),
                axis=1,
            )

            self.logger.debug(f"Calculated MFE/MAE for {len(df)} trades")
            return df

        except Exception as e:
            self.logger.exception(f"Error calculating MFE/MAE from trades: {e}")
            return self._add_default_mfe_mae(df)

    def calculate_from_price_series(
        self,
        entry_price: float,
        price_series: list[float] | pd.Series,
        direction: str = "Long",
    ) -> tuple[float, float]:
        """
        Calculate MFE/MAE from a price series (tick data or OHLC data)

        Args:
            entry_price: Entry price for the position
            price_series: Series of prices during the position
            direction: Trade direction ("Long" or "Short")

        Returns:
            Tuple of (mfe, mae)
        """
        try:
            if isinstance(price_series, pd.Series):
                prices = price_series.values
            else:
                prices = np.array(price_series)

            if len(prices) == 0:
                return 0.0, 0.0

            # Calculate returns from entry price
            returns = (prices - entry_price) / entry_price

            if direction.lower() in ["long", "buy", "1"]:
                # For long positions: MFE = max positive return, MAE = max negative return (absolute)
                mfe = max(returns.max(), 0.0)
                mae = abs(min(returns.min(), 0.0))
            else:
                # For short positions: MFE = max negative return (absolute), MAE = max positive return
                mfe = abs(min(returns.min(), 0.0))
                mae = max(returns.max(), 0.0)

            return round(float(mfe), 6), round(float(mae), 6)

        except Exception as e:
            self.logger.exception(f"Error calculating MFE/MAE from price series: {e}")
            return 0.0, 0.0

    def calculate_from_ohlc(
        self,
        entry_price: float,
        ohlc_data: pd.DataFrame,
        direction: str = "Long",
        high_col: str = "high",
        low_col: str = "low",
    ) -> tuple[float, float]:
        """
        Calculate MFE/MAE from OHLC data

        Args:
            entry_price: Entry price for the position
            ohlc_data: DataFrame with OHLC data
            direction: Trade direction
            high_col: Column name for high prices
            low_col: Column name for low prices

        Returns:
            Tuple of (mfe, mae)
        """
        try:
            if ohlc_data.empty:
                return 0.0, 0.0

            # Get extreme prices during the position
            max_high = ohlc_data[high_col].max()
            min_low = ohlc_data[low_col].min()

            if direction.lower() in ["long", "buy", "1"]:
                # For long positions
                mfe = max((max_high - entry_price) / entry_price, 0.0)
                mae = abs(min((min_low - entry_price) / entry_price, 0.0))
            else:
                # For short positions
                mfe = abs(min((min_low - entry_price) / entry_price, 0.0))
                mae = max((max_high - entry_price) / entry_price, 0.0)

            return round(float(mfe), 6), round(float(mae), 6)

        except Exception as e:
            self.logger.exception(f"Error calculating MFE/MAE from OHLC: {e}")
            return 0.0, 0.0

    def calculate_from_returns_only(
        self, returns: list[float] | pd.Series | float, direction: str = "Long",
    ) -> tuple[float, float]:
        """
        Calculate MFE/MAE from return data only (simplified calculation)

        Args:
            returns: Return value(s) - single value or series
            direction: Trade direction

        Returns:
            Tuple of (mfe, mae)
        """
        try:
            # Handle single return value
            if isinstance(returns, int | float):
                return self._calculate_mfe_mae_from_single_return(
                    float(returns), direction,
                )

            # Handle series of returns
            if isinstance(returns, pd.Series):
                return_values = returns.values
            else:
                return_values = np.array(returns)

            if len(return_values) == 0:
                return 0.0, 0.0

            # For series, use min/max approach
            if direction.lower() in ["long", "buy", "1"]:
                mfe = max(return_values.max(), 0.0)
                mae = abs(min(return_values.min(), 0.0))
            else:
                mfe = abs(min(return_values.min(), 0.0))
                mae = max(return_values.max(), 0.0)

            return round(float(mfe), 6), round(float(mae), 6)

        except Exception as e:
            self.logger.exception(f"Error calculating MFE/MAE from returns: {e}")
            return 0.0, 0.0

    def validate_mfe_mae(
        self,
        current_return: float,
        mfe: float,
        mae: float,
        direction: str = "Long",
        tolerance: float = 0.01,
    ) -> list[str]:
        """
        Validate MFE/MAE calculations for logical consistency

        Args:
            current_return: Current/final return of the position
            mfe: Maximum Favorable Excursion
            mae: Maximum Adverse Excursion
            direction: Trade direction
            tolerance: Tolerance for floating point comparisons

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        try:
            # Convert to float and handle edge cases
            current_return = (
                float(current_return) if current_return is not None else 0.0
            )
            mfe = float(mfe) if mfe is not None else 0.0
            mae = float(mae) if mae is not None else 0.0

            # Basic logical checks
            if mfe < 0:
                errors.append(f"MFE should not be negative: {mfe:.4f}")

            if mae < 0:
                errors.append(f"MAE should not be negative: {mae:.4f}")

            # Direction-specific validations
            if direction.lower() in ["long", "buy", "1"]:
                # For long positions
                if current_return > 0 and mfe == 0:
                    errors.append(
                        f"Positive return ({current_return:.4f}) should have MFE > 0",
                    )

                if current_return < 0 and mae == 0:
                    errors.append(
                        f"Negative return ({current_return:.4f}) should have MAE > 0",
                    )

                # Current return should not exceed MFE significantly
                if current_return > mfe + tolerance:
                    errors.append(
                        f"Current return ({current_return:.4f}) exceeds MFE ({mfe:.4f}) by {((current_return - mfe) / abs(mfe) * 100 if mfe != 0 else 100):.1f}%",
                    )

            else:
                # For short positions (reverse logic)
                if current_return < 0 and mfe == 0:
                    errors.append(
                        f"Negative return ({current_return:.4f}) for short should have MFE > 0",
                    )

                if current_return > 0 and mae == 0:
                    errors.append(
                        f"Positive return ({current_return:.4f}) for short should have MAE > 0",
                    )

            return errors

        except Exception as e:
            self.logger.exception(f"Error validating MFE/MAE: {e}")
            return [f"Validation error: {e}"]

    def standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize MFE/MAE column names across different data sources

        Args:
            df: DataFrame with potentially different MFE/MAE column names

        Returns:
            DataFrame with standardized 'mfe' and 'mae' columns
        """
        df = df.copy()

        # Common column name mappings
        mfe_mappings = {
            "Max_Favourable_Excursion": "mfe",
            "max_favorable_excursion": "mfe",
            "max_favourable_excursion": "mfe",
            "MFE": "mfe",
            "MaxFavorableExcursion": "mfe",
        }

        mae_mappings = {
            "Max_Adverse_Excursion": "mae",
            "max_adverse_excursion": "mae",
            "MAE": "mae",
            "MaxAdverseExcursion": "mae",
        }

        # Apply mappings
        for old_name, new_name in mfe_mappings.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})

        for old_name, new_name in mae_mappings.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})

        # Add default columns if missing
        if "mfe" not in df.columns:
            df["mfe"] = 0.0
        if "mae" not in df.columns:
            df["mae"] = 0.0

        return df

    # Private helper methods

    def _calculate_mfe_single_trade(self, return_pct: float, direction: str) -> float:
        """Calculate MFE for a single trade"""
        try:
            return_pct = float(return_pct)
            if direction.lower() in ["long", "buy", "1"]:
                return round(max(return_pct, 0.0), 6)
            return round(abs(min(return_pct, 0.0)), 6)
        except:
            return 0.0

    def _calculate_mae_single_trade(self, return_pct: float, direction: str) -> float:
        """Calculate MAE for a single trade"""
        try:
            return_pct = float(return_pct)
            if direction.lower() in ["long", "buy", "1"]:
                return round(abs(min(return_pct, 0.0)), 6)
            return round(max(return_pct, 0.0), 6)
        except:
            return 0.0

    def _calculate_mfe_mae_from_single_return(
        self, return_pct: float, direction: str,
    ) -> tuple[float, float]:
        """Calculate MFE/MAE from a single return value"""
        try:
            if direction.lower() in ["long", "buy", "1"]:
                if return_pct >= 0:
                    return round(float(return_pct), 6), 0.0
                return 0.0, round(abs(float(return_pct)), 6)
            if return_pct <= 0:
                return round(abs(float(return_pct)), 6), 0.0
            return 0.0, round(float(return_pct), 6)
        except:
            return 0.0, 0.0

    def _add_default_mfe_mae(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add default MFE/MAE columns"""
        df = df.copy()
        if "mfe" not in df.columns:
            df["mfe"] = 0.0
        if "mae" not in df.columns:
            df["mae"] = 0.0
        return df


# Global instance for easy access throughout the codebase
_global_calculator = None


def get_mfe_mae_calculator(logger: logging.Logger | None = None) -> MFEMAECalculator:
    """
    Get the global MFE/MAE calculator instance

    Args:
        logger: Optional logger for the calculator

    Returns:
        Global MFE/MAE calculator instance
    """
    global _global_calculator
    if _global_calculator is None:
        _global_calculator = MFEMAECalculator(logger)
    return _global_calculator


# Convenience functions for direct use
def calculate_mfe_mae_from_trades(
    trades_df: pd.DataFrame,
    entry_price_col: str = "entry_price",
    exit_price_col: str = "exit_price",
    direction_col: str = "direction",
    return_col: str = "return_pct",
) -> pd.DataFrame:
    """Convenience function to calculate MFE/MAE from trades"""
    calculator = get_mfe_mae_calculator()
    return calculator.calculate_from_trades(
        trades_df, entry_price_col, exit_price_col, direction_col, return_col,
    )


def validate_mfe_mae_data(
    current_return: float, mfe: float, mae: float, direction: str = "Long",
) -> list[str]:
    """Convenience function to validate MFE/MAE data"""
    calculator = get_mfe_mae_calculator()
    return calculator.validate_mfe_mae(current_return, mfe, mae, direction)


def standardize_mfe_mae_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convenience function to standardize MFE/MAE column names"""
    calculator = get_mfe_mae_calculator()
    return calculator.standardize_column_names(df)
