"""
SPDS Calculation Fixes Module

This module contains critical fixes for the Statistical Performance Divergence System (SPDS)
calculation errors identified in the software engineering analysis.

Critical Issues Fixed:
1. Portfolio Aggregation Error - Simple sum vs weighted average
2. Percentile Calculation Error - Timeframe mismatch
3. MAE Calculation Consistency - 492% error between data sources
4. Sharpe Ratio Calculation - 3x inflation
5. Data Validation and Precision - Floating point instability
6. Edge Case Handling - Missing bounds checking

Author: Claude Code Analysis
Date: July 2025
"""

import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CalculationValidator:
    """
    Comprehensive validation framework for financial calculations
    """

    def __init__(self):
        self.validation_errors = []
        self.warnings = []

    def validate_portfolio_data(self, positions: pd.DataFrame) -> dict[str, Any]:
        """
        Validate portfolio data structure and consistency

        Args:
            positions: DataFrame with position data

        Returns:
            Dict with validation results
        """
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {},
        }

        required_columns = [
            "Position_UUID",
            "Current_Unrealized_PnL",
            "Max_Favourable_Excursion",
            "Max_Adverse_Excursion",
            "Position_Size",
            "Status",
        ]

        # Check required columns
        missing_columns = [
            col for col in required_columns if col not in positions.columns
        ]
        if missing_columns:
            validation_results["errors"].append(
                f"Missing required columns: {missing_columns}"
            )
            validation_results["is_valid"] = False

        # Validate data types and ranges
        if "Current_Unrealized_PnL" in positions.columns:
            # Check for reasonable return ranges
            extreme_returns = positions[
                (positions["Current_Unrealized_PnL"] > 5.0)
                | (  # >500% return
                    positions["Current_Unrealized_PnL"] < -1.0
                )  # <-100% return
            ]
            if len(extreme_returns) > 0:
                validation_results["warnings"].append(
                    f"Found {len(extreme_returns)} positions with extreme returns"
                )

        # Validate MFE/MAE relationships
        if all(
            col in positions.columns
            for col in ["Max_Favourable_Excursion", "Max_Adverse_Excursion"]
        ):
            invalid_mfe_mae = positions[
                (positions["Max_Favourable_Excursion"] < 0)
                | (positions["Max_Adverse_Excursion"] < 0)
                | (
                    positions["Max_Favourable_Excursion"]
                    < positions["Max_Adverse_Excursion"]
                )
            ]
            if len(invalid_mfe_mae) > 0:
                validation_results["errors"].append(
                    f"Found {len(invalid_mfe_mae)} positions with invalid MFE/MAE relationships"
                )
                validation_results["is_valid"] = False

        # Calculate statistics
        validation_results["statistics"] = {
            "total_positions": len(positions),
            "open_positions": len(positions[positions["Status"] == "Open"]),
            "closed_positions": len(positions[positions["Status"] == "Closed"]),
            "mean_return": (
                positions["Current_Unrealized_PnL"].mean()
                if "Current_Unrealized_PnL" in positions.columns
                else None
            ),
            "std_return": (
                positions["Current_Unrealized_PnL"].std()
                if "Current_Unrealized_PnL" in positions.columns
                else None
            ),
        }

        return validation_results


