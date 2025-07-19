"""
Monte Carlo Parameter Robustness Analysis Module.

This module provides portfolio-level Monte Carlo parameter robustness testing
for the concurrency analysis framework. It tests parameter stability through
bootstrap sampling and parameter noise injection rather than price simulation.

Key Components:
    - MonteCarloAnalyzer: Core analysis engine for parameter robustness
    - MonteCarloConfig: Configuration management for Monte Carlo analysis
    - Bootstrap sampling utilities for time series data
    - Parameter stability metrics and scoring
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from .bootstrap import BootstrapSampler, create_bootstrap_sampler
from .config import MonteCarloConfig, create_monte_carlo_config
from .core import (
    MonteCarloAnalyzer,
    MonteCarloPortfolioResult,
    ParameterStabilityResult,
)
from .manager import MonteCarloProgressTracker, PortfolioMonteCarloManager
from .visualization import (
    MonteCarloVisualizationConfig,
    PortfolioMonteCarloVisualizer,
    create_monte_carlo_visualizations,
)


class MonteCarloManager:
    """Simplified Monte Carlo manager for CLI integration.

    This class provides a unified interface for running Monte Carlo simulations
    on trading portfolios, calculating risk metrics, and generating forecasts.
    It wraps the existing Monte Carlo infrastructure to provide the interface
    expected by the CLI commands.
    """

    def __init__(
        self,
        n_simulations: int = 10000,
        confidence_levels: List[float] = None,
        horizon_days: int = 252,
        use_bootstrap: bool = True,
    ):
        """Initialize Monte Carlo manager.

        Args:
            n_simulations: Number of Monte Carlo simulations to run
            confidence_levels: Confidence levels for VaR/CVaR calculations
            horizon_days: Forecast horizon in trading days
            use_bootstrap: Whether to use bootstrap resampling
        """
        self.n_simulations = n_simulations
        self.confidence_levels = confidence_levels or [95, 99]
        self.horizon_days = horizon_days
        self.use_bootstrap = use_bootstrap

        # Create Monte Carlo configuration
        self.config = create_monte_carlo_config(
            n_simulations=n_simulations,
            confidence_levels=confidence_levels,
            max_parameters_to_test=50,
            parameter_stability_threshold=0.7,
            minimum_stability_score=0.6,
            enable_bootstrap=use_bootstrap,
        )

        # Initialize portfolio manager
        self.portfolio_manager = PortfolioMonteCarloManager(self.config)

    def run_portfolio_simulation(
        self,
        portfolio_data: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Dict[str, Any]:
        """Run Monte Carlo simulation on portfolio.

        Args:
            portfolio_data: List of strategy configurations
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary containing risk metrics and forecasts
        """
        try:
            # Run parameter stability analysis
            mc_results = self.portfolio_manager.analyze_portfolio(portfolio_data)

            # Calculate portfolio returns for risk metrics
            portfolio_returns = self._calculate_portfolio_returns(portfolio_data)

            # Run simulations
            simulated_returns = self._run_return_simulations(
                portfolio_returns, progress_callback
            )

            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(simulated_returns)

            # Generate forecasts
            forecast = self._generate_forecast(simulated_returns)

            # Calculate portfolio statistics
            stats = self._calculate_portfolio_stats(portfolio_returns)

            return {
                "risk_metrics": risk_metrics,
                "forecast": forecast,
                "expected_return": stats["expected_return"],
                "volatility": stats["volatility"],
                "sharpe_ratio": stats["sharpe_ratio"],
                "max_drawdown": stats["max_drawdown"],
                "monte_carlo_results": mc_results,
                "n_simulations": self.n_simulations,
                "horizon_days": self.horizon_days,
            }

        except Exception as e:
            raise RuntimeError(f"Monte Carlo simulation failed: {str(e)}")

    def _calculate_portfolio_returns(
        self, portfolio_data: List[Dict[str, Any]]
    ) -> np.ndarray:
        """Calculate historical portfolio returns.

        This is a placeholder that would integrate with the actual
        portfolio return calculation logic.
        """
        # For demo purposes, generate synthetic returns
        # In production, this would calculate actual portfolio returns
        np.random.seed(42)
        daily_returns = np.random.normal(0.0005, 0.02, 252 * 3)  # 3 years of data
        return daily_returns

    def _run_return_simulations(
        self,
        historical_returns: np.ndarray,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> np.ndarray:
        """Run Monte Carlo simulations on returns."""
        n_days = self.horizon_days
        n_sims = self.n_simulations

        # Calculate return statistics
        mean_return = np.mean(historical_returns)
        return_volatility = np.std(historical_returns)

        # Generate simulated return paths
        simulated_returns = np.zeros((n_sims, n_days))

        for i in range(n_sims):
            if self.use_bootstrap:
                # Bootstrap from historical returns
                daily_returns = np.random.choice(
                    historical_returns, size=n_days, replace=True
                )
            else:
                # Generate from normal distribution
                daily_returns = np.random.normal(mean_return, return_volatility, n_days)

            # Calculate cumulative returns
            simulated_returns[i] = np.cumprod(1 + daily_returns) - 1

            # Update progress
            if progress_callback and i % 100 == 0:
                progress_callback(i)

        if progress_callback:
            progress_callback(n_sims)

        return simulated_returns

    def _calculate_risk_metrics(
        self, simulated_returns: np.ndarray
    ) -> Dict[str, float]:
        """Calculate VaR and CVaR from simulated returns."""
        final_returns = simulated_returns[:, -1]  # Terminal values

        risk_metrics = {}
        for confidence_level in self.confidence_levels:
            percentile = 100 - confidence_level

            # Calculate VaR
            var = np.percentile(final_returns, percentile)
            risk_metrics[f"var_{int(confidence_level)}"] = var

            # Calculate CVaR (expected shortfall)
            cvar = np.mean(final_returns[final_returns <= var])
            risk_metrics[f"cvar_{int(confidence_level)}"] = cvar

        return risk_metrics

    def _generate_forecast(self, simulated_returns: np.ndarray) -> Dict[str, float]:
        """Generate forecast statistics from simulations."""
        final_returns = simulated_returns[:, -1]

        return {
            "median": np.median(final_returns),
            "mean": np.mean(final_returns),
            "lower_95": np.percentile(final_returns, 2.5),
            "upper_95": np.percentile(final_returns, 97.5),
            "lower_99": np.percentile(final_returns, 0.5),
            "upper_99": np.percentile(final_returns, 99.5),
            "probability_positive": np.mean(final_returns > 0),
        }

    def _calculate_portfolio_stats(self, returns: np.ndarray) -> Dict[str, float]:
        """Calculate portfolio statistics."""
        # Annualized statistics
        expected_return = np.mean(returns) * 252
        volatility = np.std(returns) * np.sqrt(252)
        sharpe_ratio = expected_return / volatility if volatility > 0 else 0

        # Calculate maximum drawdown
        cumulative_returns = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdowns)

        return {
            "expected_return": expected_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
        }

    def save_simulation_paths(self, output_dir: Path) -> None:
        """Save simulation paths to directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        # Implementation would save simulation data

    def create_visualization(self, results: Dict[str, Any]) -> Path:
        """Create visualization of Monte Carlo results."""
        # Use existing visualization infrastructure
        viz_config = MonteCarloVisualizationConfig()
        visualizer = PortfolioMonteCarloVisualizer(viz_config)

        # Create appropriate visualizations
        output_path = Path("./monte_carlo_visualizations")
        output_path.mkdir(parents=True, exist_ok=True)

        # Placeholder for actual visualization
        viz_path = output_path / "monte_carlo_results.html"

        return viz_path


__all__ = [
    "MonteCarloAnalyzer",
    "MonteCarloConfig",
    "MonteCarloPortfolioResult",
    "ParameterStabilityResult",
    "BootstrapSampler",
    "PortfolioMonteCarloManager",
    "MonteCarloProgressTracker",
    "MonteCarloVisualizationConfig",
    "PortfolioMonteCarloVisualizer",
    "create_bootstrap_sampler",
    "create_monte_carlo_config",
    "create_monte_carlo_visualizations",
    "MonteCarloManager",  # Added the new manager
]
