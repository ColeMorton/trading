# Monte Carlo Framework Migration Guide

## Overview

The Monte Carlo parameter robustness testing functionality has been refactored from strategy-specific modules to a comprehensive portfolio-level framework integrated with the concurrency analysis system. This migration guide helps you update existing code to use the new framework.

## What Changed

### Old Architecture (Deprecated)

- **Location**: `app/strategies/ma_cross/monte_carlo_integration.py`
- **Scope**: Single-ticker, strategy-specific analysis
- **Usage**: `MonteCarloEnhancedAnalyzer` class
- **Performance**: Sequential processing

### New Architecture (Recommended)

- **Location**: `app/concurrency/tools/monte_carlo/`
- **Scope**: Portfolio-level, multi-ticker analysis
- **Usage**: `PortfolioMonteCarloManager` class
- **Performance**: Concurrent processing with resource management

## Migration Steps

### 1. Import Changes

**Before (Deprecated):**

```python
from app.strategies.ma_cross.monte_carlo_integration import MonteCarloEnhancedAnalyzer
from app.strategies.monte_carlo.parameter_robustness import MonteCarloConfig
```

**After (Recommended):**

```python
from app.concurrency.tools.monte_carlo import (
    PortfolioMonteCarloManager,
    MonteCarloConfig,
    create_monte_carlo_config,
)
```

### 2. Configuration Changes

**Before:**

```python
# Legacy MonteCarloConfig
mc_config = MonteCarloConfig(
    num_simulations=1000,
    confidence_level=0.95,
    bootstrap_block_size=63
)
```

**After:**

```python
# New configuration format
config_dict = {
    "MC_INCLUDE_IN_REPORTS": True,
    "MC_NUM_SIMULATIONS": 1000,
    "MC_CONFIDENCE_LEVEL": 0.95,
    "MC_MAX_PARAMETERS_TO_TEST": 10,
}
mc_config = create_monte_carlo_config(config_dict)
```

### 3. Analysis Setup Changes

**Before:**

```python
# Single-ticker analysis
analyzer = MonteCarloEnhancedAnalyzer(
    parameter_config=param_config,
    mc_config=mc_config,
    robustness_threshold=0.7
)
results = analyzer.run_enhanced_analysis()
```

**After:**

```python
# Portfolio-level analysis
manager = PortfolioMonteCarloManager(
    config=mc_config,
    max_workers=4,
    log=log_function
)

# Convert strategies to new format
strategies = [
    {
        "ticker": "AAPL",
        "MA Type": "EMA",
        "Window Short": 10,
        "Window Long": 20,
    },
    {
        "ticker": "MSFT",
        "MA Type": "SMA",
        "Window Short": 15,
        "Window Long": 30,
    },
]

results = manager.analyze_portfolio(strategies)
```

### 4. Results Format Changes

**Before:**

```python
# Legacy results structure
{
    "standard_results": [...],
    "robust_parameters": [...],
    "recommendations": [...],
    "summary": {...}
}
```

**After:**

```python
# New results structure (per ticker)
{
    "AAPL": MonteCarloPortfolioResult(
        ticker="AAPL",
        parameter_results=[...],
        portfolio_stability_score=0.8,
        recommended_parameters=(10, 20)
    ),
    "MSFT": MonteCarloPortfolioResult(...)
}

# Portfolio-level metrics
portfolio_metrics = manager.get_portfolio_stability_metrics()
recommendations = manager.get_recommendations()
```

## Compatibility Layer

A compatibility layer is provided to ease migration. The old interface still works but issues deprecation warnings:

```python
# This still works but is deprecated
from app.strategies.ma_cross.monte_carlo_integration import MonteCarloEnhancedAnalyzer

# Issues deprecation warning
analyzer = MonteCarloEnhancedAnalyzer(param_config)
results = analyzer.run_enhanced_analysis()  # Uses new framework under the hood
```

## Integration with Concurrency Analysis

### Automatic Integration

The new Monte Carlo framework integrates automatically with the concurrency review pipeline:

```python
# In concurrency config
config = {
    "PORTFOLIO": "portfolio.csv",
    "MC_INCLUDE_IN_REPORTS": True,  # Enable Monte Carlo
    "MC_NUM_SIMULATIONS": 500,
    "VISUALIZATION": True,  # Generate Monte Carlo visualizations
}

# Run concurrency analysis (automatically includes Monte Carlo)
python -m app.concurrency.review
```

### Manual Integration

You can also run Monte Carlo analysis independently:

```python
from app.concurrency.tools.monte_carlo import (
    PortfolioMonteCarloManager,
    create_monte_carlo_config,
    create_monte_carlo_visualizations,
)

# Setup
config = create_monte_carlo_config({
    "MC_INCLUDE_IN_REPORTS": True,
    "MC_NUM_SIMULATIONS": 1000,
})

manager = PortfolioMonteCarloManager(config)

# Analyze
results = manager.analyze_portfolio(strategies)
portfolio_metrics = manager.get_portfolio_stability_metrics()

# Visualize
viz_paths = create_monte_carlo_visualizations(results, portfolio_metrics)
```

## Benefits of Migration

### Performance Improvements

- **Concurrent Processing**: Multi-ticker analysis runs in parallel
- **Resource Management**: Configurable worker limits and memory management
- **Progress Tracking**: Real-time progress monitoring with error isolation

### Enhanced Capabilities

- **Portfolio-Level Analysis**: Analyze multiple tickers simultaneously
- **Comprehensive Reporting**: Integrated JSON reports with portfolio metrics
- **Advanced Visualizations**: Portfolio heatmaps, distribution plots, summary dashboards
- **Error Resilience**: Individual ticker failures don't stop portfolio analysis