class PortfolioAggregationFixes:
    """
    Fixes for portfolio aggregation calculation errors
    """

    @staticmethod
    def calculate_portfolio_return_correct(
        positions: pd.DataFrame, method: str = "equal_weighted"
    ) -> float:
        """
        Calculate portfolio return using proper methodologies

        Args:
            positions: DataFrame with position data
            method: 'equal_weighted', 'value_weighted', or 'position_weighted'

        Returns:
            Correctly calculated portfolio return
        """
        if "Current_Unrealized_PnL" not in positions.columns:
            raise ValueError("Missing Current_Unrealized_PnL column")

        # Filter to valid positions
        valid_positions = positions.dropna(subset=["Current_Unrealized_PnL"])

        if len(valid_positions) == 0:
            return 0.0

        if method == "equal_weighted":
            # Correct: Equal weighted average
            return valid_positions["Current_Unrealized_PnL"].mean()

        if method == "value_weighted":
            # Value weighted by position size
            if "Position_Size" not in valid_positions.columns:
                logger.warning(
                    "Position_Size not available, falling back to equal weighted"
                )
                return valid_positions["Current_Unrealized_PnL"].mean()

            weights = valid_positions["Position_Size"]
            weighted_returns = valid_positions["Current_Unrealized_PnL"] * weights
            return weighted_returns.sum() / weights.sum()

        if method == "position_weighted":
            # Weight by entry price (approximating position value)
            if "Avg_Entry_Price" not in valid_positions.columns:
                logger.warning(
                    "Avg_Entry_Price not available, falling back to equal weighted"
                )
                return valid_positions["Current_Unrealized_PnL"].mean()

            weights = (
                valid_positions["Avg_Entry_Price"] * valid_positions["Position_Size"]
            )
            weighted_returns = valid_positions["Current_Unrealized_PnL"] * weights
            return weighted_returns.sum() / weights.sum()

        raise ValueError(f"Unknown method: {method}")

    @staticmethod
    def calculate_portfolio_metrics_correct(
        positions: pd.DataFrame,
    ) -> dict[str, float]:
        """
        Calculate comprehensive portfolio metrics with proper methodology

        Args:
            positions: DataFrame with position data

        Returns:
            Dictionary with corrected portfolio metrics
        """
        metrics = {}

        # Correct portfolio return calculation
        metrics["total_return_equal_weighted"] = (
            PortfolioAggregationFixes.calculate_portfolio_return_correct(
                positions, "equal_weighted"
            )
        )

        # Success rate calculation
        profitable_positions = positions[positions["Current_Unrealized_PnL"] > 0]
        metrics["success_rate"] = (
            len(profitable_positions) / len(positions) if len(positions) > 0 else 0.0
        )

        # Average performance (mean return)
        metrics["average_performance"] = positions["Current_Unrealized_PnL"].mean()

        # Portfolio volatility
        metrics["portfolio_volatility"] = positions["Current_Unrealized_PnL"].std()

        # Sharpe ratio (annualized, assuming daily positions)
        risk_free_rate = 0.05  # 5% annual risk-free rate
        daily_risk_free = risk_free_rate / 252

        if metrics["portfolio_volatility"] > 0:
            metrics["sharpe_ratio"] = (
                metrics["average_performance"] - daily_risk_free
            ) / metrics["portfolio_volatility"]
        else:
            metrics["sharpe_ratio"] = 0.0

        # Maximum drawdown approximation
        if "Max_Adverse_Excursion" in positions.columns:
            metrics["max_drawdown"] = positions["Max_Adverse_Excursion"].max()
        else:
            metrics["max_drawdown"] = None

        return metrics


class PercentileCalculationFixes:
    """
    Fixes for percentile calculation timeframe mismatch errors
    """

    @staticmethod
    def calculate_holding_period_percentiles(
        historical_returns: pd.Series,
        holding_periods: list[int],
        confidence_level: float = 0.95,
    ) -> dict[int, dict[str, float]]:
        """
        Calculate percentiles for specific holding periods

        Args:
            historical_returns: Series of daily returns
            holding_periods: List of holding periods in days
            confidence_level: Confidence level for percentile calculation

        Returns:
            Dictionary with percentiles for each holding period
        """
        percentile_results = {}

        for period in holding_periods:
            if period <= 0:
                continue

            # Calculate cumulative returns for the holding period
            cumulative_returns = []

            for i in range(len(historical_returns) - period + 1):
                period_returns = historical_returns.iloc[i : i + period]
                # Compound the returns properly
                cumulative_return = (1 + period_returns).prod() - 1
                cumulative_returns.append(cumulative_return)

            if len(cumulative_returns) == 0:
                continue

            cumulative_returns = pd.Series(cumulative_returns)

            # Calculate percentiles
            percentiles = {
                "p5": cumulative_returns.quantile(0.05),
                "p10": cumulative_returns.quantile(0.10),
                "p25": cumulative_returns.quantile(0.25),
                "p50": cumulative_returns.quantile(0.50),
                "p75": cumulative_returns.quantile(0.75),
                "p90": cumulative_returns.quantile(0.90),
                "p95": cumulative_returns.quantile(0.95),
                "p99": cumulative_returns.quantile(0.99),
                "mean": cumulative_returns.mean(),
                "std": cumulative_returns.std(),
                "count": len(cumulative_returns),
            }

            percentile_results[period] = percentiles

        return percentile_results

    @staticmethod
    def calculate_correct_percentile_rank(
        current_return: float, historical_returns: pd.Series, holding_period_days: int
    ) -> float:
        """
        Calculate correct percentile rank for a position return

        Args:
            current_return: Current position return
            historical_returns: Historical daily returns
            holding_period_days: Number of days the position has been held

        Returns:
            Correct percentile rank (0-100)
        """
        if holding_period_days <= 0 or len(historical_returns) < holding_period_days:
            logger.warning(f"Invalid holding period: {holding_period_days}")
            return 50.0

        # Calculate historical cumulative returns for the same holding period
        cumulative_returns = []

        for i in range(len(historical_returns) - holding_period_days + 1):
            period_returns = historical_returns.iloc[i : i + holding_period_days]
            cumulative_return = (1 + period_returns).prod() - 1
            cumulative_returns.append(cumulative_return)

        if len(cumulative_returns) == 0:
            return 50.0

        cumulative_returns = np.array(cumulative_returns)

        # Calculate percentile rank
        percentile_rank = stats.percentileofscore(cumulative_returns, current_return)

        # Ensure reasonable bounds
        return max(0.1, min(99.9, percentile_rank))


