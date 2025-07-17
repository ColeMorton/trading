# SPDS Critical Path Documentation

## Overview

This documentation covers the 3 primary analysis workflows in the Statistical Performance Divergence System (SPDS). Understanding these workflows is essential for developer onboarding and system maintenance.

## Primary Analysis Workflows

### 1. Portfolio Analysis Workflow

**Purpose**: Analyze entire portfolio files for exit signals and performance metrics.

**Entry Points**:
- CLI: `python -m app.cli spds analyze risk_on.csv`
- Direct: `PortfolioStatisticalAnalyzer("risk_on.csv")`

**Data Flow**:
```
Portfolio File (CSV) → Position Parsing → Strategy Matching → Analysis → Results
```

**Key Components**:
1. **`app/cli/commands/spds.py`**: CLI entry point and parameter processing
2. **`app/tools/portfolio_analyzer.py`**: Main portfolio analyzer
3. **`app/tools/services/statistical_analysis_service.py`**: Core analysis orchestration
4. **`app/tools/analysis/divergence_detector.py`**: Statistical divergence detection
5. **`app/tools/analysis/trade_history_analyzer.py`**: Trade-level analysis

**Detailed Process**:

#### Step 1: Portfolio Loading and Validation
```python
# File: app/tools/portfolio_analyzer.py
class PortfolioStatisticalAnalyzer:
    def __init__(self, portfolio: str, use_trade_history: bool = True):
        self.portfolio = portfolio
        self.use_trade_history = use_trade_history
        self.config = StatisticalAnalysisConfig.create(portfolio, use_trade_history)
```

#### Step 2: Position UUID Parsing
```python
# File: app/tools/uuid_utils.py
def parse_strategy_uuid(uuid: str) -> Dict[str, Any]:
    # Parse Position_UUID format: TICKER_STRATEGY_SHORT_LONG_DATE
    # Example: AAPL_SMA_20_50_20250101
```

#### Step 3: Data Source Selection
```python
# File: app/tools/services/statistical_analysis_service.py
class StatisticalAnalysisService:
    async def analyze_portfolio(self, portfolio: str) -> Dict[str, StatisticalAnalysisResult]:
        # 1. Load portfolio positions
        # 2. Determine data source (trade history vs equity curves)
        # 3. Route to appropriate analyzer
```

#### Step 4: Statistical Analysis
```python
# File: app/tools/analysis/divergence_detector.py
class DivergenceDetector:
    async def detect_asset_divergence(self, analysis, position_data):
        # 1. Calculate z-scores and percentiles
        # 2. Identify statistical outliers
        # 3. Generate component scores
        # 4. Determine exit signals
```

#### Step 5: Result Aggregation and Export
```python
# File: app/tools/services/backtesting_parameter_export_service.py
class BacktestingParameterExportService:
    async def export_backtesting_parameters(self, results, portfolio):
        # 1. Format results for export
        # 2. Generate JSON, CSV, and Markdown outputs
        # 3. Save to exports directory
```

**Input Requirements**:
- Portfolio CSV file in `csv/positions/` directory
- Columns: `Position_UUID`, `Ticker`, `Strategy`, `Win_Rate`, `Total_Return`, etc.
- Optional: Trade history JSON files in `json/trade_history/`

**Output Artifacts**:
- `exports/statistical_analysis/{portfolio}_analysis.json`
- `exports/statistical_analysis/{portfolio}_analysis.csv`
- `exports/statistical_analysis/{portfolio}_analysis.md`
- `exports/backtesting_parameters/{portfolio}_parameters.json`

**Performance Characteristics**:
- **1K positions**: ~2-5 seconds
- **10K positions**: ~10-30 seconds
- **100K positions**: ~60-300 seconds (depends on memory optimization)

---

### 2. Strategy Analysis Workflow

**Purpose**: Analyze specific trading strategies for performance and exit signals.

**Entry Points**:
- CLI: `python -m app.cli spds analyze TSLA_SMA_15_25`
- Direct: `StrategyAnalyzer("TSLA_SMA_15_25")`

**Data Flow**:
```
Strategy Spec → Parameter Parsing → Data Retrieval → Analysis → Results
```

**Key Components**:
1. **`app/tools/parameter_parser.py`**: Strategy specification parsing
2. **`app/tools/specialized_analyzers.py`**: Strategy-specific analyzers
3. **`app/tools/analysis/trade_history_analyzer.py`**: Trade data analysis
4. **`app/contexts/analytics/services/statistical_analyzer.py`**: Statistical computations

