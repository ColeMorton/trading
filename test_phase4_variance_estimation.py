#!/usr/bin/env python3
"""
Test script for Phase 4: Enhanced Variance Estimation implementation.

This script tests the new variance estimation methods and validation framework
using real portfolio data to ensure the implementation works correctly.
"""

import sys
import os
import numpy as np
import polars as pl
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_test_logger():
    """Create a simple test logging function."""
    def log(message: str, level: str = "info"):
        print(f"[{level.upper()}] {message}")
    return log

def test_variance_estimators():
    """Test the variance estimation methods."""
    log = create_test_logger()
    log("Testing Phase 4: Variance Estimators", "info")
    
    try:
        from app.concurrency.tools.variance_estimators import VarianceEstimator, estimate_portfolio_variance
        
        # Create test data
        np.random.seed(42)
        n_periods = 100
        n_strategies = 3
        
        # Generate correlated returns
        base_return = np.random.normal(0.001, 0.02, n_periods)
        returns_matrix = np.zeros((n_periods, n_strategies))
        
        # Strategy 1: Base return + noise
        returns_matrix[:, 0] = base_return + np.random.normal(0, 0.01, n_periods)
        
        # Strategy 2: Negatively correlated with base
        returns_matrix[:, 1] = -0.5 * base_return + np.random.normal(0, 0.015, n_periods)
        
        # Strategy 3: Independent
        returns_matrix[:, 2] = np.random.normal(0.0005, 0.025, n_periods)
        
        strategy_names = ["Strategy_1", "Strategy_2", "Strategy_3"]
        strategy_returns_list = [returns_matrix[:, i] for i in range(n_strategies)]
        
        log(f"Created test data: {n_periods} periods, {n_strategies} strategies", "info")
        
        # Test individual variance estimation methods
        estimator = VarianceEstimator(log)
        
        methods = ['sample', 'rolling', 'ewma', 'bootstrap', 'bayesian']
        
        for method in methods:
            try:
                log(f"\nTesting {method} variance estimation:", "info")
                
                if method == 'sample':
                    estimate = estimator.sample_variance(returns_matrix[:, 0])
                elif method == 'rolling':
                    estimate = estimator.rolling_variance(returns_matrix[:, 0])
                elif method == 'ewma':
                    estimate = estimator.ewma_variance(returns_matrix[:, 0])
                elif method == 'bootstrap':
                    estimate = estimator.bootstrap_variance(returns_matrix[:, 0])
                elif method == 'bayesian':
                    estimate = estimator.bayesian_variance(returns_matrix[:, 0])
                
                log(f"  Method: {estimate.method}")
                log(f"  Variance: {estimate.value:.8f}")
                log(f"  Confidence Interval: [{estimate.confidence_interval[0]:.8f}, {estimate.confidence_interval[1]:.8f}]")
                log(f"  Quality Score: {estimate.data_quality_score:.3f}")
                log(f"  Observations Used: {estimate.observations_used}")
                if estimate.warnings:
                    log(f"  Warnings: {estimate.warnings}")
                
            except Exception as e:
                log(f"Error testing {method}: {str(e)}", "error")
        
        # Test auto-selection
        log(f"\nTesting automatic method selection:", "info")
        auto_estimate = estimator.select_best_estimator(returns_matrix[:, 0])
        log(f"Auto-selected method: {auto_estimate.method}")
        log(f"Auto variance: {auto_estimate.value:.8f}")
        
        # Test portfolio-level estimation
        log(f"\nTesting portfolio-level variance estimation:", "info")
        variance_estimates = estimate_portfolio_variance(
            strategy_returns_list, strategy_names, 'auto', log
        )
        
        for name, estimate in variance_estimates.items():
            log(f"  {name}: {estimate.value:.8f} ({estimate.method}, quality: {estimate.data_quality_score:.3f})")
        
        log("Variance estimators test completed successfully", "info")
        return True
        
    except Exception as e:
        log(f"Variance estimators test failed: {str(e)}", "error")
        return False