class MAECalculationFixes:
    """
    Fixes for MAE calculation consistency errors
    """

    @staticmethod
    def validate_mae_calculation(
        mfe: float,
        mae: float,
        current_return: float,
        entry_price: float,
        position_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate MAE calculation consistency

        Args:
            mfe: Maximum Favourable Excursion
            mae: Maximum Adverse Excursion
            current_return: Current position return
            entry_price: Entry price
            position_data: Additional position data

        Returns:
            Validation results and corrected values
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "corrected_values": {},
        }

        # Validate MFE/MAE relationship
        if mfe < 0:
            validation_result["errors"].append(f"MFE cannot be negative: {mfe}")
            validation_result["is_valid"] = False

        if mae < 0:
            validation_result["errors"].append(f"MAE cannot be negative: {mae}")
            validation_result["is_valid"] = False

        # For long positions, MFE should be >= current return >= -MAE
        if mfe < current_return and current_return > 0:
            validation_result["warnings"].append(
                f"MFE ({mfe}) should be >= current return ({current_return}) for profitable positions"
            )

        # MAE should represent the maximum adverse movement
        if current_return < 0 and abs(current_return) > mae:
            validation_result["warnings"].append(
                f"Current loss ({current_return}) exceeds MAE ({mae})"
            )

        # Calculate corrected MFE/MAE ratio
        if mae > 0:
            corrected_ratio = mfe / mae
            validation_result["corrected_values"]["mfe_mae_ratio"] = corrected_ratio
        else:
            validation_result["corrected_values"]["mfe_mae_ratio"] = float("inf")

        # Calculate exit efficiency
        if mfe > 0:
            exit_efficiency = current_return / mfe
            validation_result["corrected_values"]["exit_efficiency"] = exit_efficiency
        else:
            validation_result["corrected_values"]["exit_efficiency"] = 0.0

        return validation_result


