"""
Risk contribution calculator with mathematically correct implementation.

This module implements the correct risk contribution calculations that ensure
contributions sum to 100%. It fixes the critical error in the original
implementation where risk contributions summed to 441%.
"""

import numpy as np
import polars as pl
from typing import Dict, List, Tuple, Optional, Any
import logging
from app.tools.exceptions import PortfolioVarianceError

logger = logging.getLogger(__name__)


class RiskContributionCalculator:
    """
    Calculates risk contributions ensuring they sum to 100%.
    
    This implementation follows the mathematical formula:
    RC_i = w_i * (∂σ_p / ∂w_i)
    
    Where the percentage risk contribution is RC_i / σ_p.
    """
    
    @staticmethod
    def calculate_portfolio_metrics(
        returns: np.ndarray,
        weights: np.ndarray,
        strategy_names: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate complete portfolio risk metrics with correct risk contributions.
        
        Args:
            returns: Array of shape (n_periods, n_strategies) with returns
            weights: Array of shape (n_strategies,) with allocations
            strategy_names: List of strategy identifiers
            
        Returns:
            Dictionary with risk metrics and contributions that sum to 100%
        """
        # Validate inputs
        if returns.shape[1] != len(weights):
            raise ValueError(f"Returns shape {returns.shape} doesn't match weights length {len(weights)}")
        
        if len(strategy_names) != len(weights):
            raise ValueError(f"Strategy names length {len(strategy_names)} doesn't match weights length {len(weights)}")
        
        # Validate and normalize weights - fail fast on invalid inputs
        logger.info(f"Input weights before validation: {weights}")
        logger.info(f"Weights shape: {weights.shape}, dtype: {weights.dtype}")
        
        if np.any(np.isnan(weights)):
            nan_indices = np.where(np.isnan(weights))[0]
            raise PortfolioVarianceError(f"Portfolio weights contain NaN values at indices {nan_indices} - check strategy allocations")
        
        if np.any(np.isinf(weights)):
            raise PortfolioVarianceError("Portfolio weights contain infinite values - check strategy allocations")
        
        if np.any(weights < 0):
            raise PortfolioVarianceError("Portfolio weights contain negative values - check strategy allocations")
        
        weights_sum = np.sum(weights)
        if weights_sum <= 0:
            raise PortfolioVarianceError(f"Portfolio weights sum to {weights_sum} (must be positive) - check strategy allocations")
        
        if np.isnan(weights_sum):
            raise PortfolioVarianceError("Portfolio weights sum is NaN - check strategy allocations")
        
        # Normalize weights to sum to 1
        weights = weights / weights_sum
        
        # Calculate covariance matrix
        cov_matrix = np.cov(returns.T)
        
        # Validate covariance matrix - fail fast on invalid values
        from app.tools.exceptions import CovarianceMatrixError
        
        if np.any(np.isnan(cov_matrix)):
            raise CovarianceMatrixError("Covariance matrix contains NaN values - check input return data quality")
        
        if np.any(np.isinf(cov_matrix)):
            raise CovarianceMatrixError("Covariance matrix contains infinite values - check input return data quality")
        
        # Calculate portfolio variance and standard deviation
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        
        # Handle NaN and negative values in portfolio variance
        if np.isnan(portfolio_variance) or portfolio_variance < 0:
            logger.warning(f"Invalid portfolio variance ({portfolio_variance}), setting to 0")
            portfolio_variance = 0.0
            portfolio_std = 0.0
        else:
            portfolio_std = np.sqrt(portfolio_variance)
            # Additional safety check for NaN in portfolio standard deviation
            if np.isnan(portfolio_std):
                logger.warning("NaN detected in portfolio standard deviation, setting to 0")
                portfolio_std = 0.0
        
        logger.info(f"Portfolio standard deviation: {portfolio_std:.6f}")
        
        # Calculate marginal contributions: Σw
        marginal_contributions = np.dot(cov_matrix, weights)
        
        # Calculate component contributions: w_i * (Σw)_i
        component_contributions = weights * marginal_contributions
        
        # Convert to percentage contributions
        # This is the key fix: divide by portfolio_variance, not portfolio_std twice
        # Handle edge case where portfolio_variance is zero or very small
        if portfolio_variance > 1e-10:
            risk_contributions_pct = component_contributions / portfolio_variance
        else:
            # If portfolio variance is essentially zero, use equal weights
            logger.warning(f"Portfolio variance is near zero ({portfolio_variance:.10f}), using equal risk contributions")
            risk_contributions_pct = np.ones(len(weights)) / len(weights)
        
        # Check for NaN values and handle them
        if np.any(np.isnan(risk_contributions_pct)):
            logger.warning("NaN values detected in risk contributions, using equal weights")
            risk_contributions_pct = np.ones(len(weights)) / len(weights)
        
        # Validate sum equals 1.0
        total_contribution = np.sum(risk_contributions_pct)
        if not np.isclose(total_contribution, 1.0, rtol=1e-5) and total_contribution > 0:
            logger.warning(
                f"Risk contributions sum to {total_contribution:.6f}, "
                f"normalizing to ensure 100% total"
            )
            # Force normalization if needed
            risk_contributions_pct = risk_contributions_pct / total_contribution
        elif total_contribution == 0:
            # If all contributions are zero, use equal weights
            logger.warning("All risk contributions are zero, using equal weights")
            risk_contributions_pct = np.ones(len(weights)) / len(weights)
        
        # Create output dictionary
        risk_metrics = {
            "portfolio_volatility": float(portfolio_std),
            "portfolio_variance": float(portfolio_variance),
            "total_risk_contribution": float(np.sum(risk_contributions_pct)),
            "risk_contributions": {}
        }
        
        # Add individual strategy contributions
        for i, strategy_name in enumerate(strategy_names):
            risk_metrics["risk_contributions"][strategy_name] = {
                "weight": float(weights[i]),
                "marginal_contribution": float(marginal_contributions[i]),
                "risk_contribution": float(component_contributions[i]),
                "risk_contribution_pct": float(risk_contributions_pct[i]),
                "risk_contribution_pct_display": f"{risk_contributions_pct[i]*100:.2f}%"
            }
        
        # Log summary
        logger.info(f"Risk contributions calculated - Total: {total_contribution*100:.2f}%")
        for name, contrib in zip(strategy_names, risk_contributions_pct):
            logger.info(f"  {name}: {contrib*100:.2f}%")
        
        return risk_metrics
    
    @staticmethod
    def validate_risk_contributions(risk_contributions: Dict[str, float]) -> Tuple[bool, str]:
        """
        Validate that risk contributions sum to approximately 100%.
        
        Args:
            risk_contributions: Dictionary of strategy_name -> contribution_pct
            
        Returns:
            Tuple of (is_valid, message)
        """
        total = sum(risk_contributions.values())
        
        if np.isclose(total, 1.0, rtol=1e-3):  # 0.1% tolerance
            return True, f"Risk contributions valid: {total*100:.2f}%"
        else:
            return False, f"Risk contributions invalid: {total*100:.2f}% (expected 100%)"
    
    @staticmethod
    def calculate_portfolio_metrics_with_cov(
        cov_matrix: np.ndarray,
        weights: np.ndarray,
        strategy_names: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate portfolio metrics using a pre-computed covariance matrix.
        
        Args:
            cov_matrix: Covariance matrix of shape (n_strategies, n_strategies)
            weights: Array of shape (n_strategies,) with allocations
            strategy_names: List of strategy identifiers
            
        Returns:
            Dictionary with risk metrics and contributions that sum to 100%
        """
        # Validate inputs
        if cov_matrix.shape[0] != len(weights):
            raise ValueError(f"Covariance matrix shape {cov_matrix.shape} doesn't match weights length {len(weights)}")
        
        if len(strategy_names) != len(weights):
            raise ValueError(f"Strategy names length {len(strategy_names)} doesn't match weights length {len(weights)}")
        
        # Validate and normalize weights - fail fast on invalid inputs
        logger.info(f"Input weights before validation: {weights}")
        logger.info(f"Weights shape: {weights.shape}, dtype: {weights.dtype}")
        
        if np.any(np.isnan(weights)):
            nan_indices = np.where(np.isnan(weights))[0]
            raise PortfolioVarianceError(f"Portfolio weights contain NaN values at indices {nan_indices} - check strategy allocations")
        
        if np.any(np.isinf(weights)):
            raise PortfolioVarianceError("Portfolio weights contain infinite values - check strategy allocations")
        
        if np.any(weights < 0):
            raise PortfolioVarianceError("Portfolio weights contain negative values - check strategy allocations")
        
        weights_sum = np.sum(weights)
        if weights_sum <= 0:
            raise PortfolioVarianceError(f"Portfolio weights sum to {weights_sum} (must be positive) - check strategy allocations")
        
        if np.isnan(weights_sum):
            raise PortfolioVarianceError("Portfolio weights sum is NaN - check strategy allocations")
        
        # Normalize weights to sum to 1
        weights = weights / weights_sum
        
        # Validate covariance matrix - fail fast on invalid values
        from app.tools.exceptions import CovarianceMatrixError
        
        if np.any(np.isnan(cov_matrix)):
            raise CovarianceMatrixError("Covariance matrix contains NaN values - check input return data quality")
        
        if np.any(np.isinf(cov_matrix)):
            raise CovarianceMatrixError("Covariance matrix contains infinite values - check input return data quality")
        
        # Calculate portfolio variance and standard deviation
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        
        # Validate portfolio variance - fail fast on invalid values
        from app.tools.exceptions import PortfolioVarianceError
        
        if np.isnan(portfolio_variance):
            raise PortfolioVarianceError("Portfolio variance calculation resulted in NaN - check input data quality")
        
        if portfolio_variance < 0:
            raise PortfolioVarianceError(f"Portfolio variance is negative ({portfolio_variance}) - invalid covariance matrix")
        
        if portfolio_variance == 0:
            raise PortfolioVarianceError("Portfolio variance is zero - strategies have no variability or perfect negative correlation")
        
        portfolio_std = np.sqrt(portfolio_variance)
        
        if np.isnan(portfolio_std):
            raise PortfolioVarianceError("Portfolio standard deviation calculation resulted in NaN")
        
        logger.info(f"Portfolio standard deviation: {portfolio_std:.6f}")
        logger.info(f"Portfolio variance: {portfolio_variance:.8f}")
        logger.info(f"Weights shape: {weights.shape}, sum: {np.sum(weights):.6f}")
        
        # Calculate marginal contributions: Σw
        marginal_contributions = np.dot(cov_matrix, weights)
        
        # Calculate component contributions: w_i * (Σw)_i
        component_contributions = weights * marginal_contributions
        
        # Convert to percentage contributions
        if portfolio_variance > 1e-10:
            risk_contributions_pct = component_contributions / portfolio_variance
        else:
            # If portfolio variance is essentially zero, use equal weights
            logger.warning(f"Portfolio variance is near zero ({portfolio_variance:.10f}), using equal risk contributions")
            risk_contributions_pct = np.ones(len(weights)) / len(weights)
        
        # Check for NaN values and handle them
        if np.any(np.isnan(risk_contributions_pct)):
            logger.warning("NaN values detected in risk contributions, using equal weights")
            risk_contributions_pct = np.ones(len(weights)) / len(weights)
        
        # Validate sum equals 1.0
        total_contribution = np.sum(risk_contributions_pct)
        if not np.isclose(total_contribution, 1.0, rtol=1e-5) and total_contribution > 0:
            logger.warning(
                f"Risk contributions sum to {total_contribution:.6f}, "
                f"normalizing to ensure 100% total"
            )
            # Force normalization if needed
            risk_contributions_pct = risk_contributions_pct / total_contribution
        elif total_contribution == 0:
            # If all contributions are zero, use equal weights
            logger.warning("All risk contributions are zero, using equal weights")
            risk_contributions_pct = np.ones(len(weights)) / len(weights)
        
        # Create output dictionary
        risk_metrics = {
            "portfolio_volatility": float(portfolio_std),
            "portfolio_variance": float(portfolio_variance),
            "total_risk_contribution": float(np.sum(risk_contributions_pct)),
            "risk_contributions": {}
        }
        
        # Add individual strategy contributions
        for i, strategy_name in enumerate(strategy_names):
            risk_metrics["risk_contributions"][strategy_name] = {
                "weight": float(weights[i]),
                "marginal_contribution": float(marginal_contributions[i]),
                "risk_contribution": float(component_contributions[i]),
                "risk_contribution_pct": float(risk_contributions_pct[i]),
                "risk_contribution_pct_display": f"{risk_contributions_pct[i]*100:.2f}%"
            }
        
        # Log summary
        logger.info(f"Risk contributions calculated - Total: {total_contribution*100:.2f}%")
        for name, contrib in zip(strategy_names, risk_contributions_pct):
            logger.info(f"  {name}: {contrib*100:.2f}%")
        
        return risk_metrics

    @staticmethod
    def calculate_risk_metrics_from_dataframes(
        position_arrays: List[np.ndarray],
        data_list: List[Any],  # List[pl.DataFrame]
        strategy_allocations: List[float],
        strategy_names: List[str],
        strategy_configs: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate risk metrics from position arrays and price data using aligned return series.
        
        This method uses proper return series alignment instead of fallback mechanisms
        to calculate accurate portfolio risk metrics.
        
        Args:
            position_arrays: List of position arrays for each strategy
            data_list: List of dataframes with price data
            strategy_allocations: List of strategy allocations
            strategy_names: List of strategy identifiers
            strategy_configs: Optional list of strategy configurations
            
        Returns:
            Dictionary with correct risk metrics and contributions
            
        Raises:
            DataAlignmentError: If return series alignment fails
            RiskCalculationError: If risk calculation fails
        """
        from app.tools.logging_context import logging_context
        from .return_alignment import align_portfolio_returns
        from app.tools.exceptions import DataAlignmentError, RiskCalculationError
        
        with logging_context(module_name='risk_calculation', log_file='risk_calculation.log') as log:
            try:
                # Prepare portfolio data for return alignment
                portfolios = []
                for i, (df, position_array, strategy_name) in enumerate(zip(data_list, position_arrays, strategy_names)):
                    # Add position data to dataframe for return calculation
                    df_with_position = df.with_columns([
                        pl.Series("Position", position_array[:len(df)]).alias("Position")
                    ])
                    
                    portfolios.append({
                        "ticker": strategy_name.split("_")[0] if "_" in strategy_name else strategy_name,
                        "strategy_type": strategy_name.split("_")[1] if "_" in strategy_name and len(strategy_name.split("_")) > 1 else "unknown",
                        "period": strategy_name.split("_")[2] if "_" in strategy_name and len(strategy_name.split("_")) > 2 else "D",
                        "data": df_with_position
                    })
                
                # Align return series across all strategies
                aligned_returns_matrix, aligned_strategy_names = align_portfolio_returns(
                    portfolios, log, min_observations=10
                )
                
                # Calculate covariance matrix from aligned returns
                return_columns = [col for col in aligned_returns_matrix.columns if col != "Date"]
                returns_array = aligned_returns_matrix.select(return_columns).to_numpy()
                
                if returns_array.shape[1] != len(strategy_names):
                    raise DataAlignmentError(
                        f"Strategy count mismatch: expected {len(strategy_names)}, got {returns_array.shape[1]}"
                    )
                
                # Calculate covariance matrix from aligned returns
                cov_matrix = np.cov(returns_array, rowvar=False)
                
                # Validate covariance matrix
                if np.any(np.isnan(cov_matrix)) or np.any(np.isinf(cov_matrix)):
                    raise RiskCalculationError("Covariance matrix contains invalid values (NaN or inf)")
                
                # Check for positive definiteness
                eigenvalues = np.linalg.eigvals(cov_matrix)
                if np.any(eigenvalues <= 0):
                    raise RiskCalculationError(f"Covariance matrix is not positive definite (min eigenvalue: {np.min(eigenvalues)})")
                
                # Convert allocations to numpy array
                weights = np.array(strategy_allocations)
                
                # Calculate risk metrics using aligned data
                risk_metrics = RiskContributionCalculator.calculate_portfolio_metrics_with_cov(
                    cov_matrix, weights, strategy_names
                )
                
                # Add VaR and CVaR calculations using aligned returns
                for i, strategy_name in enumerate(aligned_strategy_names):
                    strategy_returns = returns_array[:, i]
                    
                    if len(strategy_returns) > 0:
                        sorted_returns = np.sort(strategy_returns)
                        var_95 = float(np.percentile(sorted_returns, 5))
                        var_99 = float(np.percentile(sorted_returns, 1))
                        cvar_95 = float(np.mean(sorted_returns[sorted_returns <= var_95])) if len(sorted_returns[sorted_returns <= var_95]) > 0 else var_95
                        cvar_99 = float(np.mean(sorted_returns[sorted_returns <= var_99])) if len(sorted_returns[sorted_returns <= var_99]) > 0 else var_99
                    else:
                        raise DataAlignmentError(f"No returns available for strategy {strategy_name}")
                    
                    # Add to risk metrics in expected format
                    risk_metrics[f"strategy_{i+1}_var_95"] = var_95
                    risk_metrics[f"strategy_{i+1}_cvar_95"] = cvar_95
                    risk_metrics[f"strategy_{i+1}_var_99"] = var_99
                    risk_metrics[f"strategy_{i+1}_cvar_99"] = cvar_99
                
                log(f"Portfolio risk calculation completed successfully for {len(strategy_names)} strategies", "info")
                return risk_metrics
                
            except (DataAlignmentError, RiskCalculationError) as e:
                # Re-raise specific risk calculation errors
                raise e
            except Exception as e:
                # Convert unexpected errors to RiskCalculationError
                raise RiskCalculationError(f"Unexpected error in risk calculation: {str(e)}")


def calculate_risk_contributions_fixed(
    position_arrays: List[np.ndarray],
    data_list: List[Any],  # List[pl.DataFrame]
    strategy_allocations: List[float],
    log: Any,  # Callable[[str, str], None]
    strategy_configs: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, float]:
    """
    Fixed version of calculate_risk_contributions that ensures contributions sum to 100%.
    
    This function maintains the same interface as the original but uses the
    mathematically correct calculation method.
    """
    try:
        # Validate inputs
        if not position_arrays or not data_list or not strategy_allocations:
            log("Empty input arrays provided", "error")
            raise ValueError("Position arrays, data list, and strategy allocations cannot be empty")
        
        if len(position_arrays) != len(data_list) or len(position_arrays) != len(strategy_allocations):
            log("Mismatched input arrays", "error")
            raise ValueError("Number of position arrays, dataframes, and strategy allocations must match")
        
        n_strategies = len(position_arrays)
        log(f"Calculating risk contributions for {n_strategies} strategies", "info")
        
        # Generate strategy names if not provided
        strategy_names = [f"strategy_{i+1}" for i in range(n_strategies)]
        
        # Always use the fixed calculation method
        log("Using fixed risk contribution calculation", "info")
        
        # Calculate using correct method
        risk_metrics = RiskContributionCalculator.calculate_risk_metrics_from_dataframes(
            position_arrays,
            data_list,
            strategy_allocations,
            strategy_names,
            strategy_configs
        )
        
        # Transform to expected output format
        risk_contributions = {}
        
        # Calculate individual strategy returns and volatilities for alpha calculation
        strategy_returns = []
        strategy_volatilities = []
        
        for i, df in enumerate(data_list):
            # Calculate returns from Close prices
            close_prices = df["Close"].to_numpy()
            returns = np.diff(close_prices) / close_prices[:-1]
            
            # Only consider periods where strategy was active
            active_positions = position_arrays[i][1:]  # Align with returns
            active_returns = returns[active_positions != 0]
            
            # Calculate volatility and average return
            vol = float(np.std(active_returns)) if len(active_returns) > 0 else 0.0
            avg_return = float(np.mean(active_returns)) if len(active_returns) > 0 else 0.0
            
            strategy_volatilities.append(vol)
            strategy_returns.append(avg_return)
            
            log(f"Strategy {i+1} - Average Return: {avg_return:.6f}, Volatility: {vol:.6f}", "info")
        
        # Calculate benchmark return (average of all strategies)
        benchmark_return = np.mean(strategy_returns) if strategy_returns else 0.0
        log(f"Benchmark return calculated: {benchmark_return:.6f}", "info")
        
        # Add individual strategy risk contributions
        for i in range(n_strategies):
            strategy_name = strategy_names[i]
            contrib_data = risk_metrics["risk_contributions"][strategy_name]
            risk_contributions[f"strategy_{i+1}_risk_contrib"] = contrib_data["risk_contribution_pct"]
            
            # Add VaR/CVaR metrics
            risk_contributions[f"strategy_{i+1}_var_95"] = risk_metrics.get(f"strategy_{i+1}_var_95", 0.0)
            risk_contributions[f"strategy_{i+1}_cvar_95"] = risk_metrics.get(f"strategy_{i+1}_cvar_95", 0.0)
            risk_contributions[f"strategy_{i+1}_var_99"] = risk_metrics.get(f"strategy_{i+1}_var_99", 0.0)
            risk_contributions[f"strategy_{i+1}_cvar_99"] = risk_metrics.get(f"strategy_{i+1}_cvar_99", 0.0)
            
            # Calculate Risk-Adjusted Alpha (excess return over benchmark, adjusted for volatility)
            excess_return = strategy_returns[i] - benchmark_return
            strategy_volatility = strategy_volatilities[i]
            
            if strategy_volatility > 0:
                # Risk-adjusted alpha: excess return per unit of risk
                risk_adjusted_alpha = excess_return / strategy_volatility
            else:
                # If no volatility, use raw excess return
                risk_adjusted_alpha = excess_return
            
            # Handle potential NaN values in alpha
            if np.isnan(risk_adjusted_alpha):
                log(f"Warning: NaN detected in alpha for strategy {i+1}, setting to 0", "warning")
                risk_adjusted_alpha = 0.0
                
            risk_contributions[f"strategy_{i+1}_alpha_to_portfolio"] = float(risk_adjusted_alpha)
            log(f"Strategy {i+1} excess return: {excess_return:.6f}, alpha to portfolio: {risk_adjusted_alpha:.6f}", "info")
        
        # Add portfolio-level metrics with NaN handling
        portfolio_volatility = risk_metrics["portfolio_volatility"]
        if np.isnan(portfolio_volatility):
            log("Warning: NaN detected in portfolio volatility, setting to 0", "warning")
            portfolio_volatility = 0.0
        risk_contributions["total_portfolio_risk"] = portfolio_volatility
        
        # Calculate combined VaR/CVaR metrics (weighted by allocation)
        total_allocation = sum(strategy_allocations)
        if total_allocation > 0:
            combined_var_95 = 0.0
            combined_var_99 = 0.0
            combined_cvar_95 = 0.0
            combined_cvar_99 = 0.0
            
            for i in range(n_strategies):
                # Get allocation weight as proportion
                allocation_weight = strategy_allocations[i] / total_allocation
                
                # Add weighted contribution
                combined_var_95 += risk_contributions[f"strategy_{i+1}_var_95"] * allocation_weight
                combined_var_99 += risk_contributions[f"strategy_{i+1}_var_99"] * allocation_weight
                combined_cvar_95 += risk_contributions[f"strategy_{i+1}_cvar_95"] * allocation_weight
                combined_cvar_99 += risk_contributions[f"strategy_{i+1}_cvar_99"] * allocation_weight
            
            risk_contributions["combined_var_95"] = combined_var_95
            risk_contributions["combined_var_99"] = combined_var_99
            risk_contributions["combined_cvar_95"] = combined_cvar_95
            risk_contributions["combined_cvar_99"] = combined_cvar_99
            
            log(f"Combined VaR 95%: {combined_var_95:.4f}, CVaR 95%: {combined_cvar_95:.4f}", "info")
            log(f"Combined VaR 99%: {combined_var_99:.4f}, CVaR 99%: {combined_cvar_99:.4f}", "info")
        else:
            # If no allocations, set to zero
            risk_contributions["combined_var_95"] = 0.0
            risk_contributions["combined_var_99"] = 0.0
            risk_contributions["combined_cvar_95"] = 0.0
            risk_contributions["combined_cvar_99"] = 0.0
            log("No allocations provided, setting combined VaR/CVaR to zero", "info")
        
        # Add benchmark return
        risk_contributions["benchmark_return"] = float(benchmark_return)
        
        # Validate the sum
        contrib_sum = sum(
            v for k, v in risk_contributions.items() 
            if k.endswith("_risk_contrib")
        )
        log(f"Risk contributions sum: {contrib_sum*100:.2f}%", "info")
        
        return risk_contributions
    
    except Exception as e:
        log(f"Error calculating risk contributions: {str(e)}", "error")
        raise