**Detailed Process**:

#### Step 1: Strategy Specification Parsing
```python
# File: app/tools/parameter_parser.py
def parse_spds_parameter(parameter: str) -> ParsedParameter:
    # Parse format: TICKER_STRATEGY_SHORT_LONG
    # Example: TSLA_SMA_15_25
    # Returns: ParsedParameter with ticker, strategy_type, windows
```

#### Step 2: Data Source Discovery
```python
# File: app/tools/specialized_analyzers.py
class StrategyAnalyzer:
    def __init__(self, strategy_spec: str):
        self.ticker = parsed.ticker
        self.strategy_type = parsed.strategy_type
        self.short_window = parsed.short_window
        self.long_window = parsed.long_window
        
        # Look for trade history file
        self.trade_history_file = f"{ticker}_D_{strategy_type}_{short_window}_{long_window}.json"
```

#### Step 3: Historical Data Analysis
```python
# File: app/tools/analysis/trade_history_analyzer.py
class TradeHistoryAnalyzer:
    async def analyze_strategy_performance(self, strategy_spec):
        # 1. Load trade history JSON
        # 2. Calculate performance metrics
        # 3. Analyze equity curve characteristics
        # 4. Generate statistical insights
```

#### Step 4: Divergence Detection
```python
# Same as Portfolio Analysis - uses DivergenceDetector
# But focuses on single strategy instead of portfolio
```

**Input Requirements**:
- Strategy specification string (e.g., "TSLA_SMA_15_25")
- Optional: Trade history JSON file in `json/trade_history/`
- Optional: Equity curve data in configured equity paths

**Output Artifacts**:
- Single strategy analysis result
- Component scores (risk, momentum, trend, etc.)
- Exit signal recommendation
- Statistical confidence metrics

**Performance Characteristics**:
- **Single strategy**: ~0.1-0.5 seconds
- **Multi-strategy batch**: ~1-10 seconds (parallel processing)

---

### 3. Position Analysis Workflow

**Purpose**: Analyze individual position UUIDs for real-time trading decisions.

**Entry Points**:
- CLI: `python -m app.cli spds analyze TSLA_SMA_15_25_20250710`
- Direct: `PositionAnalyzer("TSLA_SMA_15_25_20250710")`

**Data Flow**:
```
Position UUID → UUID Parsing → Position Lookup → Analysis → Exit Signal
```

**Key Components**:
1. **`app/tools/parameter_parser.py`**: Position UUID parsing
2. **`app/tools/analysis/real_time_position_analyzer.py`**: Real-time position analysis
3. **`app/tools/analysis/trade_history_analyzer.py`**: Historical context analysis
4. **`app/tools/services/statistical_analysis_service.py`**: Statistical processing

**Detailed Process**:

#### Step 1: Position UUID Parsing
```python
# File: app/tools/parameter_parser.py
def parse_position_uuid(uuid: str) -> ParsedPosition:
    # Parse format: TICKER_STRATEGY_SHORT_LONG_DATE
    # Example: TSLA_SMA_15_25_20250710
    # Returns: ParsedPosition with all components + entry_date
```

#### Step 2: Position Context Retrieval
```python
# File: app/tools/analysis/real_time_position_analyzer.py
class RealTimePositionAnalyzer:
    async def analyze_position(self, position_uuid: str):
        # 1. Parse position UUID
        # 2. Find position in portfolio files
        # 3. Retrieve current market data
        # 4. Load historical performance context
```

#### Step 3: Real-Time Analysis
```python
# Combines multiple analysis layers:
# 1. Current position P&L and metrics
# 2. Strategy historical performance
# 3. Market condition assessment
# 4. Risk-adjusted exit recommendations
```

#### Step 4: Exit Signal Generation
```python
# File: app/tools/analysis/divergence_detector.py
# Generates position-specific exit signals based on:
# - Current unrealized P&L
# - Strategy performance history
# - Market volatility regime
# - Risk management parameters
```

**Input Requirements**:
- Position UUID string (e.g., "TSLA_SMA_15_25_20250710")
- Position data in portfolio CSV files
- Current market price (real-time or recent)
- Optional: Trade history for strategy context

**Output Artifacts**:
- Position-specific exit signal
- Current P&L status
- Risk assessment
- Statistical confidence level
- Recommended action (HOLD, EXIT_SOON, EXIT_IMMEDIATELY)

