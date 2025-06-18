# Quantitative Trading System Enhancement Specification

## Executive Summary

This specification outlines a comprehensive enhancement plan for evolving the current dual SMA crossover trading system into a professional-grade quantitative trading platform. The enhancements focus on five core areas: signal quality optimization, dynamic position allocation, exit strategy evolution, regime detection, and portfolio correlation management.

## 1. System Overview

### 1.1 Current State

- **Primary Strategy**: Dual SMA crossover with hyperparameter optimization per asset
- **Position Holding Period**: Weeks to months (position trading)
- **Asset Universe**: Nasdaq 100 and S&P 500 constituents
- **Risk Management**: Fractional Kelly sizing with Sortino-optimized efficient frontier
- **Portfolio CVaR Target**: 11.8% at 95% confidence level
- **Execution**: Daily scanning with exact price fills

### 1.2 Enhancement Objectives

1. Reduce false signals and improve trade quality
2. Implement systematic daily position allocation
3. Optimize exit strategies beyond reverse crossover
4. Add market regime detection and adaptation
5. Quantify and manage portfolio correlations

## 2. Dual-Tier Scoring Architecture

### 2.1 Scoring System Overview

The enhanced trading system implements a sophisticated two-tier scoring architecture that separates historical strategy validation from real-time signal assessment:

#### 2.1.1 Strategy Performance Score (Tier 1: Historical)

**Purpose**: Identify and select historically profitable strategy parameters
**Data Source**: Backtesting results stored in `csv/strategies/next.csv`
**Calculation**: Implemented in `app/tools/stats_converter.py`

```python
# From stats_converter.py - Strategy Performance Score calculation
base_score = (
    win_rate_normalized * 2.5          # Historical win rate with confidence
    + total_trades_normalized * 1.5    # Statistical validity (trade count)
    + sortino_normalized * 1.2         # Risk-adjusted returns
    + profit_factor_normalized * 1.2   # Profit sustainability
    + expectancy_per_trade_normalized * 1.0  # Per-trade expectation
    + beats_bnh_normalized * 0.6       # Market outperformance
) / 8.0

# Apply confidence penalty for low trade counts
if total_trades < 50:
    confidence_multiplier = calculate_confidence_penalty(total_trades)
    final_score = base_score * confidence_multiplier
```

**Key Characteristics**:

- Range: 0.0 to 2.618 (golden ratio squared)
- Heavily penalizes strategies with <50 trades
- Emphasizes statistical confidence and risk-adjusted returns
- Examples from current system:
  - AMZN SMA(51,69): Score = 1.549 (61 trades, 61.67% win rate)
  - IRM SMA(70,84): Score = 1.324 (71 trades, 55.71% win rate)
  - VRSN SMA(12,31): Score = 1.200 (114 trades, 46.02% win rate)

#### 2.1.2 Signal Quality Score (Tier 2: Real-time)

**Purpose**: Filter and rank individual trading signals based on current market conditions
**Data Source**: Real-time technical indicators and market structure analysis
**Calculation**: New implementation for enhanced system

**Key Characteristics**:

- Range: 0 to 10 points
- Independent of historical performance
- Based on current market conditions
- Evaluates signal strength and market structure
- No dependency on trade count or historical metrics

#### 2.1.3 Integration Workflow

```
Phase 1: Strategy Selection (Historical)
├── Load backtested strategies from CSV files
├── Filter by Strategy Performance Score ≥ 1.0
├── Select top-performing parameter combinations per asset
└── Create watchlist of qualified strategies

Phase 2: Daily Signal Generation (Real-time)
├── Monitor qualified strategies for crossover signals
├── Calculate Signal Quality Score for each trigger
├── Filter signals with Quality Score ≥ 4.0
├── Rank remaining signals by quality
└── Pass to position allocation system

Phase 3: Position Allocation (Combined)
├── Calculate Conviction Score = f(Strategy Performance, Signal Quality)
├── Apply correlation and risk constraints
├── Allocate capital proportional to conviction
└── Execute highest-conviction signals within limits
```

This dual-tier architecture ensures that only historically proven strategies generate signals, while current market conditions determine which specific signals to act upon.

## 3. Signal Quality Enhancement Module

### 3.1 Signal Filtering System

#### 3.1.1 Core Filters

**ADX (Average Directional Index) Filter**

