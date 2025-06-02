#!/usr/bin/env python3
"""
Risk Metrics Validator Module.

This module provides validation for risk metrics calculations, addressing the issues
identified in Phase 1 including:
- Max drawdown understatement (62.91% MSTR vs actual CSV data)
- Risk contribution validation
- Volatility aggregation accuracy
- Correlation calculation methodology

Classes:
    RiskMetricsValidator: Comprehensive risk metrics validation
    DrawdownCalculator: Proper portfolio drawdown calculation
    VolatilityAggregator: Correct volatility aggregation methods
"""

from typing import Dict, List, Any, Optional, Callable, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass
import warnings


@dataclass
class RiskValidationResult:
    """Result of risk metrics validation."""
    valid: bool
    issue_type: str
    csv_value: float
    json_value: float
    difference: float
    relative_difference: float
    tolerance: float
    message: str


@dataclass
class DrawdownComponents:
    """Components of drawdown calculation."""
    max_drawdown: float
    peak_date: Optional[str]
    trough_date: Optional[str]
    recovery_date: Optional[str]
    drawdown_duration: int
    recovery_duration: int
    equity_curve: np.ndarray


class RiskMetricsValidator:
    """
    Comprehensive risk metrics validator addressing calculation issues.
    
    This validator addresses the core issues identified in the portfolio metrics:
    1. Max drawdown understatement (27-44 percentage points)
    2. Risk contribution validation 
    3. Volatility aggregation accuracy
    4. Correlation calculation methodology
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize the risk metrics validator.
        
        Args:
            strict_mode: Whether to use strict validation tolerances
        """
        self.strict_mode = strict_mode
        self.tolerances = {
            'max_drawdown': 0.05 if strict_mode else 0.15,  # 5% vs 15% tolerance
            'volatility': 0.10 if strict_mode else 0.20,
            'correlation': 0.15 if strict_mode else 0.25,
            'var': 0.10 if strict_mode else 0.20,
            'risk_contribution': 0.10 if strict_mode else 0.15
        }
    
    def validate_max_drawdown(
        self,
        csv_max_drawdown: float,
        json_max_drawdown: float,
        ticker: str,
        log: Optional[Callable[[str, str], None]] = None
    ) -> RiskValidationResult:
        """
        Validate max drawdown calculation against CSV data.
        
        This addresses the critical issue where MSTR shows 62.91% JSON drawdown
        vs actual CSV values that should be much higher.
        
        Args:
            csv_max_drawdown: Max drawdown from CSV backtest data
            json_max_drawdown: Max drawdown from JSON aggregation
            ticker: Ticker symbol for context
            log: Optional logging function
            
        Returns:
            RiskValidationResult with validation outcome
        """
        if csv_max_drawdown <= 0 or json_max_drawdown < 0:
            return RiskValidationResult(
                valid=False,
                issue_type="invalid_values",
                csv_value=csv_max_drawdown,
                json_value=json_max_drawdown,
                difference=0,
                relative_difference=0,
                tolerance=self.tolerances['max_drawdown'],
                message=f"Invalid drawdown values for {ticker}"
            )
        
        # Calculate differences
        difference = abs(json_max_drawdown - csv_max_drawdown)
        relative_difference = difference / csv_max_drawdown if csv_max_drawdown > 0 else float('inf')
        
        # Determine issue type
        if json_max_drawdown < csv_max_drawdown * 0.5:
            issue_type = "severe_understatement"
        elif json_max_drawdown < csv_max_drawdown * 0.8:
            issue_type = "moderate_understatement" 
        elif relative_difference > self.tolerances['max_drawdown']:
            issue_type = "tolerance_exceeded"
        else:
            issue_type = "acceptable"
        
        is_valid = issue_type == "acceptable"
        
        # Create detailed message
        if not is_valid:
            if issue_type == "severe_understatement":
                message = f"{ticker}: Severe drawdown understatement! JSON: {json_max_drawdown:.1%} vs CSV: {csv_max_drawdown:.1%} (understated by {difference:.1%})"
            elif issue_type == "moderate_understatement":
                message = f"{ticker}: Moderate drawdown understatement. JSON: {json_max_drawdown:.1%} vs CSV: {csv_max_drawdown:.1%} (understated by {difference:.1%})"
            else:
                message = f"{ticker}: Drawdown difference exceeds tolerance. JSON: {json_max_drawdown:.1%} vs CSV: {csv_max_drawdown:.1%} (diff: {relative_difference:.1%})"
        else:
            message = f"{ticker}: Drawdown validation passed. JSON: {json_max_drawdown:.1%} vs CSV: {csv_max_drawdown:.1%}"
        
        if log:
            level = "warning" if not is_valid else "info"
            log(message, level)
        
        return RiskValidationResult(
            valid=is_valid,
            issue_type=issue_type,
            csv_value=csv_max_drawdown,
            json_value=json_max_drawdown,
            difference=difference,
            relative_difference=relative_difference,
            tolerance=self.tolerances['max_drawdown'],
            message=message
        )
    
    def validate_volatility_aggregation(
        self,
        individual_volatilities: List[float],
        individual_correlations: List[List[float]],
        aggregated_volatility: float,
        allocation_weights: List[float],
        log: Optional[Callable[[str, str], None]] = None
    ) -> RiskValidationResult:
        """
        Validate portfolio volatility aggregation using proper portfolio theory.
        
        Portfolio volatility should account for correlations between strategies:
        σ_p = sqrt(w^T * Σ * w)
        where w is weights and Σ is covariance matrix
        
        Args:
            individual_volatilities: List of individual strategy volatilities
            individual_correlations: Correlation matrix between strategies
            aggregated_volatility: Portfolio volatility from JSON
            allocation_weights: Strategy allocation weights
            log: Optional logging function
            
        Returns:
            RiskValidationResult with validation outcome
        """
        try:
            # Calculate expected portfolio volatility using portfolio theory
            n_strategies = len(individual_volatilities)
            
            if len(allocation_weights) != n_strategies:
                return RiskValidationResult(
                    valid=False,
                    issue_type="dimension_mismatch",
                    csv_value=0,
                    json_value=aggregated_volatility,
                    difference=0,
                    relative_difference=0,
                    tolerance=self.tolerances['volatility'],
                    message="Dimension mismatch in volatility validation inputs"
                )
            
            # Construct covariance matrix
            volatilities = np.array(individual_volatilities)
            weights = np.array(allocation_weights)
            
            # Handle correlation matrix
            if len(individual_correlations) == n_strategies and len(individual_correlations[0]) == n_strategies:
                correlation_matrix = np.array(individual_correlations)
            else:
                # Use identity matrix if correlations not provided properly
                correlation_matrix = np.eye(n_strategies)
                if log:
                    log("Using identity correlation matrix due to dimension issues", "warning")
            
            # Calculate covariance matrix: Σ = D * P * D (where D is diag(volatilities), P is correlation matrix)
            vol_matrix = np.outer(volatilities, volatilities)
            covariance_matrix = vol_matrix * correlation_matrix
            
            # Calculate portfolio volatility: σ_p = sqrt(w^T * Σ * w)
            expected_portfolio_vol = np.sqrt(np.dot(weights, np.dot(covariance_matrix, weights)))
            
            # Compare with aggregated volatility
            difference = abs(aggregated_volatility - expected_portfolio_vol)
            relative_difference = difference / expected_portfolio_vol if expected_portfolio_vol > 0 else float('inf')
            
            # Determine validation result
            if relative_difference <= self.tolerances['volatility']:
                issue_type = "acceptable"
                is_valid = True
            elif relative_difference <= self.tolerances['volatility'] * 2:
                issue_type = "tolerance_exceeded"
                is_valid = False
            else:
                issue_type = "significant_error"
                is_valid = False
            
            message = f"Portfolio volatility validation: Expected={expected_portfolio_vol:.4f}, Actual={aggregated_volatility:.4f}, Diff={relative_difference:.1%}"
            
            if log:
                level = "info" if is_valid else "warning"
                log(message, level)
            
            return RiskValidationResult(
                valid=is_valid,
                issue_type=issue_type,
                csv_value=expected_portfolio_vol,
                json_value=aggregated_volatility,
                difference=difference,
                relative_difference=relative_difference,
                tolerance=self.tolerances['volatility'],
                message=message
            )
            
        except Exception as e:
            error_message = f"Error in volatility validation: {str(e)}"
            if log:
                log(error_message, "error")
            
            return RiskValidationResult(
                valid=False,
                issue_type="calculation_error",
                csv_value=0,
                json_value=aggregated_volatility,
                difference=0,
                relative_difference=0,
                tolerance=self.tolerances['volatility'],
                message=error_message
            )
    
    def validate_risk_contributions(
        self,
        individual_risk_contributions: List[float],
        portfolio_total_risk: float,
        strategy_names: List[str],
        log: Optional[Callable[[str, str], None]] = None
    ) -> RiskValidationResult:
        """
        Validate that individual risk contributions sum to total portfolio risk.
        
        Risk contributions should sum to approximately 100% of portfolio risk,
        accounting for correlation effects.
        
        Args:
            individual_risk_contributions: List of individual strategy risk contributions
            portfolio_total_risk: Total portfolio risk
            strategy_names: Names of strategies for logging
            log: Optional logging function
            
        Returns:
            RiskValidationResult with validation outcome
        """
        if not individual_risk_contributions or portfolio_total_risk <= 0:
            return RiskValidationResult(
                valid=False,
                issue_type="invalid_inputs",
                csv_value=portfolio_total_risk,
                json_value=sum(individual_risk_contributions) if individual_risk_contributions else 0,
                difference=0,
                relative_difference=0,
                tolerance=self.tolerances['risk_contribution'],
                message="Invalid inputs for risk contribution validation"
            )
        
        # Sum individual contributions
        total_contributions = sum(individual_risk_contributions)
        
        # Calculate difference
        difference = abs(total_contributions - portfolio_total_risk)
        relative_difference = difference / portfolio_total_risk if portfolio_total_risk > 0 else float('inf')
        
        # Determine validation result
        if relative_difference <= self.tolerances['risk_contribution']:
            issue_type = "acceptable"
            is_valid = True
        elif relative_difference <= self.tolerances['risk_contribution'] * 2:
            issue_type = "tolerance_exceeded"
            is_valid = False
        else:
            issue_type = "significant_error"
            is_valid = False
        
        # Create detailed message
        message = f"Risk contributions validation: Sum={total_contributions:.4f}, Portfolio={portfolio_total_risk:.4f}, Diff={relative_difference:.1%}"
        
        if log:
            level = "info" if is_valid else "warning"
            log(message, level)
            
            if not is_valid and strategy_names:
                log("Individual risk contributions:", "info")
                for name, contrib in zip(strategy_names, individual_risk_contributions):
                    log(f"  {name}: {contrib:.4f} ({contrib/portfolio_total_risk:.1%} of total)", "info")
        
        return RiskValidationResult(
            valid=is_valid,
            issue_type=issue_type,
            csv_value=portfolio_total_risk,
            json_value=total_contributions,
            difference=difference,
            relative_difference=relative_difference,
            tolerance=self.tolerances['risk_contribution'],
            message=message
        )
    
    def validate_all_risk_metrics(
        self,
        csv_data: pd.DataFrame,
        json_metrics: Dict[str, Any],
        log: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, RiskValidationResult]:
        """
        Comprehensive validation of all risk metrics.
        
        Args:
            csv_data: DataFrame with CSV backtest data
            json_metrics: Dictionary with JSON portfolio metrics  
            log: Optional logging function
            
        Returns:
            Dictionary of validation results by metric type
        """
        results = {}
        
        try:
            # Validate max drawdown for each ticker
            unique_tickers = csv_data['Ticker'].unique() if 'Ticker' in csv_data.columns else []
            
            for ticker in unique_tickers:
                # Get CSV max drawdown
                ticker_csv = csv_data[csv_data['Ticker'] == ticker]
                if 'Max Drawdown %' in ticker_csv.columns:
                    csv_max_dd = ticker_csv['Max Drawdown %'].max() / 100  # Convert to decimal
                else:
                    continue
                
                # Get JSON max drawdown
                ticker_metrics = json_metrics.get('ticker_metrics', {}).get(ticker, {})
                signal_quality = ticker_metrics.get('signal_quality_metrics', {})
                json_max_dd = signal_quality.get('max_drawdown', 0)
                
                # Validate
                dd_result = self.validate_max_drawdown(csv_max_dd, json_max_dd, ticker, log)
                results[f'max_drawdown_{ticker}'] = dd_result
            
            # Validate portfolio-level risk metrics if available
            portfolio_metrics = json_metrics.get('portfolio_metrics', {})
            
            # Additional validations can be added here for:
            # - Portfolio volatility
            # - Risk contributions  
            # - Correlation matrices
            # - Value at Risk calculations
            
            if log:
                valid_count = sum(1 for result in results.values() if result.valid)
                total_count = len(results)
                log(f"Risk metrics validation complete: {valid_count}/{total_count} metrics passed", "info")
            
        except Exception as e:
            error_message = f"Error in comprehensive risk validation: {str(e)}"
            if log:
                log(error_message, "error")
            
            results['validation_error'] = RiskValidationResult(
                valid=False,
                issue_type="validation_error",
                csv_value=0,
                json_value=0,
                difference=0,
                relative_difference=0,
                tolerance=0,
                message=error_message
            )
        
        return results