**Performance Characteristics**:
- **Single position**: ~0.05-0.2 seconds
- **Multi-position batch**: ~0.5-5 seconds
- **Real-time processing**: <100ms (with caching)

---

## Common Components Across Workflows

### Configuration Management
**File**: `app/tools/config/statistical_analysis_config.py`

```python
class StatisticalAnalysisConfig:
    # Core configuration for all workflows
    PERCENTILE_THRESHOLDS = {"exit_immediately": 95.0, "exit_soon": 85.0}
    CONVERGENCE_THRESHOLD = 0.85
    MIN_SAMPLE_SIZE = 15
    BOOTSTRAP_ITERATIONS = 1000
    CONFIDENCE_LEVEL = "medium"
```

### Data Models
**File**: `app/tools/models/statistical_analysis_models.py`

```python
@dataclass
class StatisticalAnalysisResult:
    # Common result structure for all workflows
    strategy_name: str
    ticker: str
    exit_signal: ProbabilisticExitSignal
    confidence_level: float
    divergence_metrics: DivergenceMetrics
    component_scores: Dict[str, float]
```

### Export System
**File**: `app/tools/services/divergence_export_service.py`

```python
class DivergenceExportService:
    # Unified export system for all workflows
    async def export_json(self, results: List[StatisticalAnalysisResult], filename: str)
    async def export_csv(self, results: List[StatisticalAnalysisResult], filename: str)
    async def export_markdown(self, results: List[StatisticalAnalysisResult], filename: str)
```

## Developer Onboarding Guide

### Prerequisites
- Python 3.8+
- Understanding of statistical concepts (z-scores, percentiles)
- Basic knowledge of trading strategies (SMA, EMA, MACD)
- Familiarity with async/await patterns

### Quick Start (30 minutes)
1. **Read this documentation** (10 minutes)
2. **Run Portfolio Analysis example** (10 minutes):
   ```bash
   python -m app.cli spds analyze risk_on.csv --verbose
   ```
3. **Examine output files** (10 minutes):
   - Check `exports/statistical_analysis/`
   - Review JSON and CSV results
   - Understand component scores

### Deep Dive (2 hours)
1. **Study core files** (60 minutes):
   - `app/tools/portfolio_analyzer.py` - Main interface
   - `app/tools/services/statistical_analysis_service.py` - Core logic
   - `app/tools/analysis/divergence_detector.py` - Statistical analysis
   
2. **Trace workflow execution** (30 minutes):
   - Add debug prints to key methods
   - Run analysis with verbose logging
   - Follow data flow from input to output

3. **Understand configuration** (30 minutes):
   - Examine `statistical_analysis_config.py`
   - Modify thresholds and observe impact
   - Test different confidence levels

### Advanced Topics (1 day)
1. **Memory optimization components** (app/tools/processing/)
2. **Service architecture patterns** (app/tools/services/)
3. **Export system internals** (app/tools/services/*_export_service.py)
4. **Statistical model validation** (app/tools/analysis/bootstrap_validator.py)

## Common Issues and Solutions

### Issue 1: "Portfolio file not found"
**Solution**: Ensure portfolio CSV is in `csv/positions/` directory

### Issue 2: "No trade history available"
**Solution**: System falls back to equity curve analysis automatically

### Issue 3: "Analysis takes too long"
**Solution**: 
- Check portfolio size (>10K positions = slow)
- Enable memory optimization
- Use smaller test portfolios

### Issue 4: "Export files not generated"
**Solution**: Check permissions on `exports/` directory

### Issue 5: "Statistical analysis fails"
**Solution**: 
- Verify minimum sample size requirements
- Check for valid strategy parameters
- Ensure position data quality

## Future Improvements

Based on the Senior Code Owner Review, these workflows will be simplified through:

1. **Service Layer Consolidation**: Reduce 5-layer to 3-layer architecture
2. **Statistical Library Integration**: Replace custom implementations with scipy/numpy
3. **Memory Optimization Evaluation**: Assess if complexity is justified
4. **Configuration Simplification**: Reduce configuration complexity
5. **Export System Unification**: Single export service instead of multiple

---

**Documentation Version**: 1.0
**Last Updated**: 2025-01-15
**Target Audience**: SPDS developers and maintainers
**Review Cycle**: Monthly updates recommended