"""
Strategies Count Integration for Position Sizing

This module integrates Total Strategies count from @json/concurrency/portfolio.json
as specified in Phase 2 of the position sizing migration plan.
"""

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any


@dataclass
class StrategiesCountData:
    """Strategies count data from concurrency analysis."""

    total_strategies_analyzed: int
    stable_strategies_count: int
    stable_strategies_percentage: float
    average_stability_score: float
    max_concurrent_strategies: int
    avg_concurrent_strategies: float
    last_updated: datetime
    data_source: str = "portfolio.json"


class StrategiesCountIntegration:
    """Service for sourcing Total Strategies count from concurrency portfolio analysis."""

    def __init__(self, base_dir: str | None = None):
        """Initialize the strategies count integration.

        Args:
            base_dir: Base directory path. If None, uses current working directory.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.concurrency_dir = self.base_dir / "json" / "concurrency"
        self.portfolio_file = self.concurrency_dir / "portfolio.json"

    def _load_portfolio_json(self) -> dict[str, Any]:
        """Load portfolio concurrency analysis JSON file.

        Returns:
            Parsed JSON data from portfolio.json

        Raises:
            FileNotFoundError: If portfolio.json doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        if not self.portfolio_file.exists():
            msg = f"Portfolio file not found: {self.portfolio_file}"
            raise FileNotFoundError(msg)

        try:
            with open(self.portfolio_file) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in portfolio file: {self.portfolio_file}"
            raise json.JSONDecodeError(
                msg,
                e.doc,
                e.pos,
            )

    def get_total_strategies_count(self) -> int:
        """Get total strategies analyzed count from portfolio.json.

        Returns:
            Total number of strategies analyzed

        Raises:
            FileNotFoundError: If portfolio.json doesn't exist
            KeyError: If expected data structure is missing
        """
        data = self._load_portfolio_json()

        try:
            total_strategies = data["portfolio_metrics"]["monte_carlo"][
                "total_strategies_analyzed"
            ]
            return int(total_strategies)
        except KeyError as e:
            msg = f"Missing expected key in portfolio.json: {e}"
            raise KeyError(msg)

    def get_strategies_count_data(self) -> StrategiesCountData:
        """Get comprehensive strategies count data from portfolio.json.

        Returns:
            StrategiesCountData object with all relevant metrics

        Raises:
            FileNotFoundError: If portfolio.json doesn't exist
            KeyError: If expected data structure is missing
        """
        data = self._load_portfolio_json()

        try:
            monte_carlo = data["portfolio_metrics"]["monte_carlo"]
            concurrency = data["portfolio_metrics"]["concurrency"]

            return StrategiesCountData(
                total_strategies_analyzed=int(monte_carlo["total_strategies_analyzed"]),
                stable_strategies_count=int(monte_carlo["stable_strategies_count"]),
                stable_strategies_percentage=float(
                    monte_carlo["stable_strategies_percentage"],
                ),
                average_stability_score=float(monte_carlo["average_stability_score"]),
                max_concurrent_strategies=int(
                    concurrency["max_concurrent_strategies"]["value"],
                ),
                avg_concurrent_strategies=float(
                    concurrency["avg_concurrent_strategies"]["value"],
                ),
                last_updated=datetime.now(),
                data_source="portfolio.json",
            )
        except KeyError as e:
            msg = f"Missing expected key in portfolio.json: {e}"
            raise KeyError(msg)

    def get_concurrency_metrics(self) -> dict[str, Any]:
        """Get concurrency metrics from portfolio.json.

        Returns:
            Dictionary containing concurrency analysis metrics
        """
        data = self._load_portfolio_json()

        try:
            concurrency = data["portfolio_metrics"]["concurrency"]
            return {
                "total_concurrent_periods": concurrency["total_concurrent_periods"][
                    "value"
                ],
                "concurrency_ratio": concurrency["concurrency_ratio"]["value"],
                "exclusive_ratio": concurrency["exclusive_ratio"]["value"],
                "inactive_ratio": concurrency["inactive_ratio"]["value"],
                "avg_concurrent_strategies": concurrency["avg_concurrent_strategies"][
                    "value"
                ],
                "max_concurrent_strategies": concurrency["max_concurrent_strategies"][
                    "value"
                ],
            }
        except KeyError as e:
            msg = f"Missing expected concurrency key in portfolio.json: {e}"
            raise KeyError(msg)

    def get_monte_carlo_metrics(self) -> dict[str, Any]:
        """Get Monte Carlo simulation metrics from portfolio.json.

        Returns:
            Dictionary containing Monte Carlo analysis metrics
        """
        data = self._load_portfolio_json()

        try:
            monte_carlo = data["portfolio_metrics"]["monte_carlo"]
            return {
                "total_strategies_analyzed": monte_carlo["total_strategies_analyzed"],
                "stable_strategies_count": monte_carlo["stable_strategies_count"],
                "stable_strategies_percentage": monte_carlo[
                    "stable_strategies_percentage"
                ],
                "average_stability_score": monte_carlo["average_stability_score"],
                "simulation_parameters": monte_carlo.get("simulation_parameters", {}),
            }
        except KeyError as e:
            msg = f"Missing expected Monte Carlo key in portfolio.json: {e}"
            raise KeyError(msg)

    def validate_strategies_count(
        self,
        expected_count: int,
        tolerance: int = 0,
    ) -> tuple[bool, str]:
        """Validate strategies count against expected value.

        Args:
            expected_count: Expected total strategies count (e.g., from Excel)
            tolerance: Tolerance for comparison (default 0 for exact match)

        Returns:
            Tuple of (is_valid, validation_message)
        """
        actual_count = self.get_total_strategies_count()
        difference = abs(actual_count - expected_count)

        if difference <= tolerance:
            return True, f"Strategies count validation passed: {actual_count}"
        return (
            False,
            f"Strategies count validation failed: "
            f"Expected {expected_count}, "
            f"Got {actual_count}, "
            f"Difference {difference} exceeds tolerance {tolerance}",
        )

    def calculate_strategy_utilization_metrics(self) -> dict[str, float]:
        """Calculate strategy utilization metrics for position sizing.

        Returns:
            Dictionary containing strategy utilization metrics
        """
        strategies_data = self.get_strategies_count_data()
        concurrency_metrics = self.get_concurrency_metrics()

        # Calculate utilization metrics
        stable_utilization = (
            strategies_data.stable_strategies_count
            / strategies_data.total_strategies_analyzed
            * 100
        )

        concurrent_utilization = (
            concurrency_metrics["avg_concurrent_strategies"]
            / strategies_data.total_strategies_analyzed
            * 100
        )

        max_utilization = (
            concurrency_metrics["max_concurrent_strategies"]
            / strategies_data.total_strategies_analyzed
            * 100
        )

        return {
            "total_strategies": strategies_data.total_strategies_analyzed,
            "stable_strategies_percentage": stable_utilization,
            "average_concurrent_utilization": concurrent_utilization,
            "maximum_concurrent_utilization": max_utilization,
            "strategy_efficiency_score": strategies_data.average_stability_score * 100,
            "concurrency_ratio_percentage": concurrency_metrics["concurrency_ratio"]
            * 100,
        }

    def get_excel_compatible_metrics(self) -> dict[str, Any]:
        """Get metrics formatted for Excel integration.

        Returns:
            Dictionary containing metrics formatted for Excel spreadsheet integration
        """
        strategies_data = self.get_strategies_count_data()
        utilization = self.calculate_strategy_utilization_metrics()

        return {
            "Total_Strategies": strategies_data.total_strategies_analyzed,
            "Stable_Strategies": strategies_data.stable_strategies_count,
            "Stable_Percentage": round(strategies_data.stable_strategies_percentage, 2),
            "Avg_Concurrent": round(strategies_data.avg_concurrent_strategies, 2),
            "Max_Concurrent": strategies_data.max_concurrent_strategies,
            "Stability_Score": round(strategies_data.average_stability_score, 4),
            "Utilization_Avg": round(utilization["average_concurrent_utilization"], 2),
            "Utilization_Max": round(utilization["maximum_concurrent_utilization"], 2),
            "Last_Updated": strategies_data.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def export_strategies_data_to_csv(self, output_path: str | None = None) -> str:
        """Export strategies count data to CSV format.

        Args:
            output_path: Output file path. If None, uses default location.

        Returns:
            Path to the exported CSV file
        """
        if output_path is None:
            output_dir = self.base_dir / "data" / "exports"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / "strategies_count_export.csv")

        excel_metrics = self.get_excel_compatible_metrics()

        # Create single-row DataFrame for export
        import polars as pl

        df = pl.DataFrame([excel_metrics])
        df.write_csv(output_path)

        return output_path

    def get_strategy_allocation_basis(self) -> dict[str, float]:
        """Get strategy count data for allocation calculations.

        This provides the denominator for per-strategy allocation calculations
        as used in Excel position sizing formulas.

        Returns:
            Dictionary containing allocation basis metrics
        """
        strategies_data = self.get_strategies_count_data()

        return {
            "total_strategies_for_allocation": strategies_data.total_strategies_analyzed,
            "stable_strategies_for_allocation": strategies_data.stable_strategies_count,
            "per_strategy_allocation_base": 100.0
            / strategies_data.total_strategies_analyzed,  # Percentage per strategy
            "per_stable_strategy_allocation": 100.0
            / strategies_data.stable_strategies_count,  # Percentage per stable strategy
            "allocation_efficiency_factor": strategies_data.average_stability_score,
        }

    def validate_file_freshness(self, max_age_hours: int = 24) -> tuple[bool, str]:
        """Validate that portfolio.json file is recent enough for position sizing.

        Args:
            max_age_hours: Maximum age in hours for the file to be considered fresh

        Returns:
            Tuple of (is_fresh, status_message)
        """
        if not self.portfolio_file.exists():
            return False, f"Portfolio file not found: {self.portfolio_file}"

        file_mtime = datetime.fromtimestamp(self.portfolio_file.stat().st_mtime)
        current_time = datetime.now()
        age_hours = (current_time - file_mtime).total_seconds() / 3600

        if age_hours <= max_age_hours:
            return True, f"File is fresh: {age_hours:.1f} hours old"
        return (
            False,
            f"File is stale: {age_hours:.1f} hours old (max {max_age_hours} hours)",
        )

    def get_comprehensive_summary(self) -> dict[str, Any]:
        """Get comprehensive summary for position sizing dashboard.

        Returns:
            Dictionary containing all relevant strategies count and utilization data
        """
        strategies_data = self.get_strategies_count_data()
        utilization = self.calculate_strategy_utilization_metrics()
        allocation_basis = self.get_strategy_allocation_basis()
        is_fresh, freshness_msg = self.validate_file_freshness()

        return {
            "strategies_count": {
                "total": strategies_data.total_strategies_analyzed,
                "stable": strategies_data.stable_strategies_count,
                "stable_percentage": strategies_data.stable_strategies_percentage,
            },
            "concurrency": {
                "average": strategies_data.avg_concurrent_strategies,
                "maximum": strategies_data.max_concurrent_strategies,
                "avg_utilization": utilization["average_concurrent_utilization"],
                "max_utilization": utilization["maximum_concurrent_utilization"],
            },
            "allocation_basis": allocation_basis,
            "data_quality": {
                "stability_score": strategies_data.average_stability_score,
                "file_freshness": is_fresh,
                "freshness_message": freshness_msg,
                "last_updated": strategies_data.last_updated.isoformat(),
            },
        }