class DrawdownCalculator:
    """
    Proper portfolio drawdown calculator addressing understatement issues.
    
    This calculator implements the correct methodology for portfolio drawdown
    calculation using actual equity curves rather than allocation-weighted
    averages of individual drawdowns.
    """
    
    def calculate_portfolio_max_drawdown(
        self,
        strategy_equity_curves: List[np.ndarray],
        allocation_weights: List[float],
        log: Optional[Callable[[str, str], None]] = None
    ) -> DrawdownComponents:
        """
        Calculate portfolio max drawdown using proper equity curve combination.
        
        This method addresses the core issue where portfolio drawdowns are
        understated by 27-44 percentage points by using actual combined
        equity curves rather than weighted averages of individual drawdowns.
        
        Args:
            strategy_equity_curves: List of equity curves for each strategy
            allocation_weights: Allocation weights for each strategy
            log: Optional logging function
            
        Returns:
            DrawdownComponents with comprehensive drawdown analysis
        """
        if not strategy_equity_curves or not allocation_weights:
            return DrawdownComponents(0, None, None, None, 0, 0, np.array([]))
        
        if len(strategy_equity_curves) != len(allocation_weights):
            raise ValueError("Number of equity curves must match number of allocation weights")
        
        # Normalize allocation weights
        total_allocation = sum(allocation_weights)
        if total_allocation <= 0:
            raise ValueError("Total allocation must be positive")
        
        normalized_weights = [w / total_allocation for w in allocation_weights]
        
        # Combine equity curves with proper allocation weighting
        portfolio_equity = np.zeros(len(strategy_equity_curves[0]))
        
        for i, (curve, allocation) in enumerate(zip(strategy_equity_curves, normalized_weights)):
            if len(curve) != len(portfolio_equity):
                raise ValueError(f"All equity curves must have same length. Strategy {i} has {len(curve)}, expected {len(portfolio_equity)}")
            
            portfolio_equity += curve * allocation
        
        # Calculate running maximum and drawdown
        running_max = np.maximum.accumulate(portfolio_equity)
        drawdowns = (running_max - portfolio_equity) / running_max
        
        # Find maximum drawdown and its details
        max_drawdown = np.max(drawdowns)
        max_dd_idx = np.argmax(drawdowns)
        
        # Find peak before max drawdown
        peak_idx = max_dd_idx
        for i in range(max_dd_idx, -1, -1):
            if portfolio_equity[i] == running_max[max_dd_idx]:
                peak_idx = i
                break
        
        # Find recovery point after max drawdown
        recovery_idx = None
        peak_value = running_max[max_dd_idx]
        
        for i in range(max_dd_idx + 1, len(portfolio_equity)):
            if portfolio_equity[i] >= peak_value:
                recovery_idx = i
                break
        
        # Calculate durations
        drawdown_duration = max_dd_idx - peak_idx
        recovery_duration = (recovery_idx - max_dd_idx) if recovery_idx is not None else 0
        
        if log:
            log(f"Portfolio drawdown calculation completed:", "info")
            log(f"  Max drawdown: {max_drawdown:.4f} ({max_drawdown:.1%})", "info")
            log(f"  Peak index: {peak_idx}, Trough index: {max_dd_idx}", "info")
            log(f"  Drawdown duration: {drawdown_duration} periods", "info")
            log(f"  Recovery duration: {recovery_duration} periods", "info")
        
        return DrawdownComponents(
            max_drawdown=max_drawdown,
            peak_date=str(peak_idx),  # Would be actual dates in real implementation
            trough_date=str(max_dd_idx),
            recovery_date=str(recovery_idx) if recovery_idx is not None else None,
            drawdown_duration=drawdown_duration,
            recovery_duration=recovery_duration,
            equity_curve=portfolio_equity
        )
    
    def calculate_individual_drawdown(
        self,
        equity_curve: np.ndarray,
        log: Optional[Callable[[str, str], None]] = None
    ) -> DrawdownComponents:
        """
        Calculate drawdown for an individual strategy equity curve.
        
        Args:
            equity_curve: Equity curve for the strategy
            log: Optional logging function
            
        Returns:
            DrawdownComponents with individual strategy drawdown analysis
        """
        if len(equity_curve) == 0:
            return DrawdownComponents(0, None, None, None, 0, 0, equity_curve)
        
        # Calculate running maximum and drawdown
        running_max = np.maximum.accumulate(equity_curve)
        drawdowns = (running_max - equity_curve) / running_max
        
        # Find maximum drawdown and its details
        max_drawdown = np.max(drawdowns)
        max_dd_idx = np.argmax(drawdowns)
        
        # Find peak before max drawdown
        peak_idx = max_dd_idx
        for i in range(max_dd_idx, -1, -1):
            if equity_curve[i] == running_max[max_dd_idx]:
                peak_idx = i
                break
        
        # Find recovery point
        recovery_idx = None
        peak_value = running_max[max_dd_idx]
        
        for i in range(max_dd_idx + 1, len(equity_curve)):
            if equity_curve[i] >= peak_value:
                recovery_idx = i
                break
        
        # Calculate durations
        drawdown_duration = max_dd_idx - peak_idx
        recovery_duration = (recovery_idx - max_dd_idx) if recovery_idx is not None else 0
        
        if log:
            log(f"Individual drawdown: {max_drawdown:.4f} ({max_drawdown:.1%})", "info")
        
        return DrawdownComponents(
            max_drawdown=max_drawdown,
            peak_date=str(peak_idx),
            trough_date=str(max_dd_idx),
            recovery_date=str(recovery_idx) if recovery_idx is not None else None,
            drawdown_duration=drawdown_duration,
            recovery_duration=recovery_duration,
            equity_curve=equity_curve
        )