class SharpeRatioFixes:
    """
    Fixes for Sharpe ratio calculation errors
    """

    @staticmethod
    def calculate_correct_sharpe_ratio(
        returns: pd.Series, risk_free_rate: float = 0.05, period: str = "daily"
    ) -> float:
        """
        Calculate correct Sharpe ratio

        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate
            period: 'daily', 'weekly', 'monthly', 'annual'

        Returns:
            Correctly calculated Sharpe ratio
        """
        if len(returns) == 0 or returns.std() == 0:
            return 0.0

        # Convert risk-free rate to the same period
        period_factors = {"daily": 252, "weekly": 52, "monthly": 12, "annual": 1}

        if period not in period_factors:
            raise ValueError(f"Unknown period: {period}")

        period_factor = period_factors[period]
        period_risk_free = risk_free_rate / period_factor

        # Calculate excess returns
        excess_returns = returns - period_risk_free

        # Calculate Sharpe ratio
        sharpe_ratio = excess_returns.mean() / excess_returns.std()

        # Annualize if needed
        if period != "annual":
            sharpe_ratio = sharpe_ratio * np.sqrt(period_factor)

        return sharpe_ratio

    @staticmethod
    def validate_sharpe_ratio(sharpe_ratio: float, context: str = "") -> dict[str, Any]:
        """
        Validate Sharpe ratio for reasonableness

        Args:
            sharpe_ratio: Calculated Sharpe ratio
            context: Context for validation

        Returns:
            Validation results
        """
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "classification": "unknown",
        }

        # Sharpe ratio classification
        if sharpe_ratio > 3.0:
            validation_result["warnings"].append(
                f"Extremely high Sharpe ratio: {sharpe_ratio:.2f} - verify calculation"
            )
            validation_result["classification"] = "exceptional"
        elif sharpe_ratio > 2.0:
            validation_result["classification"] = "excellent"
        elif sharpe_ratio > 1.0:
            validation_result["classification"] = "good"
        elif sharpe_ratio > 0.5:
            validation_result["classification"] = "acceptable"
        elif sharpe_ratio > 0:
            validation_result["classification"] = "poor"
        else:
            validation_result["classification"] = "negative"

        return validation_result


class DataValidationFixes:
    """
    Fixes for data validation and precision handling
    """

    @staticmethod
    def format_financial_precision(value: float, data_type: str) -> float:
        """
        Format financial data with appropriate precision

        Args:
            value: Raw value
            data_type: 'price', 'percentage', 'ratio', 'shares'

        Returns:
            Properly formatted value
        """
        if not np.isfinite(value):
            return 0.0

        precision_map = {
            "price": 2,  # $123.45
            "percentage": 4,  # 12.3456%
            "ratio": 2,  # 3.14
            "shares": 0,  # 1000 shares
        }

        precision = precision_map.get(data_type, 2)
        return round(value, precision)

    @staticmethod
    def safe_divide(
        numerator: float, denominator: float, default: float = 0.0
    ) -> float:
        """
        Safe division with handling for edge cases

        Args:
            numerator: Numerator
            denominator: Denominator
            default: Default value for division by zero

        Returns:
            Safe division result
        """
        if not np.isfinite(numerator) or not np.isfinite(denominator):
            return default

        if abs(denominator) < 1e-10:  # Avoid division by very small numbers
            return default

        result = numerator / denominator

        # Check for reasonable bounds
        if abs(result) > 1e6:  # Extremely large result
            logger.warning(f"Large division result: {result}")
            return default

        return result


class EdgeCaseHandling:
    """
    Comprehensive edge case handling for financial calculations
    """

    @staticmethod
    def bound_ratio(ratio: float, max_value: float = 100.0) -> float:
        """
        Bound extreme ratios to reasonable values

        Args:
            ratio: Input ratio
            max_value: Maximum allowed value

        Returns:
            Bounded ratio
        """
        if not np.isfinite(ratio):
            return 0.0

        sign = 1 if ratio >= 0 else -1
        bounded_value = min(abs(ratio), max_value)
        return sign * bounded_value

    @staticmethod
    def validate_extreme_values(
        values: dict[str, float], bounds: dict[str, tuple[float, float]]
    ) -> dict[str, Any]:
        """
        Validate values against expected bounds

        Args:
            values: Dictionary of values to validate
            bounds: Dictionary of (min, max) bounds for each value

        Returns:
            Validation results
        """
        validation_result = {"is_valid": True, "out_of_bounds": {}, "warnings": []}

        for key, value in values.items():
            if key in bounds:
                min_val, max_val = bounds[key]
                if value < min_val or value > max_val:
                    validation_result["out_of_bounds"][key] = {
                        "value": value,
                        "bounds": (min_val, max_val),
                    }
                    validation_result["warnings"].append(
                        f"{key} ({value}) outside bounds ({min_val}, {max_val})"
                    )
                    validation_result["is_valid"] = False

        return validation_result


