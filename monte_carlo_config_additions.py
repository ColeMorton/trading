"""
Proposed Monte Carlo Configuration Additions for app/concurrency/config_defaults.py

This outlines the configuration options that should be added to support
portfolio-level Monte Carlo parameter robustness analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MonteCarloMode(Enum):
    """Monte Carlo analysis modes for different use cases."""

    DISABLED = "disabled"  # No Monte Carlo analysis
    VALIDATION_ONLY = "validation_only"  # Validate existing parameters only
    PARAMETER_OPTIMIZATION = "parameter_optimization"  # Full parameter optimization
    RISK_ASSESSMENT = "risk_assessment"  # Focus on stability and risk metrics
    RESEARCH_MODE = "research_mode"  # Comprehensive analysis for research


class MonteCarloTrigger(Enum):
    """When to trigger Monte Carlo analysis."""

    NEVER = "never"  # Manual trigger only
    ALWAYS = "always"  # Run with every portfolio analysis
    ON_LOW_CONFIDENCE = "on_low_confidence"  # Only when strategy confidence is low
    SCHEDULED = "scheduled"  # Based on schedule/frequency
    ON_PARAMETER_CHANGE = "on_parameter_change"  # When parameters change


class BootstrapMethod(Enum):
    """Bootstrap sampling methods for time series data."""

    BLOCK = "block"  # Block bootstrap (preserves time structure)
    CIRCULAR = "circular"  # Circular block bootstrap
    STATIONARY = "stationary"  # Stationary bootstrap
    MOVING_BLOCK = "moving_block"  # Moving block bootstrap


class RegimeDetectionMethod(Enum):
    """Methods for market regime detection."""

    DISABLED = "disabled"  # No regime detection
    VOLATILITY_BASED = "volatility_based"  # Based on volatility clustering
    RETURNS_BASED = "returns_based"  # Based on return distributions
    REGIME_SWITCHING = "regime_switching"  # Markov regime switching model


@dataclass
class MonteCarloDefaults:
    """Monte Carlo configuration defaults to add to ConcurrencyDefaults."""

    # === CORE MONTE CARLO SETTINGS ===

    # Enable/disable Monte Carlo analysis
    ENABLE_MONTE_CARLO: bool = False

    # Monte Carlo analysis mode
    MONTE_CARLO_MODE: str = MonteCarloMode.DISABLED.value

    # When to trigger Monte Carlo analysis
    MONTE_CARLO_TRIGGER: str = MonteCarloTrigger.NEVER.value

    # === SIMULATION PARAMETERS ===

    # Number of Monte Carlo simulations
    MC_NUM_SIMULATIONS: int = 1000

    # Confidence level for statistical analysis
    MC_CONFIDENCE_LEVEL: float = 0.95

    # Minimum number of simulations for valid results
    MC_MIN_SIMULATIONS: int = 100

    # Maximum number of simulations (performance limit)
    MC_MAX_SIMULATIONS: int = 10000

    # === BOOTSTRAP CONFIGURATION ===

    # Bootstrap sampling method
    MC_BOOTSTRAP_METHOD: str = BootstrapMethod.BLOCK.value

    # Bootstrap block size (trading days)
    MC_BOOTSTRAP_BLOCK_SIZE: int = 63  # ~3 months

    # Minimum data fraction required for valid bootstrap
    MC_MIN_DATA_FRACTION: float = 0.7

    # Bootstrap overlap fraction
    MC_BOOTSTRAP_OVERLAP: float = 0.0

    # === PARAMETER ROBUSTNESS SETTINGS ===

    # Standard deviation for parameter noise injection
    MC_PARAMETER_NOISE_STD: float = 0.1

    # Stability score threshold for "stable" classification
    MC_STABILITY_THRESHOLD: float = 0.7

    # Parameter robustness threshold
    MC_ROBUSTNESS_THRESHOLD: float = 0.6

    # Regime consistency threshold
    MC_REGIME_CONSISTENCY_THRESHOLD: float = 0.5

    # === MARKET REGIME DETECTION ===

    # Enable market regime analysis
    MC_ENABLE_REGIME_ANALYSIS: bool = True

    # Regime detection method
    MC_REGIME_DETECTION_METHOD: str = RegimeDetectionMethod.VOLATILITY_BASED.value

    # Rolling window size for regime detection (trading days)
    MC_REGIME_WINDOW: int = 63

    # Minimum regime duration (trading days)
    MC_MIN_REGIME_DURATION: int = 10

    # === PERFORMANCE AND RESOURCE MANAGEMENT ===

    # Enable parallel processing
    MC_ENABLE_PARALLEL: bool = True

    # Maximum number of parallel workers
    MC_MAX_WORKERS: int = 4

    # Memory limit per worker (MB)
    MC_MEMORY_LIMIT_MB: int = 2048

    # Timeout for individual simulations (seconds)
    MC_SIMULATION_TIMEOUT: int = 300

    # === PORTFOLIO-LEVEL ANALYSIS ===

    # Percentage of top-performing parameters to test with Monte Carlo
    MC_TOP_PERCENTAGE_FILTER: float = 0.3

    # Maximum number of parameter combinations to test per ticker
    MC_MAX_COMBINATIONS_PER_TICKER: int = 50

    # Enable cross-ticker correlation analysis
    MC_ENABLE_CROSS_TICKER_CORRELATION: bool = True

    # Portfolio-level stability scoring
    MC_PORTFOLIO_STABILITY_WEIGHT: float = 0.6

    # === INTEGRATION SETTINGS ===

    # Include Monte Carlo results in standard portfolio reports
    MC_INCLUDE_IN_REPORTS: bool = True

    # Export detailed Monte Carlo analysis to separate files
    MC_EXPORT_DETAILED_RESULTS: bool = False

    # Generate Monte Carlo visualizations
    MC_GENERATE_VISUALIZATIONS: bool = False

    # Integration with existing scoring system weight
    MC_ROBUSTNESS_SCORE_WEIGHT: float = 0.5  # Weight in final recommendation score

    # === OUTPUT AND REPORTING ===

    # Monte Carlo report components to include
    MC_REPORT_INCLUDES: Dict[str, bool] = field(
        default_factory=lambda: {
            "STABILITY_METRICS": True,  # Parameter stability scores
            "BOOTSTRAP_STATISTICS": True,  # Bootstrap sampling statistics
            "REGIME_ANALYSIS": True,  # Market regime consistency
            "CONFIDENCE_INTERVALS": True,  # Performance confidence intervals
            "CORRELATION_MATRIX": False,  # Cross-parameter correlations
            "DETAILED_SIMULATIONS": False,  # Individual simulation results
            "VISUALIZATION_DATA": False,  # Data for generating visualizations
        }
    )

    # === DATA QUALITY AND VALIDATION ===

    # Monte Carlo-specific data quality thresholds
    MC_DATA_QUALITY_THRESHOLDS: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: {
            "strict": {
                "min_historical_periods": 252,  # 1 year minimum
                "min_trades_per_simulation": 10,  # Minimum trades for valid simulation
                "max_parameter_deviation": 0.2,  # Maximum parameter deviation allowed
                "min_simulation_success_rate": 0.95,  # Minimum successful simulation rate
                "max_correlation_with_base": 0.99,  # Maximum correlation with base case
            },
            "moderate": {
                "min_historical_periods": 126,  # 6 months minimum
                "min_trades_per_simulation": 5,  # Minimum trades for valid simulation
                "max_parameter_deviation": 0.3,  # Maximum parameter deviation allowed
                "min_simulation_success_rate": 0.90,  # Minimum successful simulation rate
                "max_correlation_with_base": 0.995,  # Maximum correlation with base case
            },
            "permissive": {
                "min_historical_periods": 63,  # 3 months minimum
                "min_trades_per_simulation": 3,  # Minimum trades for valid simulation
                "max_parameter_deviation": 0.5,  # Maximum parameter deviation allowed
                "min_simulation_success_rate": 0.80,  # Minimum successful simulation rate
                "max_correlation_with_base": 0.999,  # Maximum correlation with base case
            },
        }
    )

    # === STRATEGY-SPECIFIC OVERRIDES ===

    # Strategy-specific Monte Carlo parameters
    MC_STRATEGY_OVERRIDES: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: {
            "SMA": {
                "parameter_noise_std": 0.05,  # Lower noise for SMA
                "min_window_size": 5,  # Minimum SMA window
                "max_window_size": 200,  # Maximum SMA window
            },
            "EMA": {
                "parameter_noise_std": 0.1,  # Standard noise for EMA
                "min_window_size": 5,  # Minimum EMA window
                "max_window_size": 200,  # Maximum EMA window
            },
            "MACD": {
                "parameter_noise_std": 0.15,  # Higher noise for MACD
                "min_fast_period": 5,  # Minimum fast period
                "max_slow_period": 50,  # Maximum slow period
            },
        }
    )


# === MONTE CARLO USE CASE CONFIGURATIONS ===


def get_monte_carlo_validation_config() -> Dict[str, Any]:
    """Get Monte Carlo configuration optimized for parameter validation."""
    return {
        "MONTE_CARLO_MODE": MonteCarloMode.VALIDATION_ONLY.value,
        "MC_NUM_SIMULATIONS": 500,  # Faster validation
        "MC_TOP_PERCENTAGE_FILTER": 1.0,  # Test all current parameters
        "MC_STABILITY_THRESHOLD": 0.8,  # High stability requirement
        "MC_GENERATE_VISUALIZATIONS": True,  # Show validation results
        "MC_INCLUDE_IN_REPORTS": True,  # Include in standard reports
    }


def get_monte_carlo_optimization_config() -> Dict[str, Any]:
    """Get Monte Carlo configuration optimized for parameter optimization."""
    return {
        "MONTE_CARLO_MODE": MonteCarloMode.PARAMETER_OPTIMIZATION.value,
        "MC_NUM_SIMULATIONS": 2000,  # Comprehensive analysis
        "MC_TOP_PERCENTAGE_FILTER": 0.2,  # Focus on top performers
        "MC_ENABLE_PARALLEL": True,  # Use all available cores
        "MC_EXPORT_DETAILED_RESULTS": True,  # Export for further analysis
        "MC_GENERATE_VISUALIZATIONS": True,  # Full visualization suite
    }


def get_monte_carlo_risk_assessment_config() -> Dict[str, Any]:
    """Get Monte Carlo configuration optimized for risk assessment."""
    return {
        "MONTE_CARLO_MODE": MonteCarloMode.RISK_ASSESSMENT.value,
        "MC_NUM_SIMULATIONS": 1000,  # Balanced analysis
        "MC_ENABLE_REGIME_ANALYSIS": True,  # Critical for risk assessment
        "MC_CONFIDENCE_LEVEL": 0.99,  # High confidence for risk
        "MC_STABILITY_THRESHOLD": 0.9,  # Very high stability requirement
        "VALIDATION_LEVEL": "strict",  # Strict validation for risk
    }


def get_monte_carlo_research_config() -> Dict[str, Any]:
    """Get Monte Carlo configuration optimized for research and development."""
    return {
        "MONTE_CARLO_MODE": MonteCarloMode.RESEARCH_MODE.value,
        "MC_NUM_SIMULATIONS": 5000,  # Maximum simulations
        "MC_TOP_PERCENTAGE_FILTER": 1.0,  # Test all combinations
        "MC_EXPORT_DETAILED_RESULTS": True,  # Export everything
        "MC_GENERATE_VISUALIZATIONS": True,  # Full visualization suite
        "MC_REPORT_INCLUDES": {  # Include all reports
            "STABILITY_METRICS": True,
            "BOOTSTRAP_STATISTICS": True,
            "REGIME_ANALYSIS": True,
            "CONFIDENCE_INTERVALS": True,
            "CORRELATION_MATRIX": True,
            "DETAILED_SIMULATIONS": True,
            "VISUALIZATION_DATA": True,
        },
    }


# === MONTE CARLO TRIGGER CONDITIONS ===


def should_trigger_monte_carlo_analysis(
    portfolio_data: List[Dict], config: Dict[str, Any]
) -> bool:
    """Determine if Monte Carlo analysis should be triggered based on configuration and portfolio state."""

    trigger_mode = config.get("MONTE_CARLO_TRIGGER", MonteCarloTrigger.NEVER.value)

    if trigger_mode == MonteCarloTrigger.NEVER.value:
        return False

    if trigger_mode == MonteCarloTrigger.ALWAYS.value:
        return True

    if trigger_mode == MonteCarloTrigger.ON_LOW_CONFIDENCE.value:
        # Trigger if any strategy has low confidence (few trades, low win rate, etc.)
        for strategy in portfolio_data:
            total_trades = strategy.get("Total Trades", 0)
            win_rate = strategy.get("Win Rate [%]", 0)

            if total_trades < 20 or win_rate < 40:  # Low confidence thresholds
                return True

    # Add more trigger conditions as needed
    return False


# === CONFIGURATION VALIDATION ===


def validate_monte_carlo_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate Monte Carlo configuration parameters."""

    # Ensure simulation count is within bounds
    sim_count = config.get("MC_NUM_SIMULATIONS", 1000)
    min_sims = config.get("MC_MIN_SIMULATIONS", 100)
    max_sims = config.get("MC_MAX_SIMULATIONS", 10000)

    config["MC_NUM_SIMULATIONS"] = max(min_sims, min(max_sims, sim_count))

    # Ensure confidence level is valid
    confidence = config.get("MC_CONFIDENCE_LEVEL", 0.95)
    config["MC_CONFIDENCE_LEVEL"] = max(0.5, min(0.999, confidence))

    # Ensure thresholds are in valid ranges
    stability_thresh = config.get("MC_STABILITY_THRESHOLD", 0.7)
    config["MC_STABILITY_THRESHOLD"] = max(0.0, min(1.0, stability_thresh))

    # Validate bootstrap parameters
    block_size = config.get("MC_BOOTSTRAP_BLOCK_SIZE", 63)
    config["MC_BOOTSTRAP_BLOCK_SIZE"] = max(5, min(252, block_size))

    return config
