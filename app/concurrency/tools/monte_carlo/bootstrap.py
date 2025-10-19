"""
Bootstrap Sampling Utilities for Monte Carlo Analysis.

Provides bootstrap sampling methods optimized for time series financial data,
preserving temporal dependencies and market microstructure patterns.
"""

import random

import numpy as np
import polars as pl


class BootstrapSampler:
    """Bootstrap sampling utilities for time series financial data."""

    def __init__(self, block_size: int = 63, min_data_fraction: float = 0.7):
        """Initialize bootstrap sampler.

        Args:
            block_size: Size of blocks for block bootstrap (default: ~3 months)
            min_data_fraction: Minimum fraction of original data to include
        """
        self.block_size = block_size
        self.min_data_fraction = min_data_fraction

    def block_bootstrap_sample(
        self, data: pl.DataFrame, seed: int | None = None
    ) -> pl.DataFrame:
        """Create bootstrap sample using block bootstrap method.

        Block bootstrap preserves temporal dependencies in time series data
        by sampling contiguous blocks rather than individual observations.

        Args:
            data: Original price data DataFrame
            seed: Random seed for reproducibility

        Returns:
            Bootstrap sample of price data
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        n_periods = len(data)
        min_periods = int(n_periods * self.min_data_fraction)

        # Handle short time series
        if n_periods < self.block_size:
            return self._simple_bootstrap_sample(data, min_periods)

        # Block bootstrap for longer series
        return self._block_bootstrap_sample(data, min_periods, n_periods)

    def _simple_bootstrap_sample(
        self, data: pl.DataFrame, target_size: int
    ) -> pl.DataFrame:
        """Simple bootstrap for short time series.

        Args:
            data: Original data
            target_size: Target sample size

        Returns:
            Bootstrap sample
        """
        n_periods = len(data)
        sample_size = max(target_size, int(n_periods * 0.8))
        indices = np.random.choice(n_periods, size=sample_size, replace=True)
        return data[sorted(indices)]

    def _block_bootstrap_sample(
        self, data: pl.DataFrame, min_periods: int, n_periods: int
    ) -> pl.DataFrame:
        """Block bootstrap for longer time series.

        Args:
            data: Original data
            min_periods: Minimum periods required
            n_periods: Total periods available

        Returns:
            Bootstrap sample
        """
        n_blocks = max(1, min_periods // self.block_size)
        sampled_data = []

        for _ in range(n_blocks):
            # Random starting point for block
            start_idx = np.random.randint(0, max(1, n_periods - self.block_size))
            end_idx = min(start_idx + self.block_size, n_periods)
            block = data[start_idx:end_idx]
            sampled_data.append(block)

        # Combine blocks
        bootstrap_sample = pl.concat(sampled_data)

        # Add additional sampling if needed
        current_size = len(bootstrap_sample)
        if current_size < min_periods:
            additional_needed = min_periods - current_size
            additional_indices = np.random.choice(
                n_periods, size=additional_needed, replace=True
            )
            additional_data = data[sorted(additional_indices)]
            bootstrap_sample = pl.concat([bootstrap_sample, additional_data])

        return bootstrap_sample.sort("Date")

    def parameter_noise_injection(
        self, short: int, long: int, noise_std: float = 0.1
    ) -> tuple[int, int]:
        """Add small random variations to parameters for robustness testing.

        Args:
            short: Fast period parameter
            long: Slow period parameter
            noise_std: Standard deviation for parameter perturbation

        Returns:
            Perturbed parameter values (short_noisy, long_noisy)
        """
        # Add Gaussian noise and ensure integer values
        short_noisy = max(2, int(short + np.random.normal(0, short * noise_std)))
        long_noisy = max(
            short_noisy + 1, int(long + np.random.normal(0, long * noise_std))
        )

        return short_noisy, long_noisy


def create_bootstrap_sampler(config_dict: dict) -> BootstrapSampler:
    """Create bootstrap sampler from configuration.

    Args:
        config_dict: Configuration dictionary

    Returns:
        Configured BootstrapSampler instance
    """
    block_size = config_dict.get("MC_BOOTSTRAP_BLOCK_SIZE", 63)
    min_data_fraction = config_dict.get("MC_MIN_DATA_FRACTION", 0.7)

    return BootstrapSampler(block_size=block_size, min_data_fraction=min_data_fraction)
