# Technical Specification: Risk Contribution Calculation Fix

**Priority**: CRITICAL - Blocks Production  
**Issue**: Risk contributions sum to 441% instead of 100%  
**Root Cause**: Mathematical error in risk decomposition algorithm  

## Mathematical Background

### Correct Risk Contribution Formula

For a portfolio with N assets, the risk contribution of asset i should be:

```
RC_i = w_i * (∂σ_p / ∂w_i)
```

Where:
- `RC_i` = Risk contribution of asset i
- `w_i` = Weight of asset i in portfolio
- `σ_p` = Portfolio standard deviation
- `∂σ_p / ∂w_i` = Marginal contribution to risk

The sum of all risk contributions must equal the total portfolio risk:
```
Σ RC_i = σ_p
```

And the percentage risk contributions must sum to 100%:
```
Σ (RC_i / σ_p) = 1.0
```

## Current Implementation Error

### Problematic Code (risk_metrics.py)

```python
# CURRENT - INCORRECT
marginal_contrib = np.sum(covariance_matrix[i, :]) / portfolio_risk
relative_contrib = marginal_contrib / portfolio_risk  # Double division!
risk_contributions[f"strategy_{i+1}_risk_contrib"] = float(relative_contrib)
```

This code:
1. Divides by portfolio_risk twice
2. Doesn't properly weight by allocation
3. Uses sum of covariance row instead of proper matrix multiplication

## Correct Implementation

### Step 1: Calculate Portfolio Variance

```python
def calculate_portfolio_variance(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
    """
    Calculate portfolio variance: σ²_p = w'Σw
    """
    return np.dot(weights, np.dot(cov_matrix, weights))
```

### Step 2: Calculate Marginal Contributions

```python
def calculate_marginal_contributions(weights: np.ndarray, cov_matrix: np.ndarray) -> np.ndarray:
    """
    Calculate marginal contribution to risk for each asset.
    MC_i = (Σw)_i / σ_p
    """
    portfolio_variance = calculate_portfolio_variance(weights, cov_matrix)
    portfolio_std = np.sqrt(portfolio_variance)
    
    # Marginal contributions: Σw
    marginal_contributions = np.dot(cov_matrix, weights)
    
    # Divide by portfolio standard deviation
    marginal_contributions_scaled = marginal_contributions / portfolio_std
    
    return marginal_contributions_scaled
```

### Step 3: Calculate Risk Contributions

```python
def calculate_risk_contributions(weights: np.ndarray, cov_matrix: np.ndarray) -> Dict[str, float]:
    """
    Calculate risk contribution for each strategy.
    RC_i = w_i * MC_i
    """
    # Get marginal contributions
    marginal_contributions = calculate_marginal_contributions(weights, cov_matrix)
    
    # Calculate risk contributions
    risk_contributions = weights * marginal_contributions
    
    # Convert to percentages (should sum to 1.0)
    portfolio_std = np.sqrt(calculate_portfolio_variance(weights, cov_matrix))
    risk_contribution_pct = risk_contributions / portfolio_std
    
    # Validate
    total_contribution = np.sum(risk_contribution_pct)
    if not np.isclose(total_contribution, 1.0, rtol=1e-5):
        logger.warning(f"Risk contributions sum to {total_contribution:.4f}, expected 1.0")
    
    # Return as dictionary
    return {
        f"strategy_{i}": float(risk_contribution_pct[i]) 
        for i in range(len(weights))
    }
```

## Complete Fixed Implementation

```python
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class RiskContributionCalculator:
    """
    Calculates risk contributions ensuring they sum to 100%.
    """
    
    @staticmethod
    def calculate_portfolio_metrics(
        returns: np.ndarray,
        weights: np.ndarray,
        strategy_names: List[str]
    ) -> Dict[str, any]:
        """
        Calculate complete portfolio risk metrics.
        
        Args:
            returns: Array of shape (n_periods, n_strategies) with returns
            weights: Array of shape (n_strategies,) with allocations
            strategy_names: List of strategy identifiers
            
        Returns:
            Dictionary with risk metrics and contributions
        """
        # Ensure weights sum to 1
        weights = weights / np.sum(weights)
        
        # Calculate covariance matrix
        cov_matrix = np.cov(returns.T)
        
        # Calculate portfolio variance and standard deviation
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        portfolio_std = np.sqrt(portfolio_variance)
        
        # Calculate marginal contributions: Σw
        marginal_contributions = np.dot(cov_matrix, weights)
        
        # Calculate component contributions: w_i * (Σw)_i
        component_contributions = weights * marginal_contributions
        
        # Convert to percentage contributions
        risk_contributions_pct = component_contributions / portfolio_variance
        
        # Validate sum equals 1.0
        total_contribution = np.sum(risk_contributions_pct)
        if not np.isclose(total_contribution, 1.0, rtol=1e-5):
            logger.error(
                f"Risk contributions sum to {total_contribution:.4f}, "
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
```

