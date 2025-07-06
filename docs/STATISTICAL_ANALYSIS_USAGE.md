# Statistical Performance Divergence System - Usage Guide

## Overview

The Statistical Performance Divergence System (SPDS) provides advanced statistical analysis capabilities for trading strategy optimization, exit timing, and portfolio management with a **dramatically simplified interface**.

**Key Simplification**: The entire system now requires only **TWO parameters**:

1. **PORTFOLIO** - Portfolio filename (e.g., "risk_on.csv")
2. **USE_TRADE_HISTORY** - Data source: trade history (True) or equity curves (False)

Files are automatically located:

- **Portfolio**: `./csv/strategies/{portfolio}`
- **Trade History**: `./csv/positions/{portfolio}` (same filename)

## Table of Contents

1. [Quick Start](#quick-start)
2. [Simplified Interface](#simplified-interface)
3. [Portfolio-Based Analysis](#portfolio-based-analysis)
4. [Machine Learning Features](#machine-learning-features)
5. [Portfolio Optimization](#portfolio-optimization)
6. [Performance Validation](#performance-validation)
7. [Advanced Usage](#advanced-usage)
8. [Migration Guide](#migration-guide)

## Quick Start

### Simplified Portfolio Analysis (Recommended)

```python
from app.tools.portfolio_analyzer import analyze_portfolio

# ONE LINE portfolio analysis - that's it!
results, summary = await analyze_portfolio("risk_on.csv", use_trade_history=True)

# View results
print(f"Portfolio: {summary['portfolio']}")
print(f"Total strategies: {summary['total_strategies']}")
print(f"Immediate exits: {summary['immediate_exits']}")
print(f"Strong sells: {summary['strong_sells']}")
print(f"Confidence rate: {summary['confidence_rate']:.1%}")

# Get individual exit signals
exit_signals = analyzer.get_exit_signals(results)
for strategy, signal in exit_signals.items():
    print(f"{strategy}: {signal}")
```

### Class-Based Interface

```python
from app.tools.portfolio_analyzer import PortfolioStatisticalAnalyzer

# Initialize with portfolio and data source preference
analyzer = PortfolioStatisticalAnalyzer("risk_on.csv", use_trade_history=True)

# Analyze entire portfolio
results = await analyzer.analyze()
summary = analyzer.get_summary_report(results)

print(f"Analysis complete for {summary['total_strategies']} strategies")
print(f"Signal distribution: {summary['signal_distribution']}")
```

## Simplified Interface

### Two-Parameter Configuration

The system has been dramatically simplified from 20+ configuration parameters to just 2:

```python
from app.tools.config.statistical_analysis_config import StatisticalAnalysisConfig

# Simple configuration - just portfolio and data source
config = StatisticalAnalysisConfig.create(
    portfolio="risk_on.csv",           # Portfolio filename
    use_trade_history=True             # Use trade history or equity curves
)

# Automatic path resolution
print(f"Portfolio file: {config.get_portfolio_file_path()}")          # ./csv/strategies/risk_on.csv
print(f"Trade history: {config.get_trade_history_file_path()}")       # ./csv/positions/risk_on.csv
```

### File Structure Convention

```
./csv/strategies/risk_on.csv     # Portfolio definition (required)
./csv/positions/risk_on.csv      # Trade history (optional, same filename)
./json/return_distribution/      # Asset return data (auto-loaded)
```

### Portfolio CSV Format

Your portfolio CSV should contain strategy definitions:

```csv
strategy_name,ticker,allocation,risk_level
AAPL_SMA_20_50,AAPL,0.15,medium
TSLA_EMA_12_26,TSLA,0.12,high
NVDA_SMA_15_35,NVDA,0.10,high
MSFT_EMA_21_50,MSFT,0.08,low
```

### Trade History CSV Format (Optional)

If using `use_trade_history=True`, place trade history in `./csv/positions/` with same filename:

```csv
strategy_name,ticker,entry_date,exit_date,return,mfe,mae,duration_days,trade_quality
AAPL_SMA_20_50,AAPL,2024-01-15,2024-02-28,0.187,0.234,0.057,44,excellent
TSLA_EMA_12_26,TSLA,2024-02-01,2024-03-15,0.143,0.189,0.034,43,good
NVDA_SMA_15_35,NVDA,2024-03-01,2024-04-12,0.312,0.387,0.089,42,excellent
```

### Machine Learning Pattern Recognition

```python
from app.tools.ml.pattern_recognition_ml import PatternRecognitionML
import pandas as pd

# Initialize ML engine
ml_engine = PatternRecognitionML()

# Prepare historical data
historical_data = pd.read_csv("historical_trades.csv")

# Fit ML models
ml_engine.fit(historical_data)

# Find similar patterns
pattern_matches = ml_engine.find_similar_patterns(
    position, result, top_k=3
)

for match in pattern_matches:
    print(f"Pattern: {match.pattern_type}")
    print(f"Similarity: {match.similarity_score:.1%}")
    print(f"Recommendation: {match.recommendation}")
```

### Portfolio Optimization

```python
from app.tools.portfolio.cross_strategy_optimizer import CrossStrategyOptimizer
from app.tools.portfolio.dynamic_position_sizer import DynamicPositionSizer

# Initialize optimizer
optimizer = CrossStrategyOptimizer()
sizer = DynamicPositionSizer()

# Optimize portfolio allocation
optimization_result = optimizer.optimize_portfolio(
    positions, analysis_results, historical_returns
)

# Calculate dynamic position sizes
sizing_result = sizer.calculate_portfolio_sizing(
    positions, analysis_results, total_capital=100000
)

print(f"Optimal Weights: {optimization_result.optimal_weights}")
print(f"Expected Sharpe: {optimization_result.sharpe_ratio:.2f}")
```

## Configuration

### Statistical Analysis Configuration

```python
from app.tools.config.statistical_analysis_config import StatisticalAnalysisConfig, ConfidenceLevel

config = StatisticalAnalysisConfig(
    # Data Source Selection
    USE_TRADE_HISTORY=True,              # Use individual trade data
    TRADE_HISTORY_PATH="./csv/positions/", # Path to trade history CSVs
    FALLBACK_TO_EQUITY=True,             # Fallback to equity data if unavailable

    # Statistical Thresholds
    PERCENTILE_THRESHOLD=95,             # Exit at 95th percentile
    DUAL_LAYER_THRESHOLD=0.85,          # Dual-layer convergence threshold
    RARITY_THRESHOLD=0.05,              # Statistical rarity threshold (5%)
    MULTI_TIMEFRAME_AGREEMENT=3,        # Require 3+ timeframes agreement

    # Sample Size Requirements
    SAMPLE_SIZE_MINIMUM=15,             # Minimum trades for analysis
    CONFIDENCE_LEVELS=ConfidenceLevel(
        high_confidence=30,             # 30+ trades = high confidence
        medium_confidence=15,           # 15-29 trades = medium confidence
        low_confidence=5                # 5-14 trades = low confidence
    ),

    # Performance Optimization
    ENABLE_MEMORY_OPTIMIZATION=True,    # Enable memory optimization
    ENABLE_CACHING=True,               # Enable result caching
    CACHE_TTL_SECONDS=3600             # Cache for 1 hour
)
```

### ML Configuration

```python
from app.tools.ml.pattern_recognition_ml import PatternRecognitionML
from app.tools.ml.adaptive_learning_engine import AdaptiveLearningEngine

# Pattern Recognition Configuration
ml_config = {
    'min_similarity_threshold': 0.75,    # Minimum pattern similarity
    'anomaly_contamination': 0.1,        # Expected anomaly rate
    'n_neighbors': 5,                    # KNN neighbors
    'min_cluster_size': 3                # Minimum cluster size
}

ml_engine = PatternRecognitionML(**ml_config)

# Adaptive Learning Configuration
learning_config = {
    'learning_rate': 0.1,               # Threshold update rate
    'exploration_rate': 0.2,            # Exploration vs exploitation
    'min_samples_for_update': 10,       # Minimum samples before updating
    'optimization_window_days': 30      # Days of history for optimization
}

learning_engine = AdaptiveLearningEngine(**learning_config)
```

## Core Statistical Analysis

### Dual-Layer Analysis

The system uses dual-layer analysis combining asset-level and strategy-level statistics:

```python
# Layer 1: Asset Return Distribution Analysis
# Analyzes asset performance in market context

# Layer 2: Strategy Performance Analysis
# Analyzes strategy-specific performance patterns

# Example: Analyzing dual-layer convergence
if result.divergence_analysis:
    asset_percentile = result.divergence_analysis.asset_layer.current_percentile
    strategy_percentile = result.divergence_analysis.strategy_layer.current_percentile
    convergence_score = result.divergence_analysis.dual_layer_convergence_score

    print(f"Asset Percentile: {asset_percentile:.1f}")
    print(f"Strategy Percentile: {strategy_percentile:.1f}")
    print(f"Convergence Score: {convergence_score:.2f}")

    if convergence_score > 0.85:
        print("Strong dual-layer convergence - HIGH EXIT SIGNAL")
    elif convergence_score > 0.70:
        print("Moderate convergence - MONITOR FOR EXIT")
    else:
        print("Weak convergence - HOLD POSITION")
```

### Exit Signal Generation

```python
# Comprehensive exit signal analysis
if result.exit_signals:
    signals = result.exit_signals

    print(f"Primary Signal: {signals.primary_signal}")
    print(f"Secondary Signals: {signals.secondary_signals}")
    print(f"Confidence: {signals.confidence:.1%}")
    print(f"Signal Strength: {signals.signal_strength}")

    # Detailed signal breakdown
    for timeframe, signal in signals.timeframe_signals.items():
        print(f"{timeframe}: {signal}")

    # Risk assessment
    if signals.risk_assessment:
        risk = signals.risk_assessment
        print(f"Risk Level: {risk.risk_level}")
        print(f"VaR Estimate: {risk.var_estimate:.1%}")
        print(f"Confidence Interval: {risk.confidence_interval}")
```

### Trade History Analysis

```python
# When USE_TRADE_HISTORY=True
if config.USE_TRADE_HISTORY:
    # Individual trade analysis
    trade_analysis = result.trade_analysis

    if trade_analysis:
        print(f"Trade Return Distribution:")
        print(f"  Mean: {trade_analysis.mean_return:.1%}")
        print(f"  Median: {trade_analysis.median_return:.1%}")
        print(f"  Std Dev: {trade_analysis.std_return:.1%}")

        print(f"MFE Analysis:")
        print(f"  Current MFE Percentile: {trade_analysis.mfe_percentile:.1f}")
        print(f"  MFE Capture Ratio: {trade_analysis.mfe_capture_ratio:.2f}")

        print(f"Exit Efficiency:")
        print(f"  Historical Avg: {trade_analysis.avg_exit_efficiency:.1%}")
        print(f"  Current Position: {trade_analysis.current_exit_efficiency:.1%}")
```

## Machine Learning Features

### Pattern Recognition

```python
from app.tools.ml.pattern_recognition_ml import PatternRecognitionML

# Initialize and train ML engine
ml_engine = PatternRecognitionML(
    min_similarity_threshold=0.75,
    anomaly_contamination=0.1
)

# Training data should include:
# - return, mfe, mae, duration_days
# - mfe_mae_ratio, exit_efficiency
# - asset_percentile, strategy_percentile
# - dual_layer_score, statistical_rarity

training_data = pd.DataFrame({
    'return': historical_returns,
    'mfe': historical_mfe,
    'mae': historical_mae,
    'duration_days': historical_duration,
    'exit_efficiency': historical_exit_efficiency,
    # ... other features
})

ml_engine.fit(training_data)

# Pattern matching
pattern_matches = ml_engine.find_similar_patterns(position, analysis_result, top_k=5)

for match in pattern_matches:
    print(f"Pattern Type: {match.pattern_type}")
    print(f"Similarity: {match.similarity_score:.1%}")
    print(f"Historical Outcome: {match.historical_outcome:.1%}")
    print(f"Recommendation: {match.recommendation}")
    print(f"Expected Outcome: {match.expected_outcome}")
    print(f"Matched Features: {match.matched_features}")
    print("---")
```

### Anomaly Detection

```python
# Detect anomalous positions
anomaly_result = ml_engine.detect_anomalies(position, analysis_result)

print(f"Is Anomaly: {anomaly_result.is_anomaly}")
print(f"Anomaly Score: {anomaly_result.anomaly_score:.3f}")
print(f"Anomaly Type: {anomaly_result.anomaly_type}")
print(f"Confidence: {anomaly_result.confidence:.1%}")
print(f"Contributing Features: {anomaly_result.contributing_features}")
print(f"Recommendation: {anomaly_result.recommendation}")

# Handle anomalies
if anomaly_result.is_anomaly:
    if anomaly_result.anomaly_type == "statistical_outlier":
        print("⚠️  Statistical outlier detected - consider immediate exit")
    elif anomaly_result.anomaly_type == "performance_outlier":
        print("🎯 Performance outlier - capture exceptional gains")
```

### Adaptive Learning

```python
from app.tools.ml.adaptive_learning_engine import AdaptiveLearningEngine

# Initialize adaptive learning
learning_engine = AdaptiveLearningEngine(
    learning_rate=0.1,
    exploration_rate=0.2
)

# Optimize thresholds based on performance
current_thresholds = service._create_thresholds_from_config()

optimization_result = learning_engine.optimize_thresholds(
    historical_trades=recent_trade_data,
    current_thresholds=current_thresholds,
    target_metric="exit_efficiency"
)

print(f"Optimization Method: {optimization_result.optimization_method}")
print(f"Expected Improvement: {optimization_result.expected_improvement:.1%}")
print(f"Converged: {optimization_result.convergence_achieved}")

# Apply optimized thresholds
if optimization_result.expected_improvement > 0.05:  # 5% improvement
    optimized_config = config
    optimized_config.PERCENTILE_THRESHOLD = optimization_result.optimal_thresholds.percentile_threshold
    optimized_config.DUAL_LAYER_THRESHOLD = optimization_result.optimal_thresholds.dual_layer_threshold

    print("Applied optimized thresholds")
```

## Portfolio Optimization

### Cross-Strategy Optimization

```python
from app.tools.portfolio.cross_strategy_optimizer import CrossStrategyOptimizer

# Initialize optimizer
optimizer = CrossStrategyOptimizer(
    min_correlation_threshold=0.3,
    max_position_weight=0.4,
    min_position_weight=0.05
)

# Analyze strategy correlations
correlations = optimizer.analyze_strategy_correlations(
    positions, historical_returns
)

for corr in correlations:
    print(f"{corr.strategy1} ↔ {corr.strategy2}")
    print(f"  Pearson: {corr.pearson_correlation:.3f}")
    print(f"  Spearman: {corr.spearman_correlation:.3f}")
    print(f"  Type: {corr.correlation_type}")
    print(f"  P-value: {corr.p_value:.4f}")

# Portfolio optimization
optimization_result = optimizer.optimize_portfolio(
    positions, analysis_results, historical_returns
)

print(f"Optimal Allocation:")
for position_id, weight in optimization_result.optimal_weights.items():
    print(f"  {position_id}: {weight:.1%}")

print(f"Expected Return: {optimization_result.expected_return:.1%}")
print(f"Expected Risk: {optimization_result.expected_risk:.1%}")
print(f"Sharpe Ratio: {optimization_result.sharpe_ratio:.2f}")
print(f"Diversification Ratio: {optimization_result.diversification_ratio:.2f}")

# Recommendations
print("Recommendations:")
for rec in optimization_result.recommendations:
    print(f"  • {rec}")
```

### Dynamic Position Sizing

```python
from app.tools.portfolio.dynamic_position_sizer import DynamicPositionSizer

# Initialize position sizer
sizer = DynamicPositionSizer(
    base_risk_per_trade=0.02,    # 2% base risk
    max_position_size=0.15,      # 15% max position
    kelly_fraction=0.25          # 25% of Kelly criterion
)

# Calculate portfolio sizing
sizing_result = sizer.calculate_portfolio_sizing(
    positions, analysis_results, total_capital=100000
)

print(f"Portfolio Sizing Results:")
print(f"Risk Budget Utilization: {sizing_result.risk_budget_utilization:.1%}")
print(f"Expected Portfolio Volatility: {sizing_result.expected_portfolio_volatility:.1%}")
print(f"Diversification Score: {sizing_result.diversification_score:.2f}")

# Individual recommendations
for rec in sizing_result.recommendations:
    print(f"\nPosition: {rec.position_id}")
    print(f"  Current Size: {rec.current_size:.1%}")
    print(f"  Recommended Size: {rec.recommended_size:.1%}")
    print(f"  Change: {rec.size_change_pct:+.1f}%")
    print(f"  Risk Level: {rec.risk_level}")
    print(f"  Confidence: {rec.confidence:.1%}")
    print(f"  Rationale: {rec.rationale}")
    print(f"  Statistical Basis: {rec.statistical_basis}")
```

## Performance Validation

### Exit Efficiency Tracking

```python
# Monitor exit efficiency performance
from tests.performance.test_exit_efficiency_targets import PerformanceValidator

validator = PerformanceValidator()

# Calculate current performance
current_metrics = {
    'exit_efficiency': 0.82,
    'sharpe_ratio': 1.95,
    'win_rate': 0.71,
    'avg_return': 0.125,
    'max_drawdown': 0.075,
    'diversification_ratio': 1.38,
    'baseline_sharpe': 1.45
}

# Validate against targets
validation_results = validator.validate_performance_targets(current_metrics)

print("Performance Validation Results:")

# Exit efficiency (57% → 85% target)
exit_eff = validation_results['exit_efficiency']
print(f"Exit Efficiency: {exit_eff['current']:.1%}")
print(f"  Target: {exit_eff['target']:.1%}")
print(f"  Progress: {exit_eff['improvement_pct']:.1%}")
print(f"  Meets Target: {exit_eff['meets_target']}")

# Portfolio health (68 → 85 target)
health = validation_results['portfolio_health']
print(f"Portfolio Health Score: {health['current']:.0f}")
print(f"  Target: {health['target']:.0f}")
print(f"  Progress: {health['improvement_pct']:.1%}")
print(f"  Meets Target: {health['meets_target']}")

# Sharpe ratio improvement (25% target)
sharpe = validation_results['sharpe_improvement']
print(f"Sharpe Ratio Improvement: {sharpe['improvement_pct']:.1%}")
print(f"  Target: {sharpe['target_improvement']:.1%}")
print(f"  Meets Target: {sharpe['meets_target']}")
```

### Real-Time Performance Monitoring

```python
# Real-time performance tracking
class PerformanceMonitor:
    def __init__(self, validator):
        self.validator = validator
        self.performance_history = []

    async def monitor_performance(self, positions, analysis_results):
        # Calculate current metrics
        exit_efficiencies = []
        for pos, analysis in zip(positions, analysis_results):
            if analysis.exit_signals:
                exit_efficiencies.append(analysis.exit_signals.exit_efficiency_score)

        current_exit_efficiency = np.mean(exit_efficiencies)

        # Track performance
        self.performance_history.append({
            'timestamp': datetime.utcnow(),
            'exit_efficiency': current_exit_efficiency,
            'positions_analyzed': len(positions)
        })

        # Alert if below target
        if current_exit_efficiency < 0.75:  # Below 75%
            print(f"⚠️  Performance Alert: Exit efficiency {current_exit_efficiency:.1%} below target")

        return current_exit_efficiency

# Usage
monitor = PerformanceMonitor(validator)
current_performance = await monitor.monitor_performance(positions, analysis_results)
```

## Advanced Usage

### Custom Exit Strategies

```python
# Custom exit strategy using statistical analysis
class StatisticalExitStrategy:
    def __init__(self, config):
        self.service = StatisticalAnalysisService(config=config)
        self.ml_engine = PatternRecognitionML()

    async def generate_exit_decision(self, position):
        # Statistical analysis
        analysis = await self.service.analyze_position_statistical_performance(
            position, include_exit_signals=True
        )

        # ML pattern recognition
        patterns = self.ml_engine.find_similar_patterns(position, analysis)

        # Anomaly detection
        anomaly = self.ml_engine.detect_anomalies(position, analysis)

        # Combined decision logic
        decision = {
            'action': 'HOLD',
            'confidence': 0.5,
            'reasons': []
        }

        # Statistical signals
        if analysis.exit_signals:
            if analysis.exit_signals.primary_signal == 'EXIT_IMMEDIATELY':
                decision['action'] = 'EXIT'
                decision['confidence'] = analysis.exit_signals.confidence
                decision['reasons'].append('Statistical exhaustion detected')

        # Pattern recognition
        if patterns:
            best_pattern = max(patterns, key=lambda p: p.similarity_score)
            if best_pattern.recommendation == 'CAPTURE_GAINS_IMMEDIATELY':
                decision['action'] = 'EXIT'
                decision['confidence'] = max(decision['confidence'], best_pattern.confidence)
                decision['reasons'].append(f'Pattern match: {best_pattern.pattern_type}')

        # Anomaly detection
        if anomaly.is_anomaly and anomaly.anomaly_type == 'statistical_outlier':
            decision['action'] = 'EXIT'
            decision['confidence'] = max(decision['confidence'], anomaly.confidence)
            decision['reasons'].append('Statistical outlier detected')

        return decision

# Usage
strategy = StatisticalExitStrategy(config)
decision = await strategy.generate_exit_decision(position)

print(f"Exit Decision: {decision['action']}")
print(f"Confidence: {decision['confidence']:.1%}")
print(f"Reasons: {', '.join(decision['reasons'])}")
```

### Batch Analysis

```python
# Batch analysis of multiple positions
async def analyze_portfolio_batch(service, positions):
    """Analyze multiple positions in batch."""

    results = []

    # Batch processing with memory optimization
    for i in range(0, len(positions), 10):  # Process 10 at a time
        batch = positions[i:i+10]
        batch_results = []

        for position in batch:
            result = await service.analyze_position_statistical_performance(
                position, include_exit_signals=True
            )
            batch_results.append(result)

        results.extend(batch_results)

        # Memory cleanup between batches
        if hasattr(service, 'clear_cache'):
            service.clear_cache()

    return results

# Usage
all_results = await analyze_portfolio_batch(service, all_positions)

# Aggregate analysis
exit_signals = [r for r in all_results if r.exit_signals and r.exit_signals.primary_signal == 'EXIT_IMMEDIATELY']
high_confidence = [r for r in all_results if r.confidence_metrics and r.confidence_metrics.overall_confidence > 0.8]

print(f"Immediate exits: {len(exit_signals)}")
print(f"High confidence analyses: {len(high_confidence)}")
```

### Integration with Existing Systems

```python
# Integration with existing portfolio management
class PortfolioIntegration:
    def __init__(self):
        self.statistical_service = StatisticalAnalysisService()
        self.ml_engine = PatternRecognitionML()
        self.optimizer = CrossStrategyOptimizer()
        self.sizer = DynamicPositionSizer()

    async def enhance_existing_portfolio(self, portfolio_data):
        """Enhance existing portfolio with statistical analysis."""

        enhanced_portfolio = []

        for position_data in portfolio_data:
            # Convert to PositionData format
            position = PositionData(
                position_id=position_data['id'],
                ticker=position_data['symbol'],
                strategy_name=position_data['strategy'],
                current_return=position_data['unrealized_pnl_pct'],
                mfe=position_data.get('max_favorable', 0),
                mae=position_data.get('max_adverse', 0),
                days_held=position_data['days_held'],
                entry_price=position_data['entry_price'],
                current_price=position_data['current_price']
            )

            # Statistical analysis
            analysis = await self.statistical_service.analyze_position_statistical_performance(
                position, include_exit_signals=True
            )

            # ML pattern recognition
            patterns = self.ml_engine.find_similar_patterns(position, analysis, top_k=1)

            # Enhanced position data
            enhanced_position = {
                **position_data,
                'statistical_percentile': analysis.divergence_analysis.dual_layer_convergence_score if analysis.divergence_analysis else 0,
                'exit_signal': analysis.exit_signals.primary_signal if analysis.exit_signals else 'HOLD',
                'confidence': analysis.exit_signals.confidence if analysis.exit_signals else 0.5,
                'pattern_match': patterns[0].pattern_type if patterns else 'unknown',
                'ml_recommendation': patterns[0].recommendation if patterns else 'HOLD'
            }

            enhanced_portfolio.append(enhanced_position)

        return enhanced_portfolio

# Usage
integration = PortfolioIntegration()
enhanced_portfolio = await integration.enhance_existing_portfolio(existing_portfolio_data)

# Export enhanced data
enhanced_df = pd.DataFrame(enhanced_portfolio)
enhanced_df.to_csv('enhanced_portfolio.csv', index=False)
```

## API Reference

### Core Classes

#### StatisticalAnalysisService

- `analyze_position_statistical_performance(position, include_exit_signals=True)`
- `analyze_portfolio_performance(positions)`
- `get_threshold_recommendations()`

#### PatternRecognitionML

- `fit(training_data)`
- `find_similar_patterns(position, analysis, top_k=3)`
- `detect_anomalies(position, analysis)`
- `calculate_pattern_confidence(pattern_matches)`

#### AdaptiveLearningEngine

- `optimize_thresholds(historical_trades, current_thresholds, target_metric)`
- `analyze_threshold_performance(trades, threshold_ranges)`
- `predict_performance_improvement(new_thresholds, confidence_level)`

#### CrossStrategyOptimizer

- `optimize_portfolio(positions, analysis_results, historical_returns)`
- `analyze_strategy_correlations(positions, historical_returns)`
- `calculate_diversification_benefit(positions, weights, historical_returns)`

#### DynamicPositionSizer

- `calculate_portfolio_sizing(positions, analysis_results, total_capital)`
- `calculate_position_size(position, analysis, total_capital)`

### Configuration Classes

#### StatisticalAnalysisConfig

- `USE_TRADE_HISTORY`: bool
- `PERCENTILE_THRESHOLD`: int
- `DUAL_LAYER_THRESHOLD`: float
- `RARITY_THRESHOLD`: float

#### ConfidenceLevel

- `high_confidence`: int
- `medium_confidence`: int
- `low_confidence`: int

### Data Models

#### PositionData

- `position_id`: str
- `ticker`: str
- `strategy_name`: str
- `current_return`: float
- `mfe`: float
- `mae`: float
- `days_held`: int

#### StatisticalAnalysisResult

- `divergence_analysis`: DivergenceResult
- `exit_signals`: ExitSignals
- `confidence_metrics`: ConfidenceMetrics
- `performance_metrics`: PerformanceMetrics

## Error Handling

```python
try:
    result = await service.analyze_position_statistical_performance(position)
except Exception as e:
    logger.error(f"Analysis failed for {position.position_id}: {e}")
    # Fallback to basic analysis
    result = create_fallback_analysis(position)
```

## Performance Optimization

```python
# Enable memory optimization
config.ENABLE_MEMORY_OPTIMIZATION = True

# Enable caching
config.ENABLE_CACHING = True
config.CACHE_TTL_SECONDS = 3600

# Batch processing for large portfolios
async def process_large_portfolio(positions, batch_size=20):
    results = []
    for i in range(0, len(positions), batch_size):
        batch = positions[i:i+batch_size]
        batch_results = await asyncio.gather(*[
            service.analyze_position_statistical_performance(pos)
            for pos in batch
        ])
        results.extend(batch_results)
    return results
```

## Troubleshooting

### Common Issues

1. **Insufficient Trade History**

   ```python
   if analysis.sample_size_analysis.sample_size < 15:
       print("Warning: Small sample size, results may be unreliable")
   ```

2. **Missing Return Distribution Data**

   ```python
   if not analysis.divergence_analysis:
       print("Warning: No asset return distribution data available")
   ```

3. **Low Statistical Confidence**
   ```python
   if analysis.confidence_metrics.overall_confidence < 0.7:
       print("Warning: Low statistical confidence in analysis")
   ```

### Performance Issues

1. **Memory Usage**: Enable memory optimization in config
2. **Slow Analysis**: Use batch processing for large portfolios
3. **Cache Misses**: Increase cache TTL or enable persistent caching

For additional support, see the [troubleshooting guide](./TROUBLESHOOTING.md) or check the [performance optimization guide](./PERFORMANCE_OPTIMIZATION.md).
