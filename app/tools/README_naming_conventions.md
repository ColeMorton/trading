# Signal Processing Naming Conventions

This document establishes standard naming conventions for the signal processing codebase to ensure consistency and clarity across all modules.

## General Principles

1. **Consistency**: Use the same naming pattern for similar concepts across all modules
2. **Clarity**: Names should clearly indicate the purpose and content
3. **Specificity**: Names should be specific enough to avoid ambiguity
4. **Brevity**: Names should be concise while maintaining clarity

## File Naming Conventions

1. All Python files should use `snake_case` (lowercase with underscores)
2. Module names should reflect their primary purpose (e.g., `signal_filtering.py`)
3. Test files should be prefixed with `test_` (e.g., `test_signal_metrics.py`)
4. Documentation files should be prefixed with `README_` (e.g., `README_metrics.md`)

## Variable Naming Conventions

1. All variable names should use `snake_case`
2. Boolean variables should use prefixes like `is_`, `has_`, or `should_` (e.g., `is_valid`, `has_signals`)
3. Constants should use `UPPER_SNAKE_CASE` (e.g., `MAX_WINDOW_SIZE`)
4. Private variables (not intended for external use) should be prefixed with underscore (e.g., `_internal_cache`)

## Function Naming Conventions

1. All function names should use `snake_case`
2. Functions should be named with verb phrases that describe their action (e.g., `calculate_metrics`, `normalize_data`)
3. Boolean functions should use prefixes like `is_`, `has_`, or `should_` (e.g., `is_valid_signal`)
4. Private functions should be prefixed with underscore (e.g., `_calculate_internal_value`)

## Class Naming Conventions

1. Class names should use `PascalCase` (e.g., `SignalProcessor`, `MetricsCalculator`)
2. Abstract base classes should be prefixed with `Abstract` (e.g., `AbstractFilter`)
3. Interface classes should be suffixed with `Interface` (e.g., `FilterInterface`)
4. Exception classes should be suffixed with `Error` or `Exception` (e.g., `InvalidSignalError`)

## Metric Naming Conventions

1. All metric names should use `snake_case`
2. Metrics should be grouped by category with consistent prefixes:
   - Signal metrics: `signal_*` (e.g., `signal_count`, `signal_quality_score`)
   - Return metrics: `return_*` (e.g., `return_mean`, `return_volatility`)
   - Risk metrics: `risk_*` (e.g., `risk_adjusted_return`, `risk_drawdown`)
   - Performance metrics: `performance_*` (e.g., `performance_sharpe`, `performance_sortino`)
   - Portfolio metrics: `portfolio_*` (e.g., `portfolio_diversification`, `portfolio_correlation`)
3. Composite metrics should indicate their composition (e.g., `risk_reward_ratio`, `win_loss_ratio`)
4. Normalized metrics should be prefixed with `norm_` (e.g., `norm_return`, `norm_volatility`)
5. Raw (unnormalized) metrics should be prefixed with `raw_` when distinction is necessary

## Parameter Naming Conventions

1. All parameter names should use `snake_case`
2. Window parameters should be suffixed with `_window` (e.g., `ma_window`, `rsi_window`)
3. Threshold parameters should be suffixed with `_threshold` (e.g., `signal_threshold`, `rsi_threshold`)
4. Boolean parameters should use prefixes like `use_`, `is_`, or `has_` (e.g., `use_rsi`, `is_normalized`)
5. Configuration parameters should be grouped logically and use consistent naming within groups

## Dictionary Key Naming Conventions

1. Dictionary keys should follow the same conventions as variables (`snake_case`)
2. Keys representing the same concept across different dictionaries should use identical names
3. Nested dictionaries should use increasingly specific names (e.g., `metrics` → `signal_metrics` → `signal_quality_metrics`)

## Implementation Guidelines

1. When refactoring existing code to follow these conventions, ensure backward compatibility through appropriate deprecation warnings
2. Document any deviations from these conventions with clear rationale
3. Update all references to renamed elements throughout the codebase
4. Maintain consistent naming in both code and documentation