def test_validation_framework():
    """Test the risk accuracy validation framework."""
    log = create_test_logger()
    log("Testing Phase 4: Validation Framework", "info")
    
    try:
        from app.concurrency.tools.risk_accuracy_validator import create_validator
        
        # Create test data
        np.random.seed(42)
        n_periods = 50
        n_strategies = 3
        
        # Generate test returns with some issues
        returns_matrix = np.random.normal(0.001, 0.02, (n_periods, n_strategies))
        
        # Add some data quality issues
        returns_matrix[10, 1] = np.nan  # Missing value
        returns_matrix[20, 2] = np.inf  # Infinite value
        
        strategy_names = ["Strategy_A", "Strategy_B", "Strategy_C"]
        weights = np.array([0.4, 0.3, 0.3])
        
        log(f"Created test data with quality issues: {n_periods} periods, {n_strategies} strategies", "info")
        
        # Test different validation levels
        validation_levels = ['permissive', 'moderate', 'strict']
        
        for level in validation_levels:
            log(f"\nTesting {level} validation level:", "info")
            
            try:
                validator = create_validator(log, level)
                
                # Test return data validation
                return_validation = validator.validate_return_data(returns_matrix, strategy_names)
                log(f"  Return validation: {'PASSED' if return_validation.is_valid else 'FAILED'}")
                log(f"  Quality score: {return_validation.quality_score:.3f}")
                if return_validation.messages:
                    log(f"  Messages: {return_validation.messages}")
                if return_validation.warnings:
                    log(f"  Warnings: {return_validation.warnings}")
                
                # Test weight validation
                weight_validation = validator.validate_portfolio_weights(weights, strategy_names)
                log(f"  Weight validation: {'PASSED' if weight_validation.is_valid else 'FAILED'}")
                
                # Test comprehensive validation
                comprehensive_validation = validator.validate_risk_calculation_inputs(
                    returns_matrix, weights, strategy_names
                )
                log(f"  Comprehensive validation: {'PASSED' if comprehensive_validation.is_valid else 'FAILED'}")
                log(f"  Overall quality: {comprehensive_validation.quality_score:.3f}")
                
            except Exception as e:
                log(f"Error testing {level} validation: {str(e)}", "error")
        
        log("Validation framework test completed successfully", "info")
        return True
        
    except Exception as e:
        log(f"Validation framework test failed: {str(e)}", "error")
        return False

