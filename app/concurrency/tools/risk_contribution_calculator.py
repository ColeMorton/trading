"""
Risk contribution calculator with mathematically correct implementation.

This module implements the correct risk contribution calculations that ensure
contributions sum to 100%. It fixes the critical error in the original
implementation where risk contributions summed to 441%.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
import os

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
        
        # Ensure weights sum to 1
        weights = weights / np.sum(weights)
        
        # Calculate covariance matrix
        cov_matrix = np.cov(returns.T)
        
        # Calculate portfolio variance and standard deviation
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        portfolio_std = np.sqrt(portfolio_variance)
        
        logger.info(f"Portfolio standard deviation: {portfolio_std:.6f}")
        
        # Calculate marginal contributions: Σw
        marginal_contributions = np.dot(cov_matrix, weights)
        
        # Calculate component contributions: w_i * (Σw)_i
        component_contributions = weights * marginal_contributions
        
        # Convert to percentage contributions
        # This is the key fix: divide by portfolio_variance, not portfolio_std twice
        risk_contributions_pct = component_contributions / portfolio_variance
        
        # Validate sum equals 1.0
        total_contribution = np.sum(risk_contributions_pct)
        if not np.isclose(total_contribution, 1.0, rtol=1e-5):
            logger.warning(
                f"Risk contributions sum to {total_contribution:.6f}, "
                f"normalizing to ensure 100% total"
            )
            # Force normalization if needed
            risk_contributions_pct = risk_contributions_pct / total_contribution
        
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
    def calculate_risk_metrics_from_dataframes(
        position_arrays: List[np.ndarray],
        data_list: List[Any],  # List[pl.DataFrame]
        strategy_allocations: List[float],
        strategy_names: List[str],
        strategy_configs: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate risk metrics from position arrays and price data.
        
        This method bridges the gap between the existing data format and
        the new correct calculation method.
        
        Args:
            position_arrays: List of position arrays for each strategy
            data_list: List of dataframes with price data
            strategy_allocations: List of strategy allocations
            strategy_names: List of strategy identifiers
            strategy_configs: Optional list of strategy configurations
            
        Returns:
            Dictionary with correct risk metrics and contributions
        """
        # Extract returns from dataframes
        n_strategies = len(position_arrays)
        all_returns = []
        
        for i, df in enumerate(data_list):
            # Calculate returns from Close prices
            close_prices = df["Close"].to_numpy()
            returns = np.diff(close_prices) / close_prices[:-1]
            
            # Only consider periods where strategy was active
            active_positions = position_arrays[i][1:]  # Align with returns
            
            # For risk contribution, we need full return series (not just active)
            # but we'll weight by positions
            all_returns.append(returns)
        
        # Find common length (minimum)
        min_length = min(len(r) for r in all_returns)
        
        # Create return matrix
        return_matrix = np.zeros((min_length, n_strategies))
        for i, returns in enumerate(all_returns):
            return_matrix[:, i] = returns[:min_length]
        
        # Convert allocations to numpy array
        weights = np.array(strategy_allocations)
        
        # Calculate risk metrics using correct method
        risk_metrics = RiskContributionCalculator.calculate_portfolio_metrics(
            return_matrix, weights, strategy_names
        )
        
        # Add VaR and CVaR calculations for compatibility
        for i in range(n_strategies):
            strategy_returns = return_matrix[:, i]
            active_positions = position_arrays[i][1:min_length+1]
            active_returns = strategy_returns[active_positions != 0]
            
            if len(active_returns) > 0:
                sorted_returns = np.sort(active_returns)
                var_95 = float(np.percentile(sorted_returns, 5))
                var_99 = float(np.percentile(sorted_returns, 1))
                cvar_95 = float(np.mean(sorted_returns[sorted_returns <= var_95]))
                cvar_99 = float(np.mean(sorted_returns[sorted_returns <= var_99]))
            else:
                var_95 = var_99 = cvar_95 = cvar_99 = 0.0
            
            # Add to risk metrics in expected format
            risk_metrics[f"strategy_{i+1}_var_95"] = var_95
            risk_metrics[f"strategy_{i+1}_cvar_95"] = cvar_95
            risk_metrics[f"strategy_{i+1}_var_99"] = var_99
            risk_metrics[f"strategy_{i+1}_cvar_99"] = cvar_99
        
        return risk_metrics


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
        
        # Use feature flag to determine which implementation to use
        use_fixed_calc = os.getenv("USE_FIXED_RISK_CALC", "false").lower() == "true"
        
        if use_fixed_calc:
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
            
            # Add portfolio-level metrics
            risk_contributions["total_portfolio_risk"] = risk_metrics["portfolio_volatility"]
            
            # Validate the sum
            contrib_sum = sum(
                v for k, v in risk_contributions.items() 
                if k.endswith("_risk_contrib")
            )
            log(f"Risk contributions sum: {contrib_sum*100:.2f}%", "info")
            
            return risk_contributions
            
        else:
            log("Using legacy risk contribution calculation", "warning")
            # Import and use the original implementation
            from app.concurrency.tools.risk_metrics import calculate_risk_contributions
            return calculate_risk_contributions(
                position_arrays, data_list, strategy_allocations, log, strategy_configs
            )
    
    except Exception as e:
        log(f"Error calculating risk contributions: {str(e)}", "error")
        raise