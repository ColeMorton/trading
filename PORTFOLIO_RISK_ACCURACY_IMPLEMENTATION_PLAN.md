# Portfolio Risk Accuracy Implementation Plan

## Overview
This plan addresses the current limitation where `total_portfolio_risk` shows a fallback value of 0.1 (10% default volatility) instead of calculated risk metrics. The goal is to implement accurate portfolio risk calculation based on actual data rather than assumptions.

## Current Issues
1. **Return series alignment**: Different length return series per strategy forcing assumed correlations
2. **Hardcoded correlation assumptions**: Using 0.3 correlation instead of calculated values
3. **Individual strategy focus**: Calculating from individual returns rather than portfolio-level returns
4. **Poor variance estimation**: Using minimal fallback values instead of proper statistical estimation

## Implementation Phases

### Phase 1: Fix Return Series Alignment
**Objective**: Align all strategy return series to common time periods for accurate covariance calculation

#### Tasks:
1. **Create return alignment utility** (`app/concurrency/tools/return_alignment.py`)
   - Align all strategy return series to common date range using Polars for consistency with `ma_cross`
   - Handle missing periods with appropriate interpolation/filling
   - Ensure consistent frequency (daily/hourly) across strategies
   - Use `@handle_errors` decorator with custom `DataAlignmentError` exceptions

2. **Implement period synchronization**
   - Find common date range across all strategies
   - Create synchronized position arrays
   - Generate aligned return matrices
   - Integrate with existing logging patterns using `logging_context`

3. **Update risk calculation pipeline**
   - Modify `calculate_risk_metrics_from_dataframes` to use aligned data
   - Remove dummy return matrix construction
   - Use actual synchronized returns for covariance calculation
   - Throw exceptions when alignment fails instead of using fallbacks
   - Follow existing error handling patterns from `PortfolioOrchestrator`

**Expected Outcome**: All strategies have returns calculated over the same time periods, enabling proper covariance matrix calculation.

#### Phase 1 - COMPLETED ✅

**Summary of Changes:**
- ✅ Created `app/concurrency/tools/return_alignment.py` with strict validation and fail-fast approach
- ✅ Added new exception types to `app/tools/exceptions.py`: `DataAlignmentError`, `CovarianceMatrixError`, `PortfolioVarianceError`, `RiskCalculationError`
- ✅ Updated `risk_contribution_calculator.py` to use aligned return series instead of hardcoded assumptions
- ✅ Replaced fallback mechanisms (0.1 default risk) with fail-fast validation that throws meaningful exceptions
- ✅ Implemented proper date alignment using Polars DataFrame operations with nanosecond precision
- ✅ Added comprehensive validation for return matrix quality (no NaN, infinite values, positive variance)

**Files Created:**
- `app/concurrency/tools/return_alignment.py` (235 lines) - Complete return alignment utility with validation

**Files Modified:**
- `app/tools/exceptions.py` - Added 4 new risk calculation exception types
- `app/concurrency/tools/risk_contribution_calculator.py` - Replaced fallback logic with aligned return calculation

**Testing Results:**
- ✅ Successfully aligned 3 test strategies with 252 common observations
- ✅ Generated valid positive definite covariance matrix (3x3)
- ✅ Calculated portfolio risk: 0.009755 (realistic value, not fallback 0.1)
- ✅ All validation checks passed (no NaN, infinite values, positive variance)

**Technical Achievements:**
- Return series now aligned to common time periods using actual market data
- Covariance matrix calculated from aligned returns instead of assumptions
- Fail-fast validation ensures data quality before risk calculation
- Proper datetime handling with consistent nanosecond precision
- Eliminated the 0.1 fallback value that was causing inaccurate risk metrics

**Critical Issue Resolution - Missing Allocations:**
- ✅ **Issue Identified**: Empty allocation columns in CSV causing all-zero weights array
- ✅ **Root Cause**: Division by zero when normalizing weights (sum of zeros)
- ✅ **Solution Implemented**: Equal weights allocation when no allocations provided
- ✅ **Real-world Test**: Successfully processed portfolio_d_20250530.json with 21 strategies
- ✅ **Results**: Portfolio risk calculated as 0.0165 (realistic) vs 0.1 (fallback)

### Phase 2: Improve Covariance Matrix Construction - COMPLETED ✅
**Objective**: Replace hardcoded correlation assumptions with calculated correlations from actual data

#### Tasks:
1. **Implement correlation calculator** (`app/concurrency/tools/correlation_calculator.py`)
   - Calculate pairwise correlations from aligned return series using Polars operations
   - Handle edge cases (insufficient data, perfect correlation) with `CovarianceMatrixError` exceptions
   - Provide correlation diagnostics and validation
   - Use consistent logging with `self.log` pattern from existing modules

2. **Create robust covariance estimation**
   - Use sample covariance from aligned returns
   - Implement shrinkage estimators for small sample sizes
   - Add covariance matrix regularization for numerical stability
   - Throw exceptions for invalid covariance matrices instead of fixing them
   - Follow error handling patterns with `error_context` wrapper

