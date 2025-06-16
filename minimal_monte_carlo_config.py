"""
Minimal Monte Carlo Configuration Additions for app/concurrency/config_defaults.py

This provides only the most basic, beginner-level Monte Carlo features.
Start simple and add complexity later as users gain familiarity.
"""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class MinimalMonteCarloDefaults:
    """Minimal Monte Carlo configuration - beginner-friendly basics only."""

    # === BASIC FEATURE TOGGLE ===

    # Simple on/off switch for Monte Carlo analysis
    ENABLE_MONTE_CARLO: bool = False

    # === ESSENTIAL PARAMETERS ===

    # Number of simulations (keep it small for beginners)
    MC_NUM_SIMULATIONS: int = 100

    # Confidence level for results
    MC_CONFIDENCE_LEVEL: float = 0.95

    # Include Monte Carlo results in reports
    MC_INCLUDE_IN_REPORTS: bool = True

    # === BEGINNER-FRIENDLY DEFAULTS ===

    # Only test top-performing parameters (simpler results)
    MC_TEST_TOP_PERFORMERS_ONLY: bool = True

    # How many of the best parameters to test (keep small)
    MC_MAX_PARAMETERS_TO_TEST: int = 10


# === CONFIGURATION ADDITIONS FOR ConcurrencyDefaults ===


def get_minimal_monte_carlo_additions():
    """Get the minimal Monte Carlo fields to add to ConcurrencyDefaults."""
    return {
        # Basic Monte Carlo toggle
        "ENABLE_MONTE_CARLO": False,
        # Simple simulation count (beginner-friendly)
        "MC_NUM_SIMULATIONS": 100,
        # Standard confidence level
        "MC_CONFIDENCE_LEVEL": 0.95,
        # Include results in standard reports
        "MC_INCLUDE_IN_REPORTS": True,
        # Test only best parameters for simplicity
        "MC_TEST_TOP_PERFORMERS_ONLY": True,
        # Limit number of parameters tested
        "MC_MAX_PARAMETERS_TO_TEST": 10,
    }


# === SIMPLE VALIDATION ===


def validate_basic_monte_carlo_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Basic validation for Monte Carlo configuration."""

    # Ensure simulation count is reasonable (10-1000 range)
    sim_count = config.get("MC_NUM_SIMULATIONS", 100)
    config["MC_NUM_SIMULATIONS"] = max(10, min(1000, sim_count))

    # Ensure confidence level is valid (between 0.8 and 0.99)
    confidence = config.get("MC_CONFIDENCE_LEVEL", 0.95)
    config["MC_CONFIDENCE_LEVEL"] = max(0.8, min(0.99, confidence))

    # Ensure parameter limit is reasonable (1-50 range)
    max_params = config.get("MC_MAX_PARAMETERS_TO_TEST", 10)
    config["MC_MAX_PARAMETERS_TO_TEST"] = max(1, min(50, max_params))

    return config


# === BEGINNER USE CASE ===


def get_beginner_monte_carlo_config() -> Dict[str, Any]:
    """Get a beginner-friendly Monte Carlo configuration."""
    return {
        "ENABLE_MONTE_CARLO": True,
        "MC_NUM_SIMULATIONS": 50,  # Very fast for learning
        "MC_CONFIDENCE_LEVEL": 0.95,  # Standard confidence
        "MC_INCLUDE_IN_REPORTS": True,  # See results immediately
        "MC_TEST_TOP_PERFORMERS_ONLY": True,  # Focus on best parameters
        "MC_MAX_PARAMETERS_TO_TEST": 5,  # Just test top 5 for simplicity
    }