- **Purpose**: Eliminate entries during sideways/choppy markets
- **Implementation**:
  - Calculate ADX(14) for each asset
  - Only allow entries when ADX > threshold (default: 20)
  - Threshold customizable per asset class
- **Configuration**:
  ```json
  {
    "adx_filter": {
      "enabled": true,
      "period": 14,
      "threshold": {
        "default": 20,
        "crypto": 25,
        "stocks": 20,
        "etfs": 18
      }
    }
  }
  ```

**ATR Expansion Filter**

- **Purpose**: Capture volatility breakouts
- **Implementation**:
  - Entry only when ATR(14) > ATR_MA(50)
  - Optional: ATR expansion rate calculation
- **Configuration**:
  ```json
  {
    "atr_filter": {
      "enabled": true,
      "atr_period": 14,
      "ma_period": 50,
      "expansion_threshold": 1.0
    }
  }
  ```

**Slope Filter**

- **Purpose**: Confirm trend direction
- **Implementation**:
  - Calculate slope of slow SMA using linear regression
  - Only allow long entries when slope > 0
  - Optional: Minimum slope threshold
- **Configuration**:
  ```json
  {
    "slope_filter": {
      "enabled": true,
      "lookback": 10,
      "min_slope": 0.001
    }
  }
  ```

**Volume Confirmation**

- **Purpose**: Validate signal with increased activity
- **Implementation**:
  - Entry requires volume > multiplier × average volume
  - Use 20-day moving average as baseline
- **Configuration**:
  ```json
  {
    "volume_filter": {
      "enabled": true,
      "ma_period": 20,
      "multiplier": 1.5
    }
  }
  ```

#### 3.1.2 Optional Confirmation Indicators

**MACD Alignment**

- Only take long positions when MACD histogram is positive and rising
- Configurable fast/slow/signal periods

**RSI Momentum Filter**

- Long entries require RSI(14) > 50
- Optional overbought filter: Skip if RSI > 80

**Multi-Timeframe Alignment**

- Daily signal must align with weekly trend
- Both timeframes must show same SMA relationship

### 3.2 Signal Quality Scoring System

**Important Note**: This Signal Quality Score is distinct from the Strategy Performance Score used in portfolio selection. While Strategy Performance Score evaluates historical backtesting results (win rate, Sortino ratio, profit factor, etc.), Signal Quality Score assesses real-time market conditions for individual trade signals.

#### 3.2.1 Two-Tier Scoring Architecture

**Strategy Performance Score (Historical)**

- Used in strategy selection phase (e.g., `csv/strategies/next.csv`)
- Evaluates backtested performance over months/years
- Heavily weighted toward statistical confidence (trade count)
- Formula includes: win rate, Sortino ratio, profit factor, expectancy
- Range: typically 0.0 to 2.5+ (higher is better)
- Example: AMZN SMA(51,69) → Performance Score: 1.549

**Signal Quality Score (Real-time)**

- Used in daily trading decisions
- Evaluates current market conditions
- Based on technical indicators and market structure
- Independent of historical performance
- Range: 0 to 10 points (configurable)
- Example: AMZN crossover today → Signal Quality Score: 7/10

#### 3.2.2 Signal Quality Scoring Algorithm

```python
def calculate_signal_quality_score(signal_data):
    """
    Calculate real-time signal quality based on current market conditions.
    This is NOT the Strategy Performance Score from backtesting.
    """
    score = 0

    # Core filters (2 points each) - Strong signals
    if signal_data['adx'] > threshold:
        score += 2  # Strong trend present
    if signal_data['atr_expanding']:
        score += 2  # Volatility breakout
    if signal_data['volume_spike']:
        score += 2  # Demand confirmation

    # Secondary filters (1 point each) - Supporting signals
    if signal_data['slope_positive']:
        score += 1  # Trend direction confirmed
    if signal_data['macd_aligned']:
        score += 1  # Momentum confirmation
    if signal_data['rsi_bullish']:
        score += 1  # Not oversold
    if signal_data['higher_tf_aligned']:
        score += 1  # Multi-timeframe confluence

    # Penalty factors - Risk indicators
    if signal_data['extended_from_ma']:
        score -= 1  # Overextended price
    if signal_data['recent_whipsaw']:
        score -= 1  # Recent false signal

    return max(0, score)
```

#### 3.2.3 Integration with Strategy Performance

