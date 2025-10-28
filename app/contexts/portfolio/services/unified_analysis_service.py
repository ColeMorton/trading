"""
Unified Analysis Service.

This service provides integration between the concurrency analysis system
and the Statistical Performance Divergence System (SPDS) for comprehensive
portfolio analysis.
"""

from collections.abc import Callable
import logging
from pathlib import Path
from typing import Any

from app.contexts.portfolio.services.concurrency_analysis_service import (
    ConcurrencyAnalysisEngine,
)
from app.tools.exceptions import TradingSystemError
from app.tools.portfolio import StrategyConfig


class UnifiedAnalysisService:
    """Service for unified analysis combining concurrency and SPDS systems.

    This service coordinates between different analysis systems to provide
    comprehensive portfolio insights including concurrency, divergence,
    and optimization analysis.
    """

    def __init__(
        self,
        enable_concurrency_analysis: bool = True,
        enable_spds_analysis: bool = False,  # SPDS integration placeholder
        enable_memory_optimization: bool = False,
        log: Callable[[str, str], None] | None = None,
    ):
        """Initialize the unified analysis service.

        Args:
            enable_concurrency_analysis: Enable concurrency analysis
            enable_spds_analysis: Enable SPDS analysis integration
            enable_memory_optimization: Enable memory optimization
            log: Logging function
        """
        self.enable_concurrency = enable_concurrency_analysis
        self.enable_spds = enable_spds_analysis
        self.enable_memory_optimization = enable_memory_optimization
        self.log = log or self._default_log

        # Initialize concurrency analysis engine
        if self.enable_concurrency:
            self.concurrency_engine = ConcurrencyAnalysisEngine(
                enable_memory_optimization=enable_memory_optimization,
                enable_visualization=True,
                enable_optimization=True,
                log=self.log,
            )
        else:
            self.concurrency_engine = None

        # SPDS integration placeholder
        self.spds_engine = None
        if self.enable_spds:
            self._initialize_spds_integration()

    def run_comprehensive_analysis(
        self,
        portfolio_path: str | Path,
        config_overrides: dict[str, Any] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Run comprehensive analysis combining all enabled systems.

        Args:
            portfolio_path: Path to portfolio file
            config_overrides: Configuration overrides
            progress_callback: Progress callback

        Returns:
            Unified analysis results
        """
        try:
            self.log("Starting comprehensive unified analysis", "info")

            unified_results = {
                "portfolio_path": str(portfolio_path),
                "analysis_components": [],
                "summary": {},
            }

            # Run concurrency analysis
            if self.enable_concurrency and self.concurrency_engine:
                self.log("Running concurrency analysis", "info")

                concurrency_results = self.concurrency_engine.analyze_portfolio(
                    portfolio_path=portfolio_path,
                    config_overrides=config_overrides,
                    progress_callback=progress_callback,
                )

                unified_results["concurrency_analysis"] = concurrency_results
                unified_results["analysis_components"].append("concurrency")

                # Extract key metrics for summary
                if "portfolio_metrics" in concurrency_results:
                    portfolio_metrics = concurrency_results["portfolio_metrics"]
                    unified_results["summary"]["concurrency"] = {
                        "efficiency_score": portfolio_metrics.get("efficiency", {})
                        .get("score", {})
                        .get("value", 0),
                        "concurrent_ratio": portfolio_metrics.get("concurrency", {})
                        .get("concurrent_ratio", {})
                        .get("value", 0),
                        "total_strategies": len(
                            concurrency_results.get("strategies", [])
                        ),
                    }

            # Run SPDS analysis (placeholder)
            if self.enable_spds and self.spds_engine:
                self.log("Running SPDS analysis", "info")

                spds_results = self._run_spds_analysis(
                    portfolio_path, config_overrides, progress_callback
                )

                unified_results["spds_analysis"] = spds_results
                unified_results["analysis_components"].append("spds")

                # Extract key metrics for summary
                unified_results["summary"]["spds"] = {
                    "divergence_score": spds_results.get("divergence_score", 0),
                    "stability_rating": spds_results.get("stability_rating", "unknown"),
                }

            # Generate cross-system insights
            if len(unified_results["analysis_components"]) > 1:
                unified_results[
                    "cross_system_insights"
                ] = self._generate_cross_system_insights(unified_results)

            # Generate unified recommendations
            unified_results["recommendations"] = self._generate_unified_recommendations(
                unified_results
            )

            self.log("Comprehensive analysis completed", "info")
            return unified_results

        except Exception as e:
            error_msg = f"Unified analysis failed: {e!s}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def analyze_strategy_interactions(
        self,
        strategies: list[StrategyConfig],
        config_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Analyze interactions between strategies across different systems.

        Args:
            strategies: List of strategy configurations
            config_overrides: Configuration overrides

        Returns:
            Strategy interaction analysis results
        """
        try:
            self.log(f"Analyzing interactions for {len(strategies)} strategies", "info")

            interaction_results = {
                "total_strategies": len(strategies),
                "interaction_matrix": {},
                "system_specific_results": {},
            }

            # Concurrency-based interactions
            if self.enable_concurrency and self.concurrency_engine:
                concurrency_analysis = self.concurrency_engine.analyze_strategies(
                    strategies=strategies,
                    config_overrides=config_overrides,
                )

                interaction_results["system_specific_results"]["concurrency"] = {
                    "correlation_matrix": concurrency_analysis.get(
                        "correlation_matrix", {}
                    ),
                    "efficiency_metrics": concurrency_analysis.get(
                        "portfolio_efficiency", {}
                    ),
                    "activity_periods": concurrency_analysis.get(
                        "activity_periods", {}
                    ),
                }

            # SPDS-based interactions (placeholder)
            if self.enable_spds:
                spds_interactions = self._analyze_spds_interactions(strategies)
                interaction_results["system_specific_results"][
                    "spds"
                ] = spds_interactions

            # Cross-system interaction analysis
            if len(interaction_results["system_specific_results"]) > 1:
                interaction_results[
                    "cross_system_analysis"
                ] = self._analyze_cross_system_interactions(
                    interaction_results["system_specific_results"]
                )

            return interaction_results

        except Exception as e:
            error_msg = f"Strategy interaction analysis failed: {e!s}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def generate_optimization_recommendations(
        self,
        analysis_results: dict[str, Any],
        optimization_criteria: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate optimization recommendations based on unified analysis.

        Args:
            analysis_results: Results from unified analysis
            optimization_criteria: Criteria for optimization

        Returns:
            Optimization recommendations
        """
        try:
            self.log("Generating optimization recommendations", "info")

            criteria = optimization_criteria or {
                "max_correlation": 0.7,
                "min_efficiency": 0.6,
                "max_concurrent_ratio": 0.8,
            }

            recommendations = {
                "optimization_criteria": criteria,
                "recommendations": [],
                "risk_warnings": [],
                "performance_enhancements": [],
            }

            # Analyze concurrency results
            if "concurrency_analysis" in analysis_results:
                concurrency_recs = self._generate_concurrency_recommendations(
                    analysis_results["concurrency_analysis"], criteria
                )
                recommendations["recommendations"].extend(concurrency_recs)

            # Analyze SPDS results (placeholder)
            if "spds_analysis" in analysis_results:
                spds_recs = self._generate_spds_recommendations(
                    analysis_results["spds_analysis"], criteria
                )
                recommendations["recommendations"].extend(spds_recs)

            # Cross-system recommendations
            if "cross_system_insights" in analysis_results:
                cross_recs = self._generate_cross_system_recommendations(
                    analysis_results["cross_system_insights"], criteria
                )
                recommendations["recommendations"].extend(cross_recs)

            return recommendations

        except Exception as e:
            error_msg = f"Recommendation generation failed: {e!s}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def _initialize_spds_integration(self):
        """Initialize SPDS system integration (placeholder)."""
        try:
            # This would integrate with the actual SPDS system
            # For now, it's a placeholder for future implementation
            self.log("SPDS integration initialized (placeholder)", "info")

            # Future implementation would import and initialize SPDS components
            # from app.spds import SPDSAnalysisEngine
            # self.spds_engine = SPDSAnalysisEngine(...)

        except Exception as e:
            self.log(f"SPDS integration failed: {e!s}", "warning")
            self.enable_spds = False

    def _run_spds_analysis(
        self,
        portfolio_path: str | Path,
        config_overrides: dict[str, Any] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Run SPDS analysis (placeholder implementation)."""
        # Placeholder for SPDS integration
        return {
            "divergence_score": 0.0,
            "stability_rating": "unknown",
            "analysis_type": "placeholder",
            "message": "SPDS integration not yet implemented",
        }

    def _analyze_spds_interactions(
        self, strategies: list[StrategyConfig]
    ) -> dict[str, Any]:
        """Analyze SPDS-based strategy interactions (placeholder)."""
        return {
            "interaction_type": "spds_placeholder",
            "strategy_count": len(strategies),
            "message": "SPDS interaction analysis not yet implemented",
        }

    def _generate_cross_system_insights(
        self, unified_results: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate insights by combining results from multiple systems."""
        insights = {
            "cross_system_correlations": {},
            "system_agreement": {},
            "divergent_findings": [],
        }

        # Example cross-system analysis
        if (
            "concurrency" in unified_results["summary"]
            and "spds" in unified_results["summary"]
        ):
            concurrency_efficiency = unified_results["summary"]["concurrency"][
                "efficiency_score"
            ]
            spds_divergence = unified_results["summary"]["spds"]["divergence_score"]

            # Analyze agreement between systems
            insights["system_agreement"]["efficiency_divergence_correlation"] = {
                "concurrency_efficiency": concurrency_efficiency,
                "spds_divergence": spds_divergence,
                "correlation": (
                    "positive"
                    if concurrency_efficiency > 0.5 and spds_divergence < 0.3
                    else "negative"
                ),
            }

        return insights

    def _analyze_cross_system_interactions(
        self, system_results: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze interactions across different analysis systems."""
        cross_analysis = {
            "systems_analyzed": list(system_results.keys()),
            "interaction_strength": {},
            "consensus_metrics": {},
        }

        # Placeholder for cross-system interaction analysis
        return cross_analysis

    def _generate_unified_recommendations(
        self, unified_results: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate recommendations based on unified analysis results."""
        recommendations = []

        # Extract summary data
        summary = unified_results.get("summary", {})

        # Concurrency-based recommendations
        if "concurrency" in summary:
            concurrency_summary = summary["concurrency"]
            efficiency_score = concurrency_summary.get("efficiency_score", 0)
            concurrent_ratio = concurrency_summary.get("concurrent_ratio", 0)

            if efficiency_score < 0.5:
                recommendations.append(
                    {
                        "type": "efficiency_improvement",
                        "priority": "high",
                        "message": "Portfolio efficiency is low. Consider strategy optimization.",
                        "suggested_action": "Run optimization analysis to find better strategy combinations",
                    }
                )

            if concurrent_ratio > 0.8:
                recommendations.append(
                    {
                        "type": "risk_management",
                        "priority": "medium",
                        "message": "High concurrent trading ratio detected. Consider diversification.",
                        "suggested_action": "Add strategies with different market timing",
                    }
                )

        # SPDS-based recommendations (placeholder)
        if "spds" in summary:
            recommendations.append(
                {
                    "type": "spds_integration",
                    "priority": "low",
                    "message": "SPDS analysis available for enhanced insights",
                    "suggested_action": "Enable SPDS integration for divergence analysis",
                }
            )

        return recommendations

    def _generate_concurrency_recommendations(
        self, concurrency_results: dict[str, Any], criteria: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate recommendations based on concurrency analysis."""
        recommendations = []

        # Extract metrics
        portfolio_metrics = concurrency_results.get("portfolio_metrics", {})
        efficiency = (
            portfolio_metrics.get("efficiency", {}).get("score", {}).get("value", 0)
        )

        if efficiency < criteria.get("min_efficiency", 0.6):
            recommendations.append(
                {
                    "system": "concurrency",
                    "type": "efficiency",
                    "message": f"Portfolio efficiency ({efficiency:.3f}) below threshold",
                    "action": "Consider strategy optimization or rebalancing",
                }
            )

        return recommendations

    def _generate_spds_recommendations(
        self, spds_results: dict[str, Any], criteria: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate recommendations based on SPDS analysis (placeholder)."""
        return [
            {
                "system": "spds",
                "type": "placeholder",
                "message": "SPDS recommendations not yet implemented",
                "action": "Enable SPDS integration for detailed recommendations",
            }
        ]

    def _generate_cross_system_recommendations(
        self, cross_insights: dict[str, Any], criteria: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate recommendations based on cross-system insights."""
        recommendations = []

        if "system_agreement" in cross_insights:
            recommendations.append(
                {
                    "system": "unified",
                    "type": "consensus",
                    "message": "Multiple analysis systems provide consistent insights",
                    "action": "High confidence in portfolio assessment",
                }
            )

        return recommendations

    def _default_log(self, message: str, level: str = "info") -> None:
        """Default logging implementation."""
        logger = logging.getLogger(__name__)
        getattr(logger, level.lower(), logger.info)(message)


# Convenience functions
def run_unified_portfolio_analysis(
    portfolio_path: str | Path,
    enable_concurrency: bool = True,
    enable_spds: bool = False,
    enable_memory_optimization: bool = False,
    config_overrides: dict[str, Any] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    """Run unified portfolio analysis with all available systems.

    This is a convenience function for comprehensive portfolio analysis.
    """
    service = UnifiedAnalysisService(
        enable_concurrency_analysis=enable_concurrency,
        enable_spds_analysis=enable_spds,
        enable_memory_optimization=enable_memory_optimization,
    )

    return service.run_comprehensive_analysis(
        portfolio_path=portfolio_path,
        config_overrides=config_overrides,
        progress_callback=progress_callback,
    )
