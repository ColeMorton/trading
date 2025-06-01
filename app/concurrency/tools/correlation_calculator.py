"""
Correlation calculator for portfolio risk analysis.

This module calculates pairwise correlations from aligned return series
using Polars operations, replacing hardcoded correlation assumptions
with actual calculated values from market data.
"""

import numpy as np
import polars as pl
from typing import Dict, List, Tuple, Optional, Any, Callable
import logging
from app.tools.exceptions import CovarianceMatrixError, DataAlignmentError

logger = logging.getLogger(__name__)


class CorrelationCalculator:
    """
    Calculates correlation matrices from aligned return series with robust handling
    of edge cases and comprehensive validation.
    """
    
    def __init__(self, log: Optional[Callable[[str, str], None]] = None):
        """
        Initialize the correlation calculator.
        
        Args:
            log: Optional logging function with signature (message, level)
        """
        self.log = log or self._default_log
    
    def _default_log(self, message: str, level: str) -> None:
        """Default logging implementation."""
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)
    
    def calculate_correlation_matrix(
        self,
        aligned_returns: pl.DataFrame,
        min_observations: int = 30
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Calculate correlation matrix from aligned return series.
        
        Args:
            aligned_returns: DataFrame with aligned return series (columns are strategies)
            min_observations: Minimum number of observations required
            
        Returns:
            Tuple of (correlation_matrix, diagnostics_dict)
            
        Raises:
            DataAlignmentError: If insufficient data
            CovarianceMatrixError: If correlation calculation fails
        """
        # Validate input
        if aligned_returns.height < min_observations:
            raise DataAlignmentError(
                f"Insufficient observations: {aligned_returns.height} < {min_observations} minimum"
            )
        
        # Get return columns (exclude Date column if present)
        return_columns = [col for col in aligned_returns.columns if col != "Date"]
        
        if len(return_columns) < 2:
            raise DataAlignmentError(
                f"Need at least 2 strategies for correlation, got {len(return_columns)}"
            )
        
        self.log(f"Calculating correlation matrix for {len(return_columns)} strategies", "info")
        
        # Convert to numpy for correlation calculation
        returns_array = aligned_returns.select(return_columns).to_numpy()
        
        # Check for invalid values
        if np.any(np.isnan(returns_array)):
            raise DataAlignmentError("NaN values found in return series")
        
        if np.any(np.isinf(returns_array)):
            raise DataAlignmentError("Infinite values found in return series")
        
        # Calculate correlation matrix
        try:
            correlation_matrix = np.corrcoef(returns_array.T)
        except Exception as e:
            raise CovarianceMatrixError(f"Failed to calculate correlation matrix: {str(e)}")
        
        # Validate correlation matrix
        diagnostics = self._validate_correlation_matrix(correlation_matrix, return_columns)
        
        self.log(f"Correlation matrix calculated successfully", "info")
        self._log_correlation_summary(correlation_matrix, return_columns)
        
        return correlation_matrix, diagnostics
    
    def _validate_correlation_matrix(
        self,
        corr_matrix: np.ndarray,
        strategy_names: List[str]
    ) -> Dict[str, Any]:
        """
        Validate correlation matrix and provide diagnostics.
        
        Args:
            corr_matrix: Correlation matrix to validate
            strategy_names: List of strategy names
            
        Returns:
            Dictionary of diagnostics
            
        Raises:
            CovarianceMatrixError: If validation fails
        """
        n_strategies = len(strategy_names)
        
        # Check shape
        if corr_matrix.shape != (n_strategies, n_strategies):
            raise CovarianceMatrixError(
                f"Invalid correlation matrix shape: {corr_matrix.shape} != ({n_strategies}, {n_strategies})"
            )
        
        # Check for NaN values
        if np.any(np.isnan(corr_matrix)):
            raise CovarianceMatrixError("Correlation matrix contains NaN values")
        
        # Check diagonal elements (should be 1)
        diagonal = np.diag(corr_matrix)
        if not np.allclose(diagonal, 1.0, rtol=1e-5):
            raise CovarianceMatrixError(
                f"Correlation matrix diagonal not all 1.0: {diagonal}"
            )
        
        # Check symmetry
        if not np.allclose(corr_matrix, corr_matrix.T, rtol=1e-5):
            raise CovarianceMatrixError("Correlation matrix is not symmetric")
        
        # Check bounds (-1 to 1)
        if np.any(corr_matrix < -1.0) or np.any(corr_matrix > 1.0):
            raise CovarianceMatrixError(
                f"Correlation values out of bounds [-1, 1]: min={np.min(corr_matrix)}, max={np.max(corr_matrix)}"
            )
        
        # Calculate diagnostics
        diagnostics = {
            "avg_correlation": float(np.mean(corr_matrix[np.triu_indices_from(corr_matrix, k=1)])),
            "max_correlation": float(np.max(corr_matrix[np.triu_indices_from(corr_matrix, k=1)])),
            "min_correlation": float(np.min(corr_matrix[np.triu_indices_from(corr_matrix, k=1)])),
            "condition_number": float(np.linalg.cond(corr_matrix)),
            "eigenvalues": np.linalg.eigvals(corr_matrix).tolist(),
            "is_positive_definite": bool(np.all(np.linalg.eigvals(corr_matrix) > 0))
        }
        
        # Warn about high correlations
        high_corr_threshold = 0.95
        high_corr_pairs = []
        for i in range(n_strategies):
            for j in range(i + 1, n_strategies):
                if abs(corr_matrix[i, j]) > high_corr_threshold:
                    high_corr_pairs.append({
                        "strategy1": strategy_names[i],
                        "strategy2": strategy_names[j],
                        "correlation": float(corr_matrix[i, j])
                    })
        
        if high_corr_pairs:
            self.log(
                f"Warning: {len(high_corr_pairs)} strategy pairs have correlation > {high_corr_threshold}",
                "warning"
            )
            diagnostics["high_correlation_pairs"] = high_corr_pairs
        
        return diagnostics
    
    def _log_correlation_summary(
        self,
        corr_matrix: np.ndarray,
        strategy_names: List[str]
    ) -> None:
        """Log summary statistics of correlation matrix."""
        # Get upper triangle (excluding diagonal)
        upper_triangle = corr_matrix[np.triu_indices_from(corr_matrix, k=1)]
        
        self.log(f"Correlation summary:", "info")
        self.log(f"  Average correlation: {np.mean(upper_triangle):.4f}", "info")
        self.log(f"  Median correlation: {np.median(upper_triangle):.4f}", "info")
        self.log(f"  Std dev of correlations: {np.std(upper_triangle):.4f}", "info")
        self.log(f"  Min correlation: {np.min(upper_triangle):.4f}", "info")
        self.log(f"  Max correlation: {np.max(upper_triangle):.4f}", "info")
    
    def calculate_covariance_matrix(
        self,
        aligned_returns: pl.DataFrame,
        volatilities: Optional[np.ndarray] = None,
        min_observations: int = 30
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Calculate covariance matrix from correlation matrix and volatilities.
        
        Args:
            aligned_returns: DataFrame with aligned return series
            volatilities: Optional pre-calculated volatilities (will calculate if not provided)
            min_observations: Minimum number of observations required
            
        Returns:
            Tuple of (covariance_matrix, diagnostics_dict)
            
        Raises:
            DataAlignmentError: If insufficient data
            CovarianceMatrixError: If calculation fails
        """
        # Calculate correlation matrix
        corr_matrix, corr_diagnostics = self.calculate_correlation_matrix(
            aligned_returns, min_observations
        )
        
        # Get return columns
        return_columns = [col for col in aligned_returns.columns if col != "Date"]
        
        # Calculate volatilities if not provided
        if volatilities is None:
            volatilities = self._calculate_volatilities(aligned_returns, return_columns)
        
        # Validate volatilities
        if len(volatilities) != len(return_columns):
            raise CovarianceMatrixError(
                f"Volatility count mismatch: {len(volatilities)} != {len(return_columns)}"
            )
        
        if np.any(volatilities <= 0):
            raise CovarianceMatrixError("All volatilities must be positive")
        
        # Convert correlation to covariance: Cov[i,j] = Corr[i,j] * Vol[i] * Vol[j]
        vol_outer = np.outer(volatilities, volatilities)
        cov_matrix = corr_matrix * vol_outer
        
        # Validate covariance matrix
        cov_diagnostics = self._validate_covariance_matrix(cov_matrix, volatilities)
        
        # Combine diagnostics
        diagnostics = {
            "correlation": corr_diagnostics,
            "covariance": cov_diagnostics,
            "volatilities": volatilities.tolist()
        }
        
        self.log("Covariance matrix calculated successfully", "info")
        
        return cov_matrix, diagnostics
    
    def _calculate_volatilities(
        self,
        aligned_returns: pl.DataFrame,
        return_columns: List[str]
    ) -> np.ndarray:
        """Calculate volatilities for each strategy."""
        volatilities = []
        
        for col in return_columns:
            returns = aligned_returns[col].to_numpy()
            vol = np.std(returns)
            volatilities.append(vol)
            self.log(f"Strategy {col} volatility: {vol:.6f}", "info")
        
        return np.array(volatilities)
    
    def _validate_covariance_matrix(
        self,
        cov_matrix: np.ndarray,
        volatilities: np.ndarray
    ) -> Dict[str, Any]:
        """
        Validate covariance matrix.
        
        Args:
            cov_matrix: Covariance matrix to validate
            volatilities: Strategy volatilities
            
        Returns:
            Dictionary of diagnostics
            
        Raises:
            CovarianceMatrixError: If validation fails
        """
        # Check for NaN values
        if np.any(np.isnan(cov_matrix)):
            raise CovarianceMatrixError("Covariance matrix contains NaN values")
        
        # Check symmetry
        if not np.allclose(cov_matrix, cov_matrix.T, rtol=1e-5):
            raise CovarianceMatrixError("Covariance matrix is not symmetric")
        
        # Check positive definiteness
        eigenvalues = np.linalg.eigvals(cov_matrix)
        min_eigenvalue = np.min(eigenvalues)
        
        if min_eigenvalue <= 0:
            self.log(
                f"Warning: Covariance matrix not positive definite (min eigenvalue: {min_eigenvalue:.6f})",
                "warning"
            )
        
        # Check diagonal elements match variance
        diagonal_variances = np.diag(cov_matrix)
        expected_variances = volatilities ** 2
        
        if not np.allclose(diagonal_variances, expected_variances, rtol=1e-5):
            self.log(
                "Warning: Diagonal elements don't match expected variances",
                "warning"
            )
        
        diagnostics = {
            "condition_number": float(np.linalg.cond(cov_matrix)),
            "min_eigenvalue": float(min_eigenvalue),
            "max_eigenvalue": float(np.max(eigenvalues)),
            "is_positive_definite": bool(min_eigenvalue > 0),
            "trace": float(np.trace(cov_matrix)),
            "determinant": float(np.linalg.det(cov_matrix))
        }
        
        return diagnostics
    
    def apply_shrinkage_estimator(
        self,
        sample_cov: np.ndarray,
        shrinkage_target: str = "diagonal",
        shrinkage_intensity: Optional[float] = None
    ) -> Tuple[np.ndarray, float]:
        """
        Apply shrinkage to covariance matrix for improved estimation with small samples.
        
        Implements Ledoit-Wolf shrinkage estimator which combines the sample
        covariance matrix with a structured estimator (target).
        
        Args:
            sample_cov: Sample covariance matrix
            shrinkage_target: Target matrix type ("diagonal", "identity", "constant_correlation")
            shrinkage_intensity: Shrinkage parameter (0 to 1), auto-calculated if None
            
        Returns:
            Tuple of (shrunk_covariance_matrix, shrinkage_intensity_used)
            
        Raises:
            CovarianceMatrixError: If shrinkage fails
        """
        n = sample_cov.shape[0]
        
        # Create shrinkage target
        if shrinkage_target == "diagonal":
            # Target is diagonal matrix with sample variances
            target = np.diag(np.diag(sample_cov))
        elif shrinkage_target == "identity":
            # Target is scaled identity matrix
            target = np.eye(n) * np.trace(sample_cov) / n
        elif shrinkage_target == "constant_correlation":
            # Target assumes all correlations are equal to average
            variances = np.diag(sample_cov)
            avg_corr = self._calculate_average_correlation(sample_cov)
            target = np.outer(np.sqrt(variances), np.sqrt(variances)) * avg_corr
            np.fill_diagonal(target, variances)
        else:
            raise CovarianceMatrixError(f"Unknown shrinkage target: {shrinkage_target}")
        
        # Calculate optimal shrinkage intensity if not provided
        if shrinkage_intensity is None:
            shrinkage_intensity = self._calculate_optimal_shrinkage(sample_cov, target)
        
        # Validate shrinkage intensity
        if not 0 <= shrinkage_intensity <= 1:
            raise CovarianceMatrixError(
                f"Shrinkage intensity must be in [0, 1], got {shrinkage_intensity}"
            )
        
        # Apply shrinkage: S* = (1 - λ) * S + λ * T
        shrunk_cov = (1 - shrinkage_intensity) * sample_cov + shrinkage_intensity * target
        
        # Ensure positive definiteness
        min_eigenvalue = np.min(np.linalg.eigvals(shrunk_cov))
        if min_eigenvalue <= 0:
            self.log(
                f"Regularizing shrunk covariance matrix (min eigenvalue: {min_eigenvalue:.6f})",
                "warning"
            )
            shrunk_cov = self._regularize_covariance(shrunk_cov)
        
        self.log(
            f"Applied {shrinkage_target} shrinkage with intensity {shrinkage_intensity:.4f}",
            "info"
        )
        
        return shrunk_cov, shrinkage_intensity
    
    def _calculate_average_correlation(self, cov_matrix: np.ndarray) -> float:
        """Calculate average correlation from covariance matrix."""
        # Convert to correlation
        volatilities = np.sqrt(np.diag(cov_matrix))
        corr_matrix = cov_matrix / np.outer(volatilities, volatilities)
        
        # Get average of off-diagonal elements
        n = corr_matrix.shape[0]
        off_diagonal_sum = np.sum(corr_matrix) - n  # Subtract diagonal
        avg_correlation = off_diagonal_sum / (n * (n - 1))
        
        return avg_correlation
    
    def _calculate_optimal_shrinkage(
        self,
        sample_cov: np.ndarray,
        target: np.ndarray
    ) -> float:
        """
        Calculate optimal shrinkage intensity using Ledoit-Wolf method.
        
        This is a simplified version that works well in practice.
        """
        n = sample_cov.shape[0]
        
        # Calculate Frobenius norms
        # ||S - T||^2_F
        diff = sample_cov - target
        numerator = np.sum(diff ** 2)
        
        # ||S||^2_F
        denominator = np.sum(sample_cov ** 2)
        
        if denominator == 0:
            return 0.0
        
        # Simple shrinkage estimate
        shrinkage = numerator / denominator
        
        # Bound between 0 and 1
        shrinkage = max(0.0, min(1.0, shrinkage))
        
        # Apply sample size adjustment
        sample_size_factor = min(1.0, 30.0 / n)  # Less shrinkage for larger samples
        shrinkage *= sample_size_factor
        
        return shrinkage
    
    def _regularize_covariance(
        self,
        cov_matrix: np.ndarray,
        min_eigenvalue: float = 1e-6
    ) -> np.ndarray:
        """
        Regularize covariance matrix to ensure positive definiteness.
        
        Args:
            cov_matrix: Covariance matrix to regularize
            min_eigenvalue: Minimum eigenvalue to enforce
            
        Returns:
            Regularized covariance matrix
        """
        # Eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
        
        # Clip eigenvalues
        eigenvalues = np.maximum(eigenvalues, min_eigenvalue)
        
        # Reconstruct matrix
        regularized = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
        
        # Ensure symmetry (numerical errors can break it)
        regularized = (regularized + regularized.T) / 2
        
        return regularized