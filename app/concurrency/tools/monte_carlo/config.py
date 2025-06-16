"""
Monte Carlo Configuration Management.

Provides configuration classes and validation for Monte Carlo parameter
robustness analysis integrated with the concurrency framework.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.concurrency.config_defaults import get_monte_carlo_defaults


@dataclass
class MonteCarloConfig:
    """Configuration for Monte Carlo parameter robustness analysis.

    This class manages Monte Carlo-specific configuration parameters,
    extending the base concurrency configuration with Monte Carlo settings.
    """

    # Core settings
    include_in_reports: bool = False
    num_simulations: int = 100
    confidence_level: float = 0.95
    max_parameters_to_test: int = 10

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "MonteCarloConfig":
        """Create MonteCarloConfig from configuration dictionary.

        Args:
            config_dict: Configuration dictionary with MC_ prefixed keys

        Returns:
            MonteCarloConfig: Configured Monte Carlo settings
        """
        return cls(
            include_in_reports=config_dict.get("MC_INCLUDE_IN_REPORTS", False),
            num_simulations=config_dict.get("MC_NUM_SIMULATIONS", 100),
            confidence_level=config_dict.get("MC_CONFIDENCE_LEVEL", 0.95),
            max_parameters_to_test=config_dict.get("MC_MAX_PARAMETERS_TO_TEST", 10),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert MonteCarloConfig to dictionary with MC_ prefixes.

        Returns:
            Dict[str, Any]: Configuration dictionary compatible with concurrency config
        """
        return {
            "MC_INCLUDE_IN_REPORTS": self.include_in_reports,
            "MC_NUM_SIMULATIONS": self.num_simulations,
            "MC_CONFIDENCE_LEVEL": self.confidence_level,
            "MC_MAX_PARAMETERS_TO_TEST": self.max_parameters_to_test,
        }

    def validate(self) -> "MonteCarloConfig":
        """Validate and normalize configuration values.

        Returns:
            MonteCarloConfig: Validated configuration
        """
        # Ensure simulation count is reasonable
        self.num_simulations = max(10, min(1000, self.num_simulations))

        # Ensure confidence level is valid
        self.confidence_level = max(0.5, min(0.999, self.confidence_level))

        # Ensure parameter limit is reasonable
        self.max_parameters_to_test = max(1, min(50, self.max_parameters_to_test))

        return self

    def is_enabled(self) -> bool:
        """Check if Monte Carlo analysis is enabled.

        Returns:
            bool: True if Monte Carlo analysis should run
        """
        return self.include_in_reports


def create_monte_carlo_config(
    base_config: Optional[Dict[str, Any]] = None
) -> MonteCarloConfig:
    """Create Monte Carlo configuration from base configuration.

    Args:
        base_config: Base configuration dictionary (optional)

    Returns:
        MonteCarloConfig: Validated Monte Carlo configuration
    """
    if base_config is None:
        base_config = {}

    # Get Monte Carlo defaults and merge with base config
    mc_defaults = get_monte_carlo_defaults()
    merged_config = {**mc_defaults, **base_config}

    # Create and validate configuration
    config = MonteCarloConfig.from_dict(merged_config)
    return config.validate()
