"""
Kelly Criterion Calculator for Position Sizing

This module implements Excel B17-B21 Kelly calculations using manual trading journal inputs.
"""

import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


@dataclass
class ConfidenceMetrics:
    """Confidence metrics derived from trading journal statistics."""

    num_primary: int
    num_outliers: int
    total_trades: int
    confidence_ratio: float
    primary_percentage: float
    outlier_percentage: float


@dataclass
class KellyMetrics:
    """Complete Kelly Criterion calculation results."""

    kelly_criterion: float
    confidence_metrics: ConfidenceMetrics
    position_size_multiplier: float
    max_risk_per_position: float
    recommended_position_size: float


class KellyCriterionSizer:
    """Implements Excel B17-B21 Kelly calculations using manual trading journal inputs."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize Kelly Criterion calculator.

        Args:
            base_dir: Base directory path. If None, uses current working directory.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.data_dir = self.base_dir / "data" / "kelly"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.kelly_file = self.data_dir / "kelly_parameters.json"

        # Load parameters from file or use defaults
        self._load_parameters()

    def calculate_confidence_metrics(
        self, num_primary: int, num_outliers: int
    ) -> ConfidenceMetrics:
        """Calculate confidence metrics from trading journal statistics.

        Args:
            num_primary: Number of primary (non-outlier) trades
            num_outliers: Number of outlier trades

        Returns:
            ConfidenceMetrics object with calculated statistics
        """
        total_trades = num_primary + num_outliers

        if total_trades == 0:
            raise ValueError("Total trades cannot be zero")

        confidence_ratio = num_primary / total_trades if total_trades > 0 else 0.0
        primary_percentage = (
            (num_primary / total_trades) * 100 if total_trades > 0 else 0.0
        )
        outlier_percentage = (
            (num_outliers / total_trades) * 100 if total_trades > 0 else 0.0
        )

        return ConfidenceMetrics(
            num_primary=num_primary,
            num_outliers=num_outliers,
            total_trades=total_trades,
            confidence_ratio=confidence_ratio,
            primary_percentage=primary_percentage,
            outlier_percentage=outlier_percentage,
        )

    def calculate_kelly_position(
        self, num_primary: int, num_outliers: int, kelly_criterion: float
    ) -> float:
        """Calculate Kelly position size multiplier.

        Uses manually entered values: No. Primary, No. Outliers, Kelly Criterion from trading journal.

        Args:
            num_primary: Number of primary trades (Excel B17)
            num_outliers: Number of outlier trades (Excel B18)
            kelly_criterion: Kelly criterion value (Excel B19)

        Returns:
            Position size multiplier based on Kelly formula
        """
        confidence_metrics = self.calculate_confidence_metrics(
            num_primary, num_outliers
        )

        # Apply confidence adjustment to Kelly criterion
        # Higher confidence (more primary trades) allows closer to full Kelly
        # Lower confidence (more outliers) reduces position size
        confidence_adjusted_kelly = (
            kelly_criterion * confidence_metrics.confidence_ratio
        )

        return confidence_adjusted_kelly

    def get_max_risk_per_position(
        self, portfolio_value: float, risk_percentage: float = 0.118
    ) -> float:
        """Calculate maximum risk per position based on portfolio value.

        Excel equivalent: Portfolio value * risk percentage (11.8%)

        Args:
            portfolio_value: Total portfolio value (Excel B2)
            risk_percentage: Risk percentage (default 11.8% = 0.118)

        Returns:
            Maximum risk amount per position in dollars
        """
        return portfolio_value * risk_percentage

    def calculate_kelly_amount(
        self, net_worth: float, kelly_fraction: float = 0.236
    ) -> float:
        """Calculate Kelly Amount using the specific formula.

        Formula: Kelly Amount = Kelly Criterion × Kelly Fraction × Net Worth
        Where Kelly Fraction is 23.6% (0.236) by default

        Args:
            net_worth: Total net worth
            kelly_fraction: Kelly fraction multiplier (default 0.236 = 23.6%)

        Returns:
            Kelly Amount in dollars
        """
        return self._kelly_criterion * kelly_fraction * net_worth

    def calculate_recommended_position_size(
        self,
        num_primary: int,
        num_outliers: int,
        kelly_criterion: float,
        portfolio_value: float,
        risk_percentage: float = 0.118,
    ) -> float:
        """Calculate recommended position size in dollars.

        Combines Kelly criterion with portfolio risk limits.

        Args:
            num_primary: Number of primary trades
            num_outliers: Number of outlier trades
            kelly_criterion: Kelly criterion value
            portfolio_value: Total portfolio value
            risk_percentage: Portfolio risk percentage (default 11.8%)

        Returns:
            Recommended position size in dollars
        """
        kelly_multiplier = self.calculate_kelly_position(
            num_primary, num_outliers, kelly_criterion
        )
        max_risk = self.get_max_risk_per_position(portfolio_value, risk_percentage)

        # Apply Kelly multiplier to maximum risk
        recommended_size = max_risk * kelly_multiplier

        # Ensure we don't exceed maximum risk
        return min(recommended_size, max_risk)

    def get_complete_kelly_analysis(
        self,
        num_primary: int,
        num_outliers: int,
        kelly_criterion: float,
        portfolio_value: float,
        risk_percentage: float = 0.118,
    ) -> KellyMetrics:
        """Get complete Kelly Criterion analysis matching Excel B17-B21 calculations.

        Args:
            num_primary: Number of primary trades (Excel B17)
            num_outliers: Number of outlier trades (Excel B18)
            kelly_criterion: Kelly criterion value (Excel B19)
            portfolio_value: Total portfolio value (Excel B2)
            risk_percentage: Portfolio risk percentage (Excel 11.8%)

        Returns:
            Complete KellyMetrics analysis
        """
        confidence_metrics = self.calculate_confidence_metrics(
            num_primary, num_outliers
        )
        position_size_multiplier = self.calculate_kelly_position(
            num_primary, num_outliers, kelly_criterion
        )
        max_risk = self.get_max_risk_per_position(portfolio_value, risk_percentage)
        recommended_size = self.calculate_recommended_position_size(
            num_primary, num_outliers, kelly_criterion, portfolio_value, risk_percentage
        )

        return KellyMetrics(
            kelly_criterion=kelly_criterion,
            confidence_metrics=confidence_metrics,
            position_size_multiplier=position_size_multiplier,
            max_risk_per_position=max_risk,
            recommended_position_size=recommended_size,
        )

    def calculate_excel_b20_equivalent(
        self, num_primary: int, num_outliers: int
    ) -> float:
        """Calculate Excel B20 equivalent: Confidence ratio.

        Excel formula equivalent: =B17/(B17+B18)
        Where B17 is num_primary and B18 is num_outliers

        Args:
            num_primary: Number of primary trades (Excel B17)
            num_outliers: Number of outlier trades (Excel B18)

        Returns:
            Confidence ratio (B20)
        """
        return self.calculate_confidence_metrics(
            num_primary, num_outliers
        ).confidence_ratio

    def calculate_excel_b21_equivalent(
        self, num_primary: int, num_outliers: int, kelly_criterion: float
    ) -> float:
        """Calculate Excel B21 equivalent: Adjusted Kelly position size.

        Excel formula equivalent: =B19*B20
        Where B19 is kelly_criterion and B20 is confidence_ratio

        Args:
            num_primary: Number of primary trades
            num_outliers: Number of outlier trades
            kelly_criterion: Kelly criterion value

        Returns:
            Confidence-adjusted Kelly position size multiplier (B21)
        """
        return self.calculate_kelly_position(num_primary, num_outliers, kelly_criterion)

    def validate_kelly_inputs(
        self, num_primary: int, num_outliers: int, kelly_criterion: float
    ) -> Tuple[bool, str]:
        """Validate Kelly criterion inputs.

        Args:
            num_primary: Number of primary trades
            num_outliers: Number of outlier trades
            kelly_criterion: Kelly criterion value

        Returns:
            Tuple of (is_valid, validation_message)
        """
        errors = []

        if num_primary < 0:
            errors.append("Number of primary trades cannot be negative")

        if num_outliers < 0:
            errors.append("Number of outliers cannot be negative")

        if num_primary + num_outliers == 0:
            errors.append("Total trades cannot be zero")

        if kelly_criterion < 0:
            errors.append("Kelly criterion cannot be negative")

        if kelly_criterion > 1:
            errors.append("Kelly criterion should typically be <= 1 (100%)")

        # Warn about extreme values
        warnings = []
        total_trades = num_primary + num_outliers
        if total_trades > 0:
            outlier_ratio = num_outliers / total_trades
            if outlier_ratio > 0.5:
                warnings.append(f"High outlier ratio: {outlier_ratio:.1%}")

        if kelly_criterion > 0.5:
            warnings.append(f"High Kelly criterion: {kelly_criterion:.1%}")

        if errors:
            return False, "; ".join(errors)
        elif warnings:
            return True, f"Valid with warnings: {'; '.join(warnings)}"
        else:
            return True, "All inputs valid"

    def get_kelly_statistics_summary(
        self, num_primary: int, num_outliers: int, kelly_criterion: float
    ) -> Dict[str, Any]:
        """Get summary statistics for Kelly analysis.

        Args:
            num_primary: Number of primary trades
            num_outliers: Number of outlier trades
            kelly_criterion: Kelly criterion value

        Returns:
            Dictionary containing summary statistics
        """
        confidence_metrics = self.calculate_confidence_metrics(
            num_primary, num_outliers
        )
        position_multiplier = self.calculate_kelly_position(
            num_primary, num_outliers, kelly_criterion
        )

        return {
            "trading_journal_stats": {
                "primary_trades": num_primary,
                "outlier_trades": num_outliers,
                "total_trades": confidence_metrics.total_trades,
                "outlier_ratio": confidence_metrics.outlier_percentage / 100,
            },
            "kelly_analysis": {
                "raw_kelly_criterion": kelly_criterion,
                "confidence_ratio": confidence_metrics.confidence_ratio,
                "adjusted_kelly_multiplier": position_multiplier,
                "risk_reduction_factor": position_multiplier / kelly_criterion
                if kelly_criterion > 0
                else 0,
            },
            "excel_references": {
                "B17_primary_trades": num_primary,
                "B18_outlier_trades": num_outliers,
                "B19_kelly_criterion": kelly_criterion,
                "B20_confidence_ratio": confidence_metrics.confidence_ratio,
                "B21_adjusted_position_size": position_multiplier,
            },
        }

    def update_parameters(
        self, num_primary: int, num_outliers: int, kelly_criterion: float
    ) -> None:
        """Update Kelly criterion parameters from manual trading journal.

        Args:
            num_primary: Number of primary (non-outlier) trades
            num_outliers: Number of outlier trades
            kelly_criterion: Kelly criterion value from trading journal
        """
        # Validate inputs first
        is_valid, message = self.validate_kelly_inputs(
            num_primary, num_outliers, kelly_criterion
        )
        if not is_valid:
            raise ValueError(f"Invalid Kelly parameters: {message}")

        self._num_primary = num_primary
        self._num_outliers = num_outliers
        self._kelly_criterion = kelly_criterion

    def _load_parameters(self) -> None:
        """Load Kelly parameters from JSON file."""
        if not self.kelly_file.exists():
            # Set defaults
            self._num_primary = 10
            self._num_outliers = 2
            self._kelly_criterion = 0.0448
            self._save_parameters()
            return

        try:
            with open(self.kelly_file, "r") as f:
                data = json.load(f)
                self._num_primary = data.get("num_primary", 10)
                self._num_outliers = data.get("num_outliers", 2)
                self._kelly_criterion = data.get("kelly_criterion", 0.0448)
        except (json.JSONDecodeError, FileNotFoundError):
            # Fallback to defaults
            self._num_primary = 10
            self._num_outliers = 2
            self._kelly_criterion = 0.0448
            self._save_parameters()

    def _save_parameters(self) -> None:
        """Save Kelly parameters to JSON file."""
        data = {
            "num_primary": self._num_primary,
            "num_outliers": self._num_outliers,
            "kelly_criterion": self._kelly_criterion,
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.kelly_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_current_parameters(self) -> Dict[str, Any]:
        """Get current Kelly criterion parameters.

        Returns:
            Dictionary containing current parameters with keys:
            - num_primary: Number of primary trades
            - num_outliers: Number of outlier trades
            - kelly_criterion: Kelly criterion value
        """
        return {
            "num_primary": self._num_primary,
            "num_outliers": self._num_outliers,
            "kelly_criterion": self._kelly_criterion,
        }

    def update_kelly_criterion(self, kelly_criterion: float) -> None:
        """Update just the Kelly criterion value.

        Args:
            kelly_criterion: New Kelly criterion value (0-1)
        """
        if kelly_criterion < 0:
            raise ValueError("Kelly criterion cannot be negative")
        if kelly_criterion > 1:
            raise ValueError("Kelly criterion should be <= 1 (100%)")

        self._kelly_criterion = kelly_criterion
        self._save_parameters()

    def update_trade_counts(self, num_primary: int, num_outliers: int) -> None:
        """Update trade count parameters.

        Args:
            num_primary: Number of primary trades
            num_outliers: Number of outlier trades
        """
        if num_primary < 0:
            raise ValueError("Number of primary trades cannot be negative")
        if num_outliers < 0:
            raise ValueError("Number of outliers cannot be negative")
        if num_primary + num_outliers == 0:
            raise ValueError("Total trades cannot be zero")

        self._num_primary = num_primary
        self._num_outliers = num_outliers
        self._save_parameters()