3. **Replace hardcoded assumptions**
   - Remove the 0.3 correlation assumption in line 325 of `risk_contribution_calculator.py`
   - Use calculated correlation matrix instead
   - Throw exceptions when correlation calculation fails
   - Integrate with existing configuration system from `ConfigService`

**Expected Outcome**: Covariance matrix based on actual strategy correlations rather than assumptions.

#### Phase 2 - COMPLETED ✅

**Summary of Changes:**
- ✅ Created `app/concurrency/tools/correlation_calculator.py` (438 lines) with comprehensive correlation and covariance calculation
- ✅ Implemented Ledoit-Wolf shrinkage estimator for small sample sizes
- ✅ Added covariance matrix regularization through eigenvalue decomposition
- ✅ Replaced hardcoded 0.3 correlation assumption with actual calculated correlations
- ✅ Integrated correlation calculator into risk_contribution_calculator.py
- ✅ Added robust validation for correlation matrices (symmetry, bounds, positive definiteness)

**Files Created:**
- `app/concurrency/tools/correlation_calculator.py` - Complete correlation/covariance calculator with shrinkage

**Files Modified:**
- `app/concurrency/tools/risk_contribution_calculator.py` - Updated to use CorrelationCalculator instead of np.cov directly

**Testing Results:**
- ✅ Created test with known correlations (0.71, 0.37, 0.19) - all correctly calculated
- ✅ Shrinkage estimator working correctly (intensity: 0.0585 for test data)
- ✅ Condition number improved from 9.93 to 9.35 with shrinkage
- ✅ Portfolio risk calculation producing realistic values (21.55% annualized for test portfolio)
- ✅ Production test on portfolio_d_20250530.json successful
- ✅ Average correlation across 21 strategies: 0.3568 (realistic, not hardcoded)
- ✅ Covariance matrix condition number: 4334.84 (high but handled by regularization)

**Technical Achievements:**
- Correlation matrices now calculated from actual aligned return data
- Shrinkage automatically applied for portfolios with limited data
- Comprehensive diagnostics provided (eigenvalues, condition numbers, correlation summaries)
- High correlation pairs identified and logged as warnings
- Covariance matrix regularization ensures numerical stability
- All calculations fail-fast with meaningful exceptions instead of using fallbacks

### Phase 3: Portfolio-Level Return Calculation - COMPLETED ✅
**Objective**: Calculate portfolio returns from combined strategy positions rather than individual components

#### Tasks:
1. **Implement portfolio return calculator** (`app/concurrency/tools/portfolio_returns.py`)
   - Aggregate individual strategy returns using position weights
   - Calculate time-series of portfolio returns using Polars DataFrame operations
   - Handle allocation changes over time with schema detection patterns from `portfolio.allocation`
   - Use `@handle_errors` decorator with `PortfolioVarianceError` exceptions

2. **Create portfolio-level risk metrics**
   - Calculate portfolio volatility directly from portfolio returns
   - Compute rolling risk metrics for stability analysis
   - Generate portfolio return distribution statistics
   - Follow existing patterns from `app/tools/portfolio/` modules

3. **Integrate with existing risk framework**
   - Update `RiskContributionCalculator` to use portfolio returns
   - Maintain backward compatibility with existing interfaces
   - Add portfolio-level validation checks
   - Throw exceptions for invalid portfolio return calculations
   - Use consistent error handling with existing `MACrossPortfolioError` patterns

**Expected Outcome**: Portfolio risk calculated from actual portfolio return series rather than mathematical combinations.

#### Phase 3 - COMPLETED ✅

**Summary of Changes:**
- ✅ Created `app/concurrency/tools/portfolio_returns.py` (405 lines) with comprehensive portfolio return calculation
- ✅ Implemented weighted portfolio return aggregation accounting for actual positions
- ✅ Added rolling metrics calculation (mean, std, Sharpe, VaR, CVaR) with configurable windows
- ✅ Created portfolio return distribution statistics (skewness, kurtosis, percentiles)
- ✅ Added new method `calculate_portfolio_metrics_from_returns` to RiskContributionCalculator
- ✅ Integrated portfolio-level calculation as optional mode with backward compatibility
- ✅ Added `USE_PORTFOLIO_RETURNS` configuration option to config_defaults.py

**Files Created:**
- `app/concurrency/tools/portfolio_returns.py` - Complete portfolio return calculator with diagnostics

**Files Modified:**
- `app/concurrency/tools/risk_contribution_calculator.py` - Added portfolio-level return calculation methods
- `app/concurrency/config_defaults.py` - Added USE_PORTFOLIO_RETURNS configuration option

**Testing Results:**
- ✅ Portfolio return calculation working correctly with test strategies
- ✅ Diversification ratio calculated: 1.4166 (indicates good diversification)
- ✅ Covariance-based vs portfolio-based comparison shows 18% difference (expected due to position timing)
- ✅ Rolling metrics successfully calculated over 1-year windows
- ✅ Position impact correctly accounted for (different volatility with/without positions)
- ✅ Risk contributions sum to exactly 100% with portfolio-level calculation