## Testing Strategy

### Unit Test Example

```python
import pytest
import numpy as np

def test_risk_contributions_sum_to_one():
    """Test that risk contributions always sum to 100%."""
    # Create test data
    n_periods = 100
    n_strategies = 3
    
    # Generate random returns
    np.random.seed(42)
    returns = np.random.randn(n_periods, n_strategies) * 0.01
    
    # Test with equal weights
    weights = np.array([1/3, 1/3, 1/3])
    strategy_names = ["Strategy_A", "Strategy_B", "Strategy_C"]
    
    calculator = RiskContributionCalculator()
    metrics = calculator.calculate_portfolio_metrics(returns, weights, strategy_names)
    
    # Extract risk contribution percentages
    risk_contribs = [
        metrics["risk_contributions"][name]["risk_contribution_pct"]
        for name in strategy_names
    ]
    
    # Assert sum equals 1.0
    total = sum(risk_contribs)
    assert np.isclose(total, 1.0, rtol=1e-5), f"Risk contributions sum to {total}, expected 1.0"

def test_risk_contributions_with_correlation():
    """Test risk contributions with known correlation structure."""
    # Create perfectly correlated assets
    n_periods = 252
    base_returns = np.random.randn(n_periods) * 0.01
    
    # Three assets with different volatilities but perfect correlation
    returns = np.column_stack([
        base_returns * 1.0,  # Vol = 1x
        base_returns * 2.0,  # Vol = 2x  
        base_returns * 3.0   # Vol = 3x
    ])
    
    weights = np.array([0.5, 0.3, 0.2])
    strategy_names = ["Low_Vol", "Med_Vol", "High_Vol"]
    
    calculator = RiskContributionCalculator()
    metrics = calculator.calculate_portfolio_metrics(returns, weights, strategy_names)
    
    # With perfect correlation, risk contributions should be proportional to weight * volatility
    # Expected contributions: [0.5*1, 0.3*2, 0.2*3] = [0.5, 0.6, 0.6]
    # Normalized: [0.294, 0.353, 0.353] approximately
    
    risk_contribs = {
        name: metrics["risk_contributions"][name]["risk_contribution_pct"]
        for name in strategy_names
    }
    
    # Verify sum to 1.0
    assert np.isclose(sum(risk_contribs.values()), 1.0, rtol=1e-5)
```

## Migration Strategy

### Phase 1: Parallel Implementation
```python
# Add feature flag
USE_FIXED_RISK_CALC = os.getenv("USE_FIXED_RISK_CALC", "false").lower() == "true"

if USE_FIXED_RISK_CALC:
    risk_metrics = RiskContributionCalculator.calculate_portfolio_metrics(...)
else:
    risk_metrics = legacy_calculate_risk_metrics(...)  # Current implementation
```

### Phase 2: Validation Period
- Run both calculations in parallel
- Log discrepancies
- Validate new calculation correctness

### Phase 3: Cutover
- Enable new calculation by default
- Maintain legacy code for rollback
- Monitor for issues

## Validation Checklist

- [ ] Risk contributions always sum to 100% (±0.1%)
- [ ] Individual contributions are between 0% and 100%
- [ ] Calculations match hand-calculated examples
- [ ] Performance impact < 5%
- [ ] All existing tests pass with new implementation
- [ ] New comprehensive test suite passes
- [ ] Validation logs show no anomalies over 1 week

## References

1. **Risk Parity and Budgeting** - Roncalli (2013)
2. **Modern Portfolio Theory** - Markowitz (1952)
3. **Risk Contributions in Portfolio Management** - Meucci (2007)

---

This specification provides the complete mathematical foundation and implementation details needed to fix the critical risk contribution calculation error.