```python
def should_take_signal(ticker, signal_data, strategy_params):
    """
    Combine historical strategy performance with real-time signal quality.
    """
    # Get historical performance score for this strategy
    strategy_score = get_strategy_performance_score(ticker, strategy_params)

    # Calculate real-time signal quality
    signal_quality = calculate_signal_quality_score(signal_data)

    # Define thresholds
    MIN_STRATEGY_SCORE = 1.0  # Only trade strategies with proven performance
    MIN_SIGNAL_QUALITY = 4    # Only take high-quality signals

    # Both conditions must be met
    if strategy_score >= MIN_STRATEGY_SCORE and signal_quality >= MIN_SIGNAL_QUALITY:
        return True, {
            'strategy_performance_score': strategy_score,
            'signal_quality_score': signal_quality,
            'combined_confidence': (strategy_score * signal_quality) / 10
        }

    return False, {
        'reason': 'Low strategy score' if strategy_score < MIN_STRATEGY_SCORE else 'Poor signal quality',
        'strategy_performance_score': strategy_score,
        'signal_quality_score': signal_quality
    }
```

#### 3.2.4 Signal Ranking and Selection

- Calculate quality scores for all daily signals from qualified strategies
- Filter out signals from strategies with Performance Score < 1.0
- Rank remaining signals by Signal Quality Score (highest first)
- Apply minimum Signal Quality threshold (default: 4/10)
- Store both scores for performance attribution
- Track correlation between Signal Quality at entry and trade outcomes

## 4. Dynamic Position Allocation System

### 4.1 Daily Capital Deployment Budget

#### 4.1.1 Budget Calculation

```python
def calculate_daily_budget(portfolio_metrics):
    base_budget = portfolio_value * 0.05  # 5% default

    # Adjust for current drawdown
    if current_drawdown > 0.1:
        base_budget *= 0.5
    elif current_drawdown > 0.05:
        base_budget *= 0.75

    # Adjust for portfolio CVaR
    cvr_ratio = current_cvar / target_cvar
    if cvr_ratio > 0.9:
        base_budget *= (1 - cvr_ratio)

    # Market regime adjustment
    if market_regime == 'high_volatility':
        base_budget *= 0.7

    return base_budget
```

#### 4.1.2 Position Count Limits

- **Maximum positions per day**: Based on available budget and minimum position size
- **Sector limits**: No more than 2 new positions per sector per day
- **Correlation limits**: Maximum 1 position per correlation cluster

### 4.2 Conviction-Weighted Allocation

#### 4.2.1 Conviction Score Calculation

```python
def calculate_conviction_score(signal):
    """
    Calculate conviction score combining strategy performance, signal quality,
    and portfolio considerations.
    """
    # Component 1: Historical strategy performance (0-2.5 range)
    strategy_performance = signal['strategy_performance_score']

    # Component 2: Real-time signal quality (0-10 range, normalize to 0-2.5)
    signal_quality = signal['signal_quality_score'] * 0.25

    # Component 3: Correlation penalty (reduce conviction for correlated positions)
    avg_correlation = calculate_avg_correlation_to_portfolio(signal)
    correlation_penalty = avg_correlation * 2.0  # Penalty up to 2.0 points

    # Component 4: Expected return boost from backtesting
    expected_return = signal['backtest_metrics']['expected_return']
    return_boost = min(expected_return * 10, 2.0)  # Cap at 2.0 points

    # Component 5: Regime alignment bonus
    regime_alignment = calculate_regime_alignment_bonus(signal)

    # Calculate weighted conviction score
    conviction = (
        strategy_performance * 0.4 +     # 40% weight on proven performance
        signal_quality * 0.3 +           # 30% weight on current conditions
        return_boost * 0.2 +             # 20% weight on expected returns
        regime_alignment * 0.1           # 10% weight on regime fit
    ) - correlation_penalty             # Subtract correlation penalty

    return max(0, conviction)

def calculate_regime_alignment_bonus(signal):
    """Calculate bonus for signals aligned with current market regime."""
    current_regime = get_current_market_regime()
    strategy_type = signal['strategy_type']

    # Trend-following strategies perform better in trending regimes
    if strategy_type in ['SMA', 'EMA', 'MACD'] and current_regime['trend'] == 'strong_uptrend':
        return 1.0
    elif strategy_type in ['SMA', 'EMA'] and current_regime['volatility'] == 'low':
        return 0.5
    else:
        return 0.0
```