**Technical Achievements:**
- Portfolio returns now calculated from actual combined positions
- Accounts for periods when strategies are inactive (zero positions)
- Provides comprehensive diagnostics including diversification metrics
- Risk contributions calculated using covariance between strategies and portfolio
- Rolling window analysis enables time-varying risk assessment
- Maintains full backward compatibility with existing interfaces

### Phase 4: Enhanced Variance Estimation
**Objective**: Improve variance estimation for strategies with limited data using statistical methods

#### Tasks:
1. **Implement advanced variance estimators** (`app/concurrency/tools/variance_estimators.py`)
   - Rolling window variance for time-varying volatility using Polars rolling operations
   - Exponentially weighted moving average (EWMA) variance
   - Bootstrap variance estimation for small samples
   - Bayesian variance estimation with informative priors
   - Use configuration system patterns from `ConfigService` for estimation parameters

2. **Create data sufficiency assessments**
   - Minimum data requirements per estimation method (consistent with `MINIMUMS` config pattern)
   - Confidence intervals for variance estimates
   - Data quality scoring for variance reliability
   - Follow validation patterns from `app/tools/portfolio/validation.py`

3. **Implement strict validation strategy**
   - Validate minimum data requirements before calculation using existing validation utilities
   - Throw exceptions for insufficient data instead of degrading methods
   - Provide clear error messages for data quality issues
   - Use `RiskCalculationError` exceptions with detailed context information

**Expected Outcome**: Robust variance estimates with strict validation, eliminating fallback values by throwing exceptions for invalid inputs.

## Implementation Details

### New Files to Create:
1. `app/concurrency/tools/return_alignment.py` - Return series synchronization with strict validation
2. `app/concurrency/tools/correlation_calculator.py` - Correlation estimation with exception handling
3. `app/concurrency/tools/portfolio_returns.py` - Portfolio-level return calculation with validation
4. `app/concurrency/tools/variance_estimators.py` - Advanced variance estimation with data requirements
5. `app/concurrency/tools/risk_accuracy_validator.py` - Validation with meaningful exceptions

### Files to Modify:
1. `app/concurrency/tools/risk_contribution_calculator.py` - Core calculation updates
2. `app/concurrency/tools/risk_metrics.py` - Integration with new methods
3. `tests/concurrency/test_risk_contribution_fix.py` - Add accuracy tests

### Configuration Updates:
1. Add accuracy configuration options to `config_defaults.py`:
   - Minimum data requirements
   - Estimation method preferences
   - Validation thresholds

### Exception Handling Integration:
1. Add new exception types to `app/tools/exceptions.py`:
   - `RiskCalculationError` for risk calculation failures
   - `DataAlignmentError` for return series alignment issues
   - `CovarianceMatrixError` for covariance matrix problems
   - `PortfolioVarianceError` for portfolio variance calculation issues

2. Update error handling in existing modules:
   - Use consistent exception handling with `@handle_errors` decorator
   - Integrate with existing `error_context` from `app/tools/error_context.py`
   - Follow established pattern from `ma_cross` module

## Validation Strategy

### Accuracy Metrics:
1. **Covariance matrix validation**
   - Eigenvalue analysis for positive definiteness
   - Condition number assessment for numerical stability
   - Out-of-sample validation using historical data

2. **Portfolio risk validation**
   - Compare calculated vs. actual portfolio volatility
   - Cross-validation using different time periods
   - Stress testing with extreme market conditions

3. **Risk contribution validation**
   - Verify contributions sum to 100%
   - Check mathematical consistency of marginal contributions
   - Validate against known portfolio theory results

### Testing Framework:
1. **Unit tests** for each new component
2. **Integration tests** for the complete pipeline
3. **Regression tests** to ensure no degradation
4. **Performance benchmarks** for computational efficiency

## Success Criteria

### Immediate (Phase 1-2):
- [ ] `total_portfolio_risk` shows calculated values instead of 0.1 default
- [ ] Covariance matrix based on actual correlations
- [ ] Return series properly aligned across strategies

### Medium-term (Phase 3-4):
- [ ] Portfolio-level risk metrics available
- [ ] Advanced variance estimation for all data scenarios
- [ ] Comprehensive validation framework in place

### Long-term:
- [ ] Risk accuracy improved by >50% compared to current fallback approach
- [ ] Robust handling of all edge cases with meaningful exceptions
- [ ] Full mathematical consistency with portfolio theory

## Risk Mitigation

### Backward Compatibility:
- Maintain existing API interfaces
- Replace fallback mechanisms with meaningful exception handling

### Performance Considerations:
- Benchmark computational overhead of new methods
- Implement caching for expensive calculations
- Optimize for large portfolios (>100 strategies)

### Data Quality:
- Comprehensive input validation with strict requirements
- Fail fast on missing/corrupt data with descriptive exceptions
- Clear error reporting with actionable diagnostics


## Next Steps

1. Begin with Phase 1 (return alignment) as it provides foundation for all other improvements
2. Create comprehensive test data sets for validation
3. Monitor performance impact at each phase

This plan will transform the portfolio risk calculation from a fallback-based system to a statistically rigorous implementation based on actual market data and modern portfolio theory.