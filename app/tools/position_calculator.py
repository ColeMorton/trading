"""
Centralized Position Calculator

Single source of truth for all position-related calculations including P&L,
returns, exit efficiency, and trade quality assessments with standardized
precision and comprehensive validation.
"""

import logging
from datetime import datetime
from typing import Any

import pandas as pd


# Standardized precision constants across entire system
STANDARD_PNL_PRECISION = 2  # Currency values: $13.17
STANDARD_RETURN_PRECISION = 4  # Percentages: 0.3027
STANDARD_MFE_MAE_PRECISION = 6  # Risk metrics: 0.434553
STANDARD_RATIO_PRECISION = 4  # Ratios: 7.0223
STANDARD_DAYS_PRECISION = 0  # Whole numbers: 42
STANDARD_EFFICIENCY_PRECISION = 4  # Exit efficiency: 0.6966


class PositionCalculator:
    """
    Centralized calculator for all position-related calculations.

    Provides consistent, validated calculations with standardized rounding
    precision across the entire trading system.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize the position calculator."""
        self.logger = logger or logging.getLogger(__name__)

    def calculate_pnl_and_return(
        self,
        entry_price: float,
        exit_price: float,
        position_size: float,
        direction: str = "Long",
    ) -> tuple[float, float]:
        """
        Calculate P&L and return with standardized precision.

        Args:
            entry_price: Position entry price
            exit_price: Position exit price
            position_size: Position size (number of shares/units)
            direction: Position direction ('Long' or 'Short')

        Returns:
            Tuple of (pnl, return_pct) with standardized rounding
        """
        try:
            # Ensure inputs are numeric
            entry_price = float(entry_price)
            exit_price = float(exit_price)
            position_size = float(position_size)

            if direction.upper() == "LONG":
                pnl = (exit_price - entry_price) * position_size
                return_pct = (exit_price - entry_price) / entry_price
            else:  # SHORT
                pnl = (entry_price - exit_price) * position_size
                return_pct = (entry_price - exit_price) / entry_price

            # Apply standardized rounding
            pnl = round(pnl, STANDARD_PNL_PRECISION)
            return_pct = round(return_pct, STANDARD_RETURN_PRECISION)

            return pnl, return_pct

        except Exception as e:
            self.logger.exception(f"Error calculating P&L and return: {e}")
            return 0.0, 0.0

    def calculate_days_since_entry(
        self,
        entry_timestamp: str,
        current_date: datetime | None = None,
    ) -> int:
        """
        Calculate days since position entry.

        Args:
            entry_timestamp: Entry date/timestamp string
            current_date: Current date (defaults to now)

        Returns:
            Number of days since entry (whole number)
        """
        try:
            if current_date is None:
                current_date = datetime.now()

            entry_date = pd.to_datetime(entry_timestamp, format="mixed")
            days_since = (current_date - entry_date).days

            return int(round(days_since, STANDARD_DAYS_PRECISION))

        except Exception as e:
            self.logger.exception(f"Error calculating days since entry: {e}")
            return 0

    def calculate_exit_efficiency(
        self,
        final_return: float,
        mfe: float,
    ) -> float | None:
        """
        Calculate exit efficiency with standardized precision.

        Args:
            final_return: Final return percentage
            mfe: Maximum Favorable Excursion

        Returns:
            Exit efficiency ratio or None if MFE is zero
        """
        try:
            if mfe is None or mfe <= 0:
                return None

            efficiency = float(final_return) / float(mfe)
            return round(efficiency, STANDARD_EFFICIENCY_PRECISION)

        except Exception as e:
            self.logger.exception(f"Error calculating exit efficiency: {e}")
            return None

    def calculate_excursion_status(self, current_excursion: float) -> str:
        """
        Determine excursion status based on current performance.

        Args:
            current_excursion: Current excursion value

        Returns:
            Status string: 'Favorable', 'Adverse', or 'Neutral'
        """
        try:
            excursion = float(current_excursion)

            if excursion > 0:
                return "Favorable"
            if excursion < 0:
                return "Adverse"
            return "Neutral"

        except Exception as e:
            self.logger.exception(f"Error determining excursion status: {e}")
            return "Unknown"

    def assess_trade_quality(
        self,
        mfe: float,
        mae: float,
        final_return: float | None = None,
    ) -> str:
        """
        Assess trade quality based on MFE/MAE metrics.

        Args:
            mfe: Maximum Favorable Excursion
            mae: Maximum Adverse Excursion
            final_return: Final return (for additional assessment)

        Returns:
            Trade quality: 'Excellent', 'Good', 'Poor', or 'Poor Setup - High Risk, Low Reward'
        """
        try:
            if mfe is None or mae is None:
                return "Unknown"

            mfe = float(mfe)
            mae = float(mae)

            # Calculate risk/reward ratio
            risk_reward_ratio = mfe / mae if mae > 0 else float("inf")

            # Special case: Poor risk/reward setup
            if mfe < 0.02 and mae > 0.05:
                return "Poor Setup - High Risk, Low Reward"

            # Additional check for failed upside capture
            if final_return is not None:
                return_pct = float(final_return)
                if return_pct < 0 and abs(return_pct) > mfe:
                    return "Failed to Capture Upside"

            # Standard quality assessment
            if risk_reward_ratio >= 3.0 or risk_reward_ratio >= 2.0:
                return "Excellent"
            if risk_reward_ratio >= 1.5:
                return "Good"
            return "Poor"

        except Exception as e:
            self.logger.exception(f"Error assessing trade quality: {e}")
            return "Unknown"

    def calculate_mfe_mae_ratio(self, mfe: float, mae: float) -> float:
        """
        Calculate MFE/MAE ratio with standardized precision.

        Args:
            mfe: Maximum Favorable Excursion
            mae: Maximum Adverse Excursion

        Returns:
            MFE/MAE ratio with standardized rounding
        """
        try:
            if mae is None or mae <= 0:
                return float("inf") if mfe and mfe > 0 else 0.0

            ratio = float(mfe) / float(mae)
            return round(ratio, STANDARD_RATIO_PRECISION)

        except Exception as e:
            self.logger.exception(f"Error calculating MFE/MAE ratio: {e}")
            return 0.0

    def validate_calculation_consistency(
        self,
        position_data: dict[str, Any],
        tolerance_pnl: float = 0.01,
        tolerance_return: float = 0.0001,
    ) -> dict[str, Any]:
        """
        Validate all calculations in a position for consistency.

        Args:
            position_data: Dictionary containing position data
            tolerance_pnl: Tolerance for P&L differences
            tolerance_return: Tolerance for return differences

        Returns:
            Validation results dictionary
        """
        try:
            results = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "corrected_values": {},
            }

            # Extract required fields
            entry_price = position_data.get("Avg_Entry_Price")
            exit_price = position_data.get("Avg_Exit_Price")
            position_size = position_data.get("Position_Size", 1.0)
            direction = position_data.get("Direction", "Long")
            reported_pnl = position_data.get("PnL")
            reported_return = position_data.get("Return")
            mfe = position_data.get("Max_Favourable_Excursion")
            mae = position_data.get("Max_Adverse_Excursion")

            # Skip if missing critical data
            if any(
                x is None
                for x in [entry_price, exit_price, reported_pnl, reported_return]
            ):
                results["warnings"].append("Missing critical data for validation")
                return results

            # Recalculate P&L and Return
            expected_pnl, expected_return = self.calculate_pnl_and_return(
                entry_price,
                exit_price,
                position_size,
                direction,
            )

            # Check P&L consistency
            pnl_diff = abs(float(reported_pnl) - expected_pnl)
            if pnl_diff > tolerance_pnl:
                results["valid"] = False
                results["errors"].append(
                    {
                        "field": "PnL",
                        "expected": expected_pnl,
                        "actual": reported_pnl,
                        "difference": pnl_diff,
                    },
                )
                results["corrected_values"]["PnL"] = expected_pnl

            # Check Return consistency
            return_diff = abs(float(reported_return) - expected_return)
            if return_diff > tolerance_return:
                results["valid"] = False
                results["errors"].append(
                    {
                        "field": "Return",
                        "expected": expected_return,
                        "actual": reported_return,
                        "difference": return_diff,
                    },
                )
                results["corrected_values"]["Return"] = expected_return

            # Validate MFE/MAE ratio if present
            if mfe is not None and mae is not None:
                expected_ratio = self.calculate_mfe_mae_ratio(mfe, mae)
                reported_ratio = position_data.get("MFE_MAE_Ratio")

                if reported_ratio is not None:
                    ratio_diff = abs(float(reported_ratio) - expected_ratio)
                    if ratio_diff > 0.001:  # Small tolerance for ratios
                        results["warnings"].append(
                            {
                                "field": "MFE_MAE_Ratio",
                                "expected": expected_ratio,
                                "actual": reported_ratio,
                                "difference": ratio_diff,
                            },
                        )
                        results["corrected_values"]["MFE_MAE_Ratio"] = expected_ratio

            # Validate Exit Efficiency if present
            if reported_return is not None and mfe is not None:
                expected_efficiency = self.calculate_exit_efficiency(
                    expected_return,
                    mfe,
                )
                reported_efficiency = position_data.get("Exit_Efficiency_Fixed")

                if expected_efficiency is not None and reported_efficiency is not None:
                    eff_diff = abs(float(reported_efficiency) - expected_efficiency)
                    if eff_diff > 0.001:
                        results["warnings"].append(
                            {
                                "field": "Exit_Efficiency_Fixed",
                                "expected": expected_efficiency,
                                "actual": reported_efficiency,
                                "difference": eff_diff,
                            },
                        )
                        results["corrected_values"]["Exit_Efficiency_Fixed"] = (
                            expected_efficiency
                        )

            return results

        except Exception as e:
            self.logger.exception(f"Error in validation: {e}")
            return {
                "valid": False,
                "errors": [f"Validation error: {e!s}"],
                "warnings": [],
                "corrected_values": {},
            }

    def apply_standard_rounding(self, values_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Apply standardized rounding to a dictionary of values.

        Args:
            values_dict: Dictionary of field names and values

        Returns:
            Dictionary with standardized rounding applied
        """
        try:
            rounded_values = {}

            # Define field-specific precision mapping
            precision_mapping = {
                "PnL": STANDARD_PNL_PRECISION,
                "Return": STANDARD_RETURN_PRECISION,
                "Current_Unrealized_PnL": STANDARD_RETURN_PRECISION,
                "Max_Favourable_Excursion": STANDARD_MFE_MAE_PRECISION,
                "Max_Adverse_Excursion": STANDARD_MFE_MAE_PRECISION,
                "MFE_MAE_Ratio": STANDARD_RATIO_PRECISION,
                "Exit_Efficiency_Fixed": STANDARD_EFFICIENCY_PRECISION,
                "Days_Since_Entry": STANDARD_DAYS_PRECISION,
            }

            for field, value in values_dict.items():
                if field in precision_mapping and value is not None:
                    try:
                        if value == float("inf"):
                            rounded_values[field] = float("inf")
                        else:
                            precision = precision_mapping[field]
                            rounded_values[field] = round(float(value), precision)
                    except (ValueError, TypeError):
                        rounded_values[field] = value
                else:
                    rounded_values[field] = value

            return rounded_values

        except Exception as e:
            self.logger.exception(f"Error applying standard rounding: {e}")
            return values_dict

    def comprehensive_position_refresh(
        self,
        position_data: dict[str, Any],
        mfe: float | None = None,
        mae: float | None = None,
        current_excursion: float | None = None,
    ) -> dict[str, Any]:
        """
        Perform comprehensive refresh of all calculated fields for a position.

        Args:
            position_data: Current position data dictionary
            mfe: Updated MFE value (if available)
            mae: Updated MAE value (if available)
            current_excursion: Updated current excursion (if available)

        Returns:
            Dictionary with refreshed and validated position data
        """
        try:
            refreshed_data = position_data.copy()
            changes_made = []

            # 1. Recalculate P&L and Return
            entry_price = position_data.get("Avg_Entry_Price")
            exit_price = position_data.get("Avg_Exit_Price")
            position_size = position_data.get("Position_Size", 1.0)
            direction = position_data.get("Direction", "Long")

            if entry_price is not None and exit_price is not None:
                new_pnl, new_return = self.calculate_pnl_and_return(
                    entry_price,
                    exit_price,
                    position_size,
                    direction,
                )

                if refreshed_data.get("PnL") != new_pnl:
                    changes_made.append(f'PnL: {refreshed_data.get("PnL")} → {new_pnl}')
                    refreshed_data["PnL"] = new_pnl

                if refreshed_data.get("Return") != new_return:
                    changes_made.append(
                        f'Return: {refreshed_data.get("Return")} → {new_return}',
                    )
                    refreshed_data["Return"] = new_return

                # Update Current_Unrealized_PnL for consistency
                refreshed_data["Current_Unrealized_PnL"] = new_return

            # 2. Update MFE/MAE if provided
            if mfe is not None:
                mfe_rounded = round(mfe, STANDARD_MFE_MAE_PRECISION)
                if refreshed_data.get("Max_Favourable_Excursion") != mfe_rounded:
                    changes_made.append(
                        f'MFE: {refreshed_data.get("Max_Favourable_Excursion")} → {mfe_rounded}',
                    )
                    refreshed_data["Max_Favourable_Excursion"] = mfe_rounded

            if mae is not None:
                mae_rounded = round(mae, STANDARD_MFE_MAE_PRECISION)
                if refreshed_data.get("Max_Adverse_Excursion") != mae_rounded:
                    changes_made.append(
                        f'MAE: {refreshed_data.get("Max_Adverse_Excursion")} → {mae_rounded}',
                    )
                    refreshed_data["Max_Adverse_Excursion"] = mae_rounded

            # 3. Recalculate MFE/MAE Ratio
            current_mfe = refreshed_data.get("Max_Favourable_Excursion")
            current_mae = refreshed_data.get("Max_Adverse_Excursion")

            if current_mfe is not None and current_mae is not None:
                new_ratio = self.calculate_mfe_mae_ratio(current_mfe, current_mae)
                if refreshed_data.get("MFE_MAE_Ratio") != new_ratio:
                    changes_made.append(
                        f'MFE/MAE Ratio: {refreshed_data.get("MFE_MAE_Ratio")} → {new_ratio}',
                    )
                    refreshed_data["MFE_MAE_Ratio"] = new_ratio

            # 4. Recalculate Exit Efficiency
            current_return = refreshed_data.get("Return")
            if current_return is not None and current_mfe is not None:
                new_efficiency = self.calculate_exit_efficiency(
                    current_return,
                    current_mfe,
                )
                if new_efficiency is not None:
                    if refreshed_data.get("Exit_Efficiency_Fixed") != new_efficiency:
                        changes_made.append(
                            f'Exit Efficiency: {refreshed_data.get("Exit_Efficiency_Fixed")} → {new_efficiency}',
                        )
                        refreshed_data["Exit_Efficiency_Fixed"] = new_efficiency

            # 5. Update Days Since Entry
            entry_timestamp = position_data.get("Entry_Timestamp")
            if entry_timestamp is not None:
                new_days = self.calculate_days_since_entry(entry_timestamp)
                if refreshed_data.get("Days_Since_Entry") != new_days:
                    changes_made.append(
                        f'Days Since Entry: {refreshed_data.get("Days_Since_Entry")} → {new_days}',
                    )
                    refreshed_data["Days_Since_Entry"] = new_days

            # 6. Update Excursion Status
            if current_excursion is not None:
                new_status = self.calculate_excursion_status(current_excursion)
                if refreshed_data.get("Current_Excursion_Status") != new_status:
                    changes_made.append(
                        f'Excursion Status: {refreshed_data.get("Current_Excursion_Status")} → {new_status}',
                    )
                    refreshed_data["Current_Excursion_Status"] = new_status

            # 7. Reassess Trade Quality
            if current_mfe is not None and current_mae is not None:
                new_quality = self.assess_trade_quality(
                    current_mfe,
                    current_mae,
                    current_return,
                )
                if refreshed_data.get("Trade_Quality") != new_quality:
                    changes_made.append(
                        f'Trade Quality: {refreshed_data.get("Trade_Quality")} → {new_quality}',
                    )
                    refreshed_data["Trade_Quality"] = new_quality

            # 8. Apply standard rounding to all values
            refreshed_data = self.apply_standard_rounding(refreshed_data)

            return {
                "data": refreshed_data,
                "changes": changes_made,
                "validation": self.validate_calculation_consistency(refreshed_data),
            }

        except Exception as e:
            self.logger.exception(f"Error in comprehensive position refresh: {e}")
            return {
                "data": position_data,
                "changes": [],
                "validation": {"valid": False, "errors": [str(e)]},
            }


# Global instance for easy access
_global_calculator = None


def get_position_calculator(
    logger: logging.Logger | None = None,
) -> PositionCalculator:
    """
    Get the global position calculator instance.

    Args:
        logger: Optional logger for the calculator

    Returns:
        Global position calculator instance
    """
    global _global_calculator
    if _global_calculator is None:
        _global_calculator = PositionCalculator(logger)
    return _global_calculator


# Convenience functions for direct use
def calculate_position_pnl_return(
    entry_price: float,
    exit_price: float,
    position_size: float = 1.0,
    direction: str = "Long",
) -> tuple[float, float]:
    """Convenience function to calculate P&L and return."""
    calculator = get_position_calculator()
    return calculator.calculate_pnl_and_return(
        entry_price,
        exit_price,
        position_size,
        direction,
    )


def validate_position_data(position_data: dict[str, Any]) -> dict[str, Any]:
    """Convenience function to validate position data."""
    calculator = get_position_calculator()
    return calculator.validate_calculation_consistency(position_data)


def refresh_position_calculations(
    position_data: dict[str, Any],
    mfe: float | None = None,
    mae: float | None = None,
    current_excursion: float | None = None,
) -> dict[str, Any]:
    """Convenience function to refresh all position calculations."""
    calculator = get_position_calculator()
    return calculator.comprehensive_position_refresh(
        position_data,
        mfe,
        mae,
        current_excursion,
    )