#### 4.2.2 Allocation Algorithm

1. Calculate conviction scores for all signals
2. Sort by conviction (highest first)
3. Allocate budget proportionally to conviction scores
4. Apply minimum and maximum position size constraints
5. Track unfilled allocations for next day consideration

### 4.3 CVaR-Based Position Limits

#### 4.3.1 Real-time CVaR Tracking

- Calculate portfolio CVaR after each potential position
- Reject positions that would exceed CVaR target
- Maintain 10% buffer below target for safety

#### 4.3.2 Dynamic Risk Budget

```python
def get_available_risk_budget():
    current_cvar = calculate_portfolio_cvar()
    target_cvar = 0.118  # 11.8%
    buffer = 0.01  # 1% buffer

    available = target_cvar - buffer - current_cvar
    return max(0, available)
```

## 5. Exit Strategy Evolution

### 5.1 Exit Method Framework

#### 5.1.1 Reverse Crossover Exit (Current)

- Exit when fast SMA crosses below slow SMA
- Simple but may give back significant profits

#### 5.1.2 ATR Trailing Stop

- **Initial Stop**: Entry price - (multiplier × ATR)
- **Trailing Logic**: Move stop up as price advances
- **Configuration**:
  ```json
  {
    "atr_trailing": {
      "enabled": true,
      "atr_period": 14,
      "multiplier": 3.0,
      "trail_trigger": 1.0 // ATRs of profit before trailing
    }
  }
  ```

#### 5.1.3 MFE (Maximum Favorable Excursion) Based Exit

- Track highest profit achieved per position
- Exit if price retraces X% from peak
- **Configuration**:
  ```json
  {
    "mfe_exit": {
      "enabled": true,
      "retrace_percent": 0.382, // Fibonacci level
      "min_profit_threshold": 0.02 // 2% minimum before activating
    }
  }
  ```

#### 5.1.4 Time-Based Exit

- Maximum holding period per position
- Force exit after N bars regardless of profit/loss
- **Configuration**:
  ```json
  {
    "time_exit": {
      "enabled": true,
      "max_bars": 100,
      "extension_on_profit": true, // Extend if in profit
      "extension_bars": 50
    }
  }
  ```

### 5.2 Adaptive Exit Selection

#### 5.2.1 Exit Method Testing Framework

```python
def test_exit_methods(ticker, strategy_params):
    results = {}

    for exit_method in ['crossover', 'atr_trail', 'mfe', 'time']:
        backtest = run_backtest(
            ticker=ticker,
            entry_strategy='sma_cross',
            entry_params=strategy_params,
            exit_strategy=exit_method,
            exit_params=get_exit_params(exit_method)
        )

        results[exit_method] = {
            'sharpe': backtest.sharpe_ratio,
            'win_rate': backtest.win_rate,
            'avg_win_loss_ratio': backtest.avg_win / backtest.avg_loss,
            'max_drawdown': backtest.max_drawdown,
            'avg_holding_days': backtest.avg_holding_period
        }

    return results
```

#### 5.2.2 Exit Method Selection

- Test all exit methods per asset over historical data
- Select best method based on weighted scoring:
  - Sharpe Ratio (40%)
  - Win/Loss Ratio (30%)
  - Maximum Drawdown (20%)
  - Average Holding Period (10%)
- Re-optimize quarterly or after significant regime changes

## 6. Market Regime Detection System

### 6.1 Regime Classification Framework

#### 6.1.1 Volatility Regime

**VIX-Based Classification**

- Low Volatility: VIX < 15
- Normal Volatility: 15 ≤ VIX < 25
- High Volatility: VIX ≥ 25
- Extreme Volatility: VIX ≥ 35

**Asset-Specific ATR Regime**

- Calculate rolling percentile rank of ATR
- Low: < 25th percentile
- Normal: 25th - 75th percentile
- High: > 75th percentile

#### 6.1.2 Trend Regime

**Market Breadth Indicators**

- Calculate % of stocks above 200-day SMA
- Strong Uptrend: > 70%
- Uptrend: 50% - 70%
- Neutral: 30% - 50%
- Downtrend: 10% - 30%
- Strong Downtrend: < 10%

**Trend Strength (ADX-Based)**

- Strong Trend: ADX > 25
- Moderate Trend: 20 < ADX ≤ 25
- Weak/No Trend: ADX ≤ 20

#### 6.1.3 Macro Regime