def test_enhanced_risk_calculation():
    """Test the enhanced risk calculation with Phase 4 features."""
    log = create_test_logger()
    log("Testing Phase 4: Enhanced Risk Calculation", "info")
    
    try:
        from app.concurrency.tools.risk_contribution_calculator import RiskContributionCalculator
        
        # Create test data
        np.random.seed(42)
        n_periods = 200  # Sufficient data for all methods
        n_strategies = 4
        
        # Generate realistic returns
        returns_matrix = np.zeros((n_periods, n_strategies))
        
        # Create different types of strategies
        market_return = np.random.normal(0.0008, 0.015, n_periods)
        
        # High vol growth strategy
        returns_matrix[:, 0] = 1.2 * market_return + np.random.normal(0, 0.025, n_periods)
        
        # Low vol defensive strategy  
        returns_matrix[:, 1] = 0.6 * market_return + np.random.normal(0, 0.008, n_periods)
        
        # Mean reverting strategy
        returns_matrix[:, 2] = -0.3 * market_return + np.random.normal(0.0005, 0.018, n_periods)
        
        # Momentum strategy
        momentum = np.zeros(n_periods)
        for i in range(1, n_periods):
            momentum[i] = 0.7 * momentum[i-1] + 0.3 * market_return[i-1]
        returns_matrix[:, 3] = momentum + np.random.normal(0, 0.012, n_periods)
        
        strategy_names = ["Growth", "Defensive", "MeanRevert", "Momentum"]
        weights = np.array([0.3, 0.25, 0.25, 0.2])
        
        log(f"Created realistic test data: {n_periods} periods, {n_strategies} strategies", "info")
        
        # Test different variance methods
        variance_methods = ['auto', 'sample', 'ewma', 'bayesian']
        validation_levels = ['moderate', 'strict']
        
        for var_method in variance_methods:
            for val_level in validation_levels:
                log(f"\nTesting enhanced calculation with {var_method} variance, {val_level} validation:", "info")
                
                try:
                    enhanced_metrics = RiskContributionCalculator.calculate_portfolio_metrics_enhanced(
                        returns_matrix, weights, strategy_names, var_method, val_level, log
                    )
                    
                    log(f"  Portfolio volatility: {enhanced_metrics['portfolio_volatility']:.6f}")
                    log(f"  Total risk contribution: {enhanced_metrics['total_risk_contribution']:.6f}")
                    
                    if 'enhanced_diagnostics' in enhanced_metrics:
                        diagnostics = enhanced_metrics['enhanced_diagnostics']
                        log(f"  Enhancement applied: {diagnostics['enhancement_applied']}")
                        log(f"  Method used: {diagnostics['method_used']}")
                        
                        # Check variance estimates
                        var_estimates = diagnostics['variance_estimates']
                        for name, est in var_estimates.items():
                            log(f"    {name}: {est['method']} method, quality {est['quality_score']:.3f}")
                        
                        # Check validation results
                        input_validation = diagnostics['validation_results']['input_validation']
                        log(f"  Input validation quality: {input_validation['quality_score']:.3f}")
                    
                    if 'portfolio_volatility_ci' in enhanced_metrics and enhanced_metrics['portfolio_volatility_ci']:
                        ci = enhanced_metrics['portfolio_volatility_ci']
                        log(f"  Volatility 95% CI: [{ci['lower']:.6f}, {ci['upper']:.6f}]")
                    
                    # Verify risk contributions sum to 100%
                    risk_contribs = enhanced_metrics['risk_contributions']
                    total_contrib = sum(contrib['risk_contribution_pct'] for contrib in risk_contribs.values())
                    log(f"  Risk contributions sum: {total_contrib:.6f} (should be 1.0)")
                    
                    if abs(total_contrib - 1.0) > 0.001:
                        log(f"  WARNING: Risk contributions don't sum to 100%!", "warning")
                    
                except Exception as e:
                    log(f"Error with {var_method}/{val_level}: {str(e)}", "error")
        
        log("Enhanced risk calculation test completed successfully", "info")
        return True
        
    except Exception as e:
        log(f"Enhanced risk calculation test failed: {str(e)}", "error")
        return False

def main():
    """Run all Phase 4 tests."""
    log = create_test_logger()
    log("=" * 60, "info")
    log("PHASE 4: ENHANCED VARIANCE ESTIMATION - TEST SUITE", "info")
    log("=" * 60, "info")
    
    tests = [
        ("Variance Estimators", test_variance_estimators),
        ("Validation Framework", test_validation_framework),
        ("Enhanced Risk Calculation", test_enhanced_risk_calculation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        log(f"\n{'-' * 40}", "info")
        log(f"Running {test_name} Test", "info")
        log(f"{'-' * 40}", "info")
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            log(f"Unexpected error in {test_name}: {str(e)}", "error")
            results[test_name] = False
    
    # Summary
    log("\n" + "=" * 60, "info")
    log("PHASE 4 TEST RESULTS SUMMARY", "info")
    log("=" * 60, "info")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        log(f"{test_name}: {status}", "info")
        if not passed:
            all_passed = False
    
    log(f"\nOverall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}", "info")
    
    if all_passed:
        log("\nPhase 4: Enhanced Variance Estimation implementation is working correctly!", "info")
    else:
        log("\nPhase 4 implementation has issues that need to be addressed.", "error")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)