class VolatilityAggregator:
    """
    Proper volatility aggregation using portfolio theory.
    
    This class implements correct portfolio volatility calculation that
    accounts for correlations between strategies.
    """
    
    def calculate_portfolio_volatility(
        self,
        individual_volatilities: List[float],
        correlation_matrix: np.ndarray,
        allocation_weights: List[float],
        log: Optional[Callable[[str, str], None]] = None
    ) -> float:
        """
        Calculate portfolio volatility using proper portfolio theory.
        
        Formula: σ_p = sqrt(w^T * Σ * w)
        where w is weights vector and Σ is covariance matrix
        
        Args:
            individual_volatilities: List of individual strategy volatilities
            correlation_matrix: Correlation matrix between strategies
            allocation_weights: Allocation weights for each strategy
            log: Optional logging function
            
        Returns:
            Portfolio volatility
        """
        n_strategies = len(individual_volatilities)
        
        if len(allocation_weights) != n_strategies:
            raise ValueError("Number of allocation weights must match number of strategies")
        
        if correlation_matrix.shape != (n_strategies, n_strategies):
            raise ValueError(f"Correlation matrix must be {n_strategies}x{n_strategies}")
        
        # Convert to numpy arrays
        volatilities = np.array(individual_volatilities)
        weights = np.array(allocation_weights)
        
        # Normalize weights
        weights = weights / np.sum(weights)
        
        # Calculate covariance matrix: Σ = D * P * D
        # where D is diagonal matrix of volatilities, P is correlation matrix
        vol_outer = np.outer(volatilities, volatilities)
        covariance_matrix = vol_outer * correlation_matrix
        
        # Calculate portfolio volatility: σ_p = sqrt(w^T * Σ * w)
        portfolio_variance = np.dot(weights, np.dot(covariance_matrix, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        if log:
            log(f"Portfolio volatility calculation:", "info")
            log(f"  Individual volatilities: {[f'{v:.4f}' for v in volatilities]}", "info")
            log(f"  Weights: {[f'{w:.4f}' for w in weights]}", "info")
            log(f"  Portfolio volatility: {portfolio_volatility:.4f}", "info")
        
        return float(portfolio_volatility)
    
    def calculate_risk_contributions(
        self,
        individual_volatilities: List[float],
        correlation_matrix: np.ndarray,
        allocation_weights: List[float],
        log: Optional[Callable[[str, str], None]] = None
    ) -> List[float]:
        """
        Calculate risk contributions for each strategy.
        
        Risk contribution = (w_i * σ_i * ρ_ip) / σ_p
        where ρ_ip is correlation between strategy i and portfolio
        
        Args:
            individual_volatilities: List of individual strategy volatilities
            correlation_matrix: Correlation matrix between strategies
            allocation_weights: Allocation weights for each strategy
            log: Optional logging function
            
        Returns:
            List of risk contributions for each strategy
        """
        # Calculate portfolio volatility first
        portfolio_vol = self.calculate_portfolio_volatility(
            individual_volatilities, correlation_matrix, allocation_weights, log
        )
        
        if portfolio_vol <= 0:
            return [0.0] * len(individual_volatilities)
        
        # Convert to numpy arrays
        volatilities = np.array(individual_volatilities)
        weights = np.array(allocation_weights)
        weights = weights / np.sum(weights)  # Normalize
        
        # Calculate covariance matrix
        vol_outer = np.outer(volatilities, volatilities)
        covariance_matrix = vol_outer * correlation_matrix
        
        # Calculate risk contributions
        # RC_i = (w_i * (Σ * w)_i) / σ_p^2
        portfolio_variance = portfolio_vol ** 2
        cov_times_weights = np.dot(covariance_matrix, weights)
        
        risk_contributions = []
        for i in range(len(weights)):
            rc = (weights[i] * cov_times_weights[i]) / portfolio_variance
            risk_contributions.append(float(rc))
        
        if log:
            log(f"Risk contributions calculated:", "info")
            total_rc = sum(risk_contributions)
            for i, rc in enumerate(risk_contributions):
                log(f"  Strategy {i}: {rc:.4f} ({rc/total_rc:.1%} of total)", "info")
            log(f"  Total: {total_rc:.4f} (should ≈ 1.0)", "info")
        
        return risk_contributions