**Yield Curve Analysis**

- Normal: 10Y-2Y > 100 bps
- Flattening: 0 < 10Y-2Y ≤ 100 bps
- Inverted: 10Y-2Y < 0

**Dollar Strength**

- DXY momentum and trend analysis
- Risk-on vs Risk-off classification

### 6.2 Regime Adaptation Rules

#### 6.2.1 Position Sizing Adjustments

```python
def adjust_position_size_for_regime(base_size, regime):
    multipliers = {
        'low_volatility_uptrend': 1.2,
        'normal_volatility_uptrend': 1.0,
        'high_volatility_uptrend': 0.7,
        'low_volatility_downtrend': 0.5,
        'normal_volatility_downtrend': 0.3,
        'high_volatility_downtrend': 0.0  # No new positions
    }

    regime_key = f"{regime['volatility']}_{regime['trend']}"
    return base_size * multipliers.get(regime_key, 0.5)
```

#### 6.2.2 Strategy Parameter Adjustments

- **Tight Markets**: Use shorter SMA periods
- **Trending Markets**: Use longer SMA periods
- **Volatile Markets**: Widen stops, reduce position sizes
- **Quiet Markets**: Tighten stops, increase position sizes

### 6.3 Regime Transition Detection

#### 6.3.1 Early Warning Indicators

- Monitor regime indicator momentum
- Track regime stability (days in current regime)
- Calculate regime transition probability

#### 6.3.2 Transition Actions

- Gradual position reduction when regime deteriorating
- Halt new positions during regime transitions
- Accelerated exits for positions against new regime

## 7. Portfolio Correlation Management

### 7.1 Correlation Analysis Framework

#### 7.1.1 Rolling Correlation Matrix

```python
def calculate_correlation_matrix(portfolio_assets, lookback_days=60):
    # Use Spearman correlation for robustness
    correlations = {}

    for asset1 in portfolio_assets:
        correlations[asset1] = {}
        for asset2 in portfolio_assets:
            if asset1 != asset2:
                corr = calculate_spearman_correlation(
                    asset1_returns[-lookback_days:],
                    asset2_returns[-lookback_days:]
                )
                correlations[asset1][asset2] = corr

    return correlations
```

#### 7.1.2 Correlation Clustering

**Hierarchical Clustering Algorithm**

1. Calculate pairwise correlations
2. Apply hierarchical clustering with correlation distance
3. Cut dendrogram at threshold (e.g., 0.7 correlation)
4. Assign assets to clusters

**Dynamic Cluster Updates**

- Recalculate clusters daily
- Track cluster stability over time
- Alert on significant cluster changes

### 7.2 Correlation-Based Position Limits

#### 7.2.1 Cluster Exposure Limits

```python
def check_cluster_limits(new_position, current_portfolio):
    cluster_id = get_cluster_id(new_position)
    cluster_exposure = calculate_cluster_exposure(cluster_id, current_portfolio)

    limits = {
        'max_positions_per_cluster': 3,
        'max_weight_per_cluster': 0.25,
        'max_correlation_to_existing': 0.8
    }

    if cluster_exposure['position_count'] >= limits['max_positions_per_cluster']:
        return False, "Cluster position limit exceeded"

    if cluster_exposure['total_weight'] >= limits['max_weight_per_cluster']:
        return False, "Cluster weight limit exceeded"

    max_correlation = calculate_max_correlation(new_position, current_portfolio)
    if max_correlation > limits['max_correlation_to_existing']:
        return False, f"Correlation too high: {max_correlation}"

    return True, "Position approved"
```

#### 7.2.2 Sector and Factor Limits

**Sector Exposure Caps**

- Technology: 25% maximum
- Financials: 20% maximum
- Energy: 15% maximum
- Others: 20% maximum each

**Factor Exposure Monitoring**

- Momentum factor loading
- Value factor loading
- Size factor loading
- Quality factor loading

### 7.3 Diversification Scoring

#### 7.3.1 Portfolio Diversification Metrics

```python
def calculate_diversification_score(portfolio):
    metrics = {
        'effective_n': calculate_effective_n(portfolio),
        'concentration_ratio': calculate_herfindahl_index(portfolio),
        'correlation_penalty': calculate_avg_pairwise_correlation(portfolio),
        'sector_balance': calculate_sector_entropy(portfolio)
    }

    # Weighted score
    score = (
        metrics['effective_n'] * 0.3 +
        (1 - metrics['concentration_ratio']) * 0.3 +
        (1 - metrics['correlation_penalty']) * 0.2 +
        metrics['sector_balance'] * 0.2
    )

    return score, metrics
```

