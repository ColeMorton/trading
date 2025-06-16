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
]