### Integration Benefits

- **Unified Pipeline**: Single command runs both concurrency and Monte Carlo analysis
- **Consistent Configuration**: Uses same configuration system as concurrency framework
- **Shared Infrastructure**: Leverages existing error handling, logging, and visualization systems

## Configuration Options

### Basic Configuration

```python
config = {
    "MC_INCLUDE_IN_REPORTS": True,      # Enable Monte Carlo analysis
    "MC_NUM_SIMULATIONS": 100,          # Number of simulations (beginner-friendly)
    "MC_CONFIDENCE_LEVEL": 0.95,        # Statistical confidence level
    "MC_MAX_PARAMETERS_TO_TEST": 10,    # Limit for performance
}
```

### Advanced Configuration

```python
config = {
    "MC_INCLUDE_IN_REPORTS": True,
    "MC_NUM_SIMULATIONS": 1000,         # More simulations for better accuracy
    "MC_CONFIDENCE_LEVEL": 0.99,        # Higher confidence level
    "MC_MAX_PARAMETERS_TO_TEST": 50,    # Test more parameter combinations
    "MC_MAX_WORKERS": 8,                # More concurrent workers
    "VISUALIZATION": True,               # Generate visualizations
}
```

## Common Migration Issues

### 1. Parameter Format Differences

**Issue**: Old format used `ParameterTestingConfig`, new format uses strategy dictionaries.

**Solution**: Convert parameter configs to strategy format:

```python
# Convert old parameter config
strategies = []
for ticker in param_config.tickers:
    for short in range(5, param_config.windows):
        for long in range(param_config.windows, param_config.windows * 2):
            strategies.append({
                "ticker": ticker,
                "MA Type": "EMA",
                "Window Short": short,
                "Window Long": long,
            })
```

### 2. Results Structure Changes

**Issue**: Results format changed from flat dictionaries to typed objects.

**Solution**: Access results using object attributes:

```python
# Old way
stability_score = result["stability_score"]

# New way
stability_score = result.stability_score
```

### 3. Configuration Key Names

**Issue**: Configuration keys changed to use MC\_ prefix.

**Solution**: Update configuration keys:

```python
# Old keys
"num_simulations" → "MC_NUM_SIMULATIONS"
"confidence_level" → "MC_CONFIDENCE_LEVEL"

# Add new required keys
"MC_INCLUDE_IN_REPORTS": True
"MC_MAX_PARAMETERS_TO_TEST": 10
```

## Testing Migration

Use the provided test script to verify your migration:

```bash
# Test compatibility layer
python app/strategies/ma_cross/test_monte_carlo_integration.py

# Test new framework directly
python -m pytest app/concurrency/tools/monte_carlo/test_integration.py -v
```

## Timeline and Support

### Deprecation Timeline

- **Phase 1**: Compatibility layer active (current)
- **Phase 2**: Deprecation warnings issued
- **Phase 3**: Legacy interface removal (future release)

### Migration Support

- **Compatibility Layer**: Maintains old interface while using new framework
- **Documentation**: Comprehensive migration guide and examples
- **Testing**: Test scripts to verify migration correctness

## Examples

### Complete Migration Example

**Before:**

```python
from app.strategies.ma_cross.monte_carlo_integration import MonteCarloEnhancedAnalyzer
from app.strategies.ma_cross.config.parameter_testing import ParameterTestingConfig
from app.strategies.monte_carlo.parameter_robustness import MonteCarloConfig

# Setup
param_config = ParameterTestingConfig(
    tickers=["AAPL", "MSFT"],
    windows=50,
    strategy_types=["EMA"]
)

mc_config = MonteCarloConfig(
    num_simulations=1000,
    confidence_level=0.95
)

# Analysis
analyzer = MonteCarloEnhancedAnalyzer(param_config, mc_config)
results = analyzer.run_enhanced_analysis()

# Access results
recommendations = results["recommendations"]
```

**After:**

```python
from app.concurrency.tools.monte_carlo import (
    PortfolioMonteCarloManager,
    create_monte_carlo_config,
    create_monte_carlo_visualizations,
)

# Setup
config = create_monte_carlo_config({
    "MC_INCLUDE_IN_REPORTS": True,
    "MC_NUM_SIMULATIONS": 1000,
    "MC_CONFIDENCE_LEVEL": 0.95,
    "MC_MAX_PARAMETERS_TO_TEST": 20,
})

strategies = [
    {"ticker": "AAPL", "MA Type": "EMA", "Window Short": 10, "Window Long": 20},
    {"ticker": "AAPL", "MA Type": "EMA", "Window Short": 15, "Window Long": 30},
    {"ticker": "MSFT", "MA Type": "EMA", "Window Short": 10, "Window Long": 25},
    {"ticker": "MSFT", "MA Type": "EMA", "Window Short": 12, "Window Long": 30},
]

# Analysis
manager = PortfolioMonteCarloManager(config)
results = manager.analyze_portfolio(strategies)

# Access results
portfolio_metrics = manager.get_portfolio_stability_metrics()
recommendations = manager.get_recommendations()

# Generate visualizations
viz_paths = create_monte_carlo_visualizations(results, portfolio_metrics)
```

## Need Help?

- **Documentation**: See `/architect/monte_carlo_refactoring_plan.md` for technical details
- **Examples**: Check `/app/concurrency/tools/monte_carlo/test_integration.py` for usage examples
- **Compatibility**: Use the compatibility layer during migration
- **Issues**: Review test scripts for common migration patterns

The new Monte Carlo framework provides significant improvements in performance, capabilities, and integration while maintaining backward compatibility during the migration period.