#### 7.3.2 Diversification Targets

- Minimum diversification score: 0.7
- Minimum effective N: 10
- Maximum single position: 10%
- Maximum correlation cluster: 25%

## 8. Execution and Monitoring

### 8.1 Order Execution Framework

#### 8.1.1 Smart Order Routing

```python
def execute_order(signal, allocation):
    order = {
        'symbol': signal['symbol'],
        'side': signal['side'],
        'quantity': calculate_shares(allocation, signal['entry_price']),
        'order_type': 'limit',
        'limit_price': signal['entry_price'],
        'time_in_force': 'day',
        'iceberg_quantity': calculate_iceberg_size(allocation)
    }

    # Pre-execution checks
    if not validate_order(order):
        return log_rejected_order(order)

    # Execute with retry logic
    result = execute_with_retry(order, max_retries=3)

    # Post-execution logging
    log_execution(order, result)

    return result
```

#### 8.1.2 Execution Quality Metrics

- Fill rate tracking
- Slippage analysis
- Rejected order analysis
- Opportunity cost calculation

### 8.2 Performance Monitoring

#### 8.2.1 Real-time Metrics Dashboard

**Portfolio Level Metrics**

- Current CVaR vs Target
- Sharpe Ratio (rolling)
- Correlation matrix heatmap
- Regime indicators
- Sector exposures

**Position Level Metrics**

- Unrealized P&L
- Days held
- Strategy Performance Score (historical)
- Signal Quality Score at entry (real-time)
- Conviction Score at entry (combined)
- Exit method selected
- Correlation to portfolio at entry

#### 8.2.2 Attribution Analysis

```python
def perform_attribution_analysis(portfolio_history):
    """
    Analyze performance attribution across multiple dimensions including
    both historical strategy performance and real-time signal quality.
    """
    attribution = {
        # Strategy selection attribution
        'strategy_performance': analyze_by_strategy_score(),

        # Signal timing attribution
        'signal_quality': analyze_by_signal_quality_score(),

        # Combined conviction attribution
        'conviction_score': analyze_by_conviction_score(),

        # Market condition attribution
        'regime': analyze_by_regime(),

        # Execution attribution
        'exit_method': analyze_by_exit_type(),

        # Portfolio construction attribution
        'sector': analyze_by_sector(),
        'correlation_cluster': analyze_by_cluster(),

        # Cross-correlation analysis
        'score_correlation': analyze_score_relationships()
    }

    return attribution

def analyze_score_relationships():
    """
    Analyze relationships between different scoring components and outcomes.
    """
    return {
        'strategy_vs_signal_correlation': calculate_correlation(
            'strategy_performance_score', 'signal_quality_score'
        ),
        'conviction_vs_outcome': calculate_correlation(
            'conviction_score', 'trade_return'
        ),
        'signal_quality_predictive_power': calculate_predictive_accuracy(
            'signal_quality_score', 'trade_success'
        ),
        'optimal_score_thresholds': calculate_optimal_thresholds()
    }
```

### 8.3 Risk Monitoring and Alerts

#### 8.3.1 Risk Thresholds

- CVaR approaching limit (> 90% of target)
- Correlation cluster concentration
- Regime transition detected
- Unusual drawdown pattern
- Position limit breaches

#### 8.3.2 Alert System

```python
def check_risk_alerts(portfolio):
    alerts = []

    # CVaR Alert
    if portfolio.cvar > (target_cvar * 0.9):
        alerts.append({
            'type': 'cvar_warning',
            'severity': 'high',
            'message': f'CVaR at {portfolio.cvar:.1%} approaching limit'
        })

    # Correlation Alert
    if portfolio.max_cluster_weight > 0.3:
        alerts.append({
            'type': 'correlation_concentration',
            'severity': 'medium',
            'message': f'Cluster concentration at {portfolio.max_cluster_weight:.1%}'
        })

    # Regime Alert
    if regime_transition_probability() > 0.7:
        alerts.append({
            'type': 'regime_transition',
            'severity': 'high',
            'message': 'Regime transition likely'
        })

    return alerts
```

## 9. Implementation Roadmap

### 9.1 Phase 1: Foundation (Weeks 1-4)

