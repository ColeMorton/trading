# Implementation Plan for Optimized JSON Structure

## 1. Update Type Definitions (types.py)

### New Type Definitions Required:

```python
class StrategyParameters(TypedDict):
    """Parameters for a trading strategy."""
    ticker: Dict[str, Union[str, Any]]
    timeframe: Dict[str, Union[str, Any]]
    type: Dict[str, Union[str, Any]]
    direction: Dict[str, Union[str, Any]]
    short_window: Dict[str, Union[int, str]]
    long_window: Dict[str, Union[int, str]]

class StrategyPerformance(TypedDict):
    """Performance metrics for a strategy."""
    expectancy_per_month: Dict[str, Union[float, str]]

class StrategyRiskMetrics(TypedDict):
    """Risk metrics for a strategy."""
    var_95: Dict[str, Union[float, str]]
    cvar_95: Dict[str, Union[float, str]]
    var_99: Dict[str, Union[float, str]]
    cvar_99: Dict[str, Union[float, str]]
    risk_contribution: Dict[str, Union[float, str]]
    alpha: Dict[str, Union[float, str]]

class Strategy(TypedDict):
    """Complete strategy definition."""
    id: str
    parameters: StrategyParameters
    performance: StrategyPerformance
    risk_metrics: StrategyRiskMetrics

class ConcurrencyMetrics(TypedDict):
    """Concurrency-related metrics."""
    total_concurrent_periods: Dict[str, Union[int, str]]
    concurrency_ratio: Dict[str, Union[float, str]]
    exclusive_ratio: Dict[str, Union[float, str]]
    inactive_ratio: Dict[str, Union[float, str]]
    avg_concurrent_strategies: Dict[str, Union[float, str]]
    max_concurrent_strategies: Dict[str, Union[int, str]]

class EfficiencyMetrics(TypedDict):
    """Efficiency-related metrics."""
    efficiency_score: Dict[str, Union[float, str]]
    total_expectancy: Dict[str, Union[float, str]]
    multipliers: Dict[str, Dict[str, Union[float, str]]]

class RiskMetrics(TypedDict):
    """Portfolio risk metrics."""
    portfolio_metrics: Dict[str, Dict[str, Union[float, str]]]
    combined_risk: Dict[str, Dict[str, Union[float, str]]]
    strategy_relationships: Dict[str, Dict[str, Union[float, str]]]

class SignalMetrics(TypedDict):
    """Signal-related metrics."""
    monthly_statistics: Dict[str, Dict[str, Union[float, str]]]
    summary: Dict[str, Dict[str, Union[float, str]]]

class PortfolioMetrics(TypedDict):
    """Complete portfolio metrics."""
    concurrency: ConcurrencyMetrics
    efficiency: EfficiencyMetrics
    risk: RiskMetrics
    signals: SignalMetrics

class OptimizedConcurrencyReport(TypedDict):
    """Complete optimized report structure."""
    strategies: List[Strategy]
    portfolio_metrics: PortfolioMetrics
```

## 2. Update Report Generation (report.py)

### Changes Required:

1. Modify generate_json_report function to:
   - Add strategy IDs
   - Restructure strategy objects
   - Group portfolio metrics more logically
   - Improve metric organization

2. Add helper functions:
   ```python
   def create_strategy_object(config: StrategyConfig, index: int) -> Strategy:
       """Create a strategy object with the new structure."""
       pass

   def create_portfolio_metrics(stats: Dict[str, Any]) -> PortfolioMetrics:
       """Create portfolio metrics with the new structure."""
       pass
   ```

3. Update metric grouping:
   - Move strategy-specific metrics into strategy objects
   - Group portfolio-level metrics more logically
   - Create clear hierarchy for metrics

## 3. Update Runner Logic (runner.py)

### Changes Required:

1. Ensure strategy processing adds required fields:
   - Add strategy IDs during processing
   - Calculate and include all required metrics

2. Update run_analysis function to:
   - Pass complete strategy information to report generator
   - Include all required metrics in statistics

## 4. Migration Steps

1. Create new type definitions
2. Update report generation logic
3. Modify runner to support new structure
4. Add validation for new structure
5. Test with existing data
6. Update any dependent code

## 5. Testing Plan

1. Unit Tests:
   - Test new type definitions
   - Test report generation
   - Test metric calculations

2. Integration Tests:
   - Test complete workflow
   - Verify output structure
   - Validate metric values

3. Validation:
   - Ensure all required fields are present
   - Verify metric calculations
   - Check data consistency

## 6. Implementation Order

1. Update types.py with new definitions
2. Create helper functions in report.py
3. Update main report generation logic
4. Modify runner.py to support new structure
5. Add validation
6. Test and verify
7. Update documentation

## 7. Backward Compatibility

Consider adding a version flag to support both old and new formats during transition:

```python
def generate_json_report(
    strategies: List[StrategyConfig],
    stats: Dict[str, Any],
    log: Callable[[str, str], None],
    use_new_format: bool = True
) -> Dict[str, Any]:
    """Generate report in either old or new format."""
    pass
```

This allows for gradual migration of dependent code.