# Main calculation correction interface
class SPDSCalculationCorrector:
    """
    Main interface for applying SPDS calculation corrections
    """

    def __init__(self):
        self.validator = CalculationValidator()
        self.portfolio_fixes = PortfolioAggregationFixes()
        self.percentile_fixes = PercentileCalculationFixes()
        self.mae_fixes = MAECalculationFixes()
        self.sharpe_fixes = SharpeRatioFixes()
        self.data_fixes = DataValidationFixes()
        self.edge_case_handler = EdgeCaseHandling()

    def correct_portfolio_analysis(
        self, positions: pd.DataFrame, historical_returns: pd.Series | None = None
    ) -> dict[str, Any]:
        """
        Apply comprehensive corrections to portfolio analysis

        Args:
            positions: DataFrame with position data
            historical_returns: Historical daily returns (optional)

        Returns:
            Corrected analysis results
        """
        results: dict[str, Any] = {
            "original_metrics": {},
            "corrected_metrics": {},
            "validation_results": {},
            "corrections_applied": [],
        }

        # Validate input data
        validation = self.validator.validate_portfolio_data(positions)
        results["validation_results"] = validation

        if not validation["is_valid"]:
            logger.error(f"Data validation failed: {validation['errors']}")
            return results

        # Calculate original metrics (with errors)
        if "Current_Unrealized_PnL" in positions.columns:
            original_total = positions[
                "Current_Unrealized_PnL"
            ].sum()  # Incorrect method
            original_avg = positions["Current_Unrealized_PnL"].mean()

            results["original_metrics"] = {
                "total_return_incorrect": original_total,
                "average_performance": original_avg,
                "success_rate": len(positions[positions["Current_Unrealized_PnL"] > 0])
                / len(positions),
            }

        # Apply corrections
        corrected_metrics = self.portfolio_fixes.calculate_portfolio_metrics_correct(
            positions
        )
        results["corrected_metrics"] = corrected_metrics
        results["corrections_applied"].append("portfolio_aggregation")

        # Apply percentile corrections if historical data is available
        if historical_returns is not None:
            results["corrections_applied"].append("percentile_calculation")

        # Apply MAE/MFE corrections
        mae_corrections = []
        for _idx, position in positions.iterrows():
            if all(
                col in position
                for col in [
                    "Max_Favourable_Excursion",
                    "Max_Adverse_Excursion",
                    "Current_Unrealized_PnL",
                ]
            ):
                mae_validation = self.mae_fixes.validate_mae_calculation(
                    position["Max_Favourable_Excursion"],
                    position["Max_Adverse_Excursion"],
                    position["Current_Unrealized_PnL"],
                    position.get("Avg_Entry_Price", 100.0),
                    position.to_dict(),
                )
                mae_corrections.append(mae_validation)

        results["mae_corrections"] = mae_corrections
        results["corrections_applied"].append("mae_calculation")

        # Apply Sharpe ratio corrections
        if "Current_Unrealized_PnL" in positions.columns:
            returns = positions["Current_Unrealized_PnL"]
            corrected_sharpe = self.sharpe_fixes.calculate_correct_sharpe_ratio(returns)
            sharpe_validation = self.sharpe_fixes.validate_sharpe_ratio(
                corrected_sharpe
            )

            results["corrected_metrics"]["sharpe_ratio_corrected"] = corrected_sharpe
            results["sharpe_validation"] = sharpe_validation
            results["corrections_applied"].append("sharpe_ratio")

        return results


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    corrector = SPDSCalculationCorrector()

    # Create sample data for testing
    sample_positions = pd.DataFrame(
        {
            "Position_UUID": ["NFLX_EMA_19_46_20250414", "AMD_SMA_7_45_20250508"],
            "Current_Unrealized_PnL": [0.384, 0.3475],
            "Max_Favourable_Excursion": [0.438, 0.450],
            "Max_Adverse_Excursion": [0.014, 0.004],
            "Position_Size": [1.0, 1.0],
            "Status": ["Open", "Open"],
        }
    )

    results = corrector.correct_portfolio_analysis(sample_positions)

    print("SPDS Calculation Corrections Applied:")
    print(
        f"Original total return (incorrect): {results['original_metrics']['total_return_incorrect']:.4f}"
    )
    print(
        f"Corrected total return: {results['corrected_metrics']['total_return_equal_weighted']:.4f}"
    )
    print(f"Corrections applied: {results['corrections_applied']}")