**Week 1-2: Signal Quality Enhancement**

- Implement ADX, ATR, and volume filters
- Build signal scoring system
- Update strategy configuration schema
- Create filter backtesting framework

**Week 3-4: Dynamic Allocation System**

- Implement daily budget calculation
- Build conviction scoring algorithm
- Create position limit enforcement
- Develop allocation tracking system

### 9.2 Phase 2: Advanced Features (Weeks 5-8)

**Week 5-6: Exit Strategy Evolution**

- Implement ATR trailing stop
- Build MFE-based exit logic
- Create time-based exit rules
- Develop exit method comparison framework

**Week 7-8: Regime Detection**

- Build volatility regime classifier
- Implement trend regime indicators
- Create regime adaptation rules
- Develop regime transition alerts

### 9.3 Phase 3: Portfolio Intelligence (Weeks 9-12)

**Week 9-10: Correlation Management**

- Implement correlation clustering
- Build cluster-based position limits
- Create diversification scoring
- Develop correlation monitoring dashboard

**Week 11-12: Integration and Testing**

- Full system integration testing
- Performance optimization
- User interface development
- Documentation and training

### 9.4 Phase 4: Production Deployment (Weeks 13-16)

**Week 13-14: Pilot Testing**

- Paper trading validation
- Performance benchmarking
- Bug fixes and optimization
- User feedback incorporation

**Week 15-16: Full Deployment**

- Production environment setup
- Monitoring system activation
- Alert system configuration
- Go-live and support

## 10. Success Metrics

### 10.1 Performance Targets

- **Sharpe Ratio Improvement**: +0.3 vs baseline
- **Maximum Drawdown Reduction**: -20% vs baseline
- **Win Rate Improvement**: +10% vs baseline
- **False Signal Reduction**: -40% vs baseline

### 10.2 Risk Targets

- **CVaR Compliance**: 100% within target
- **Correlation Limit Compliance**: 100%
- **Sector Limit Compliance**: 100%
- **Execution Quality**: 95%+ fill rate

### 10.3 Operational Targets

- **Signal Processing Time**: < 1 second per asset
- **Portfolio Calculation Time**: < 5 seconds
- **Alert Latency**: < 10 seconds
- **System Uptime**: 99.9%

## 11. Technical Requirements

### 11.1 Data Requirements

- **Market Data**: Real-time and historical prices
- **Volume Data**: Daily volume with intraday for signals
- **Fundamental Data**: Sector classifications
- **Macro Data**: VIX, yield curves, DXY

### 11.2 Infrastructure Requirements

- **Compute**: Multi-core processing for parallel backtesting
- **Memory**: Sufficient for correlation matrix calculations
- **Storage**: Historical data and backtest results
- **Network**: Low-latency connections for execution

### 11.3 Integration Requirements

- **Existing Systems**: Maintain compatibility with current architecture
- **API Design**: RESTful APIs for all new modules
- **Database**: Optimized schema for new data types
- **Monitoring**: Prometheus/Grafana compatible metrics

## 12. Risk Mitigation

### 12.1 Technical Risks

- **Overfitting**: Extensive out-of-sample testing
- **Latency**: Performance optimization and caching
- **Data Quality**: Multiple data source validation
- **System Failure**: Redundancy and failover systems

### 12.2 Market Risks

- **Regime Changes**: Adaptive parameter adjustment
- **Correlation Breakdown**: Dynamic limit adjustment
- **Liquidity**: Position size limits based on volume
- **Black Swan Events**: Circuit breakers and kill switches

### 12.3 Operational Risks

- **Key Person**: Comprehensive documentation
- **Process Failure**: Automated monitoring and alerts
- **Compliance**: Audit trails and reporting
- **Cybersecurity**: Encryption and access controls

## 13. Conclusion

This specification outlines a comprehensive enhancement plan that transforms the current trading system into a sophisticated quantitative platform. The modular design allows for incremental implementation while maintaining system stability. Each enhancement is designed to be measurable, testable, and reversible if needed.

The focus on signal quality, dynamic allocation, intelligent exits, regime awareness, and correlation management addresses the key limitations of simple moving average strategies while building on the solid foundation already in place.

Success will be measured not just by improved returns, but by more consistent performance, better risk management, and increased system reliability. The phased implementation approach ensures that each component is thoroughly tested before integration, minimizing disruption to existing operations.
