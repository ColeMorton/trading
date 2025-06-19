# Architecture Plan: Position Sizing System Migration

## Executive Summary

<summary>
  <objective>Migrate Excel-based position sizing system to integrated code-based solution with enhanced capabilities</objective>
  <approach>4-phase incremental migration leveraging existing modular service architecture and extending risk management framework</approach>
  <value>Automated real-time position sizing, improved risk management, elimination of manual Excel processes, 40% reduction in operational overhead</value>
</summary>

## Current State Analysis

### Existing Architecture Strengths

- **Modular Service Architecture**: ServiceCoordinator, PortfolioProcessingService, StrategyExecutionEngine
- **Comprehensive Data Processing**: Polars-based high-performance pipeline
- **Portfolio Management Framework**: Schema evolution, allocation management, 60-column extended schema
- **Performance Optimization Suite**: Caching, parallel processing, memory optimization
- **API Infrastructure**: FastAPI with dedicated routers, async operations

### Gap Analysis

**Already Implemented (40% Coverage):**

- Portfolio data loading and schema management
- Basic allocation percentage calculations
- Trade history tracking and statistics
- Performance metrics (20+ indicators)
- Data processing infrastructure

**Requires Development (60% Gap):**

- CVaR calculations for risk management
- Kelly Criterion position sizing
- Multi-account portfolio coordination
- Risk allocation bucket system
- Dual portfolio management (Trading vs Investment)

## Web Frontend Location and Technology Stack

### Current Frontend Location

The web frontend is located at **`/app/frontend/sensylate/`** with the following technology stack:

**Frontend Framework:**

- **React 18.2.0** with TypeScript
- **Vite 6.2.6** for build/dev server
- **Bootstrap 5.3.2** for styling
- **Apollo Client 3.13.8** for GraphQL
- **PWA capabilities** with offline support

**Current Navigation:**

- CSV Viewer
- Parameter Testing
- **NEW**: Position Sizing Dashboard (to be added)

## Target Architecture

```xml
<architecture>
  <core_services>
    <service name="PositionSizingOrchestrator" location="app/api/services/">
      Coordinates all position sizing operations
    </service>
    <service name="RiskCalculationEngine" location="app/tools/risk/">
      CVaR, Kelly Criterion, confidence metrics
    </service>
    <service name="AccountCoordinationService" location="app/tools/accounts/">
      Multi-broker account management
    </service>
    <service name="AllocationOptimizer" location="app/tools/allocation/">
      Risk bucket allocation and optimization
    </service>
  </core_services>

  <integration_points>
    <point>Existing ServiceCoordinator → Enhanced with position sizing</point>
    <point>Portfolio schema → Extended with account-specific fields</point>
    <point>API routers → New position sizing endpoints</point>
    <point>Database schema → Risk metrics and allocation tables</point>
    <point>React frontend → New Position Sizing Dashboard page</point>
  </integration_points>
</architecture>
```

## Implementation Phases

### Phase 1: Core Risk Calculation Components (8 days)

<phase number="1" estimated_effort="8 days">
  <objective>Implement core risk calculation components with automated data sourcing</objective>
  <scope>
    Included: Risk calculation engine, Kelly criterion implementation, confidence metrics, automated data fetching
    Excluded: Multi-account coordination, API endpoints, UI components
  </scope>
  <dependencies>
    - @json/concurrency/ portfolio analysis files (portfolio.json, trades.json)
    - @csv/strategies/ backtest results matching concurrency analysis names
    - @app/portfolio_review/efficient_frontier.py for allocation optimization
    - @app/tools/get_data.py and @app/tools/download_data.py for price data
    - Manual trading journal for Kelly parameters
  </dependencies>

  <implementation>
    <step>Create RiskCalculationEngine sourcing CVaR from @json/concurrency/ files with @csv/strategies/ backtest data integration</step>
    <step>Integrate efficient_frontier.py for automated Max Allocation % calculations</step>
    <step>Integrate existing @app/tools/get_data.py and @app/tools/download_data.py for consistent price fetching</step>
    <step>Implement Kelly Criterion calculator using manual trading journal inputs</step>
    <step>Implement 11.8% risk allocation system (currently only this tier is used)</step>
    <validation>Unit tests comparing outputs to Excel formulas, integration tests with portfolio data</validation>
    <rollback>New components are additive; existing functionality remains unchanged</rollback>
  </implementation>

  <deliverables>
    <deliverable>RiskCalculationEngine with CVaR calculations sourcing from @json/concurrency/ files (Investment: portfolio.json, Risk On: trades.json) and corresponding @csv/strategies/ backtest results matching Excel B12/E11 formulas</deliverable>
    <deliverable>KellyCriterionSizer using manual trading journal inputs (No. Primary, No. Outliers, Kelly Criterion) matching Excel B17-B21</deliverable>
    <deliverable>EfficientFrontierIntegration for automated Max Allocation % calculations</deliverable>
    <deliverable>PriceDataIntegration using existing @app/tools/get_data.py for automated price data (Incoming/Investment Price $)</deliverable>
    <deliverable>RiskAllocationCalculator implementing 11.8% risk allocation (Excel B5 formula)</deliverable>
</invoke>
    <deliverable>Comprehensive unit test suite validating Excel formula accuracy</deliverable>
  </deliverables>

  <risks>
    <risk>CVaR calculation complexity → Use existing portfolio return calculation patterns</risk>
    <risk>Kelly criterion accuracy → Validate against known Excel outputs with real data</risk>
    <risk>Performance impact → Leverage existing optimization suite patterns</risk>
  </risks>
</phase>

### Phase 2: Multi-Account Coordination (6 days)

<phase number="2" estimated_effort="6 days">
  <objective>Develop multi-account coordination with manual balance entry and position tracking</objective>
  <scope>
    Included: Manual account balance entry (IBKR/Bybit/Cash), position value tracking, portfolio coordination
    Excluded: Automated broker API integrations, real-time account feeds
  </scope>
  <dependencies>
    - Phase 1 risk calculation components
    - Database schema extensions for manual data entry
    - Existing portfolio processing service
    - @json/concurrency/portfolio.json for Total Strategies count
  </dependencies>

  <implementation>
    <step>Create manual account balance entry system (IBKR, Bybit, Cash → Net Worth)</step>
    <step>Implement position value tracking from manual IBKR trade fills</step>
    <step>Add drawdown calculator from manual stop-loss distance entries</step>
    <step>Integrate Total Strategies count from @json/concurrency/portfolio.json</step>
    <step>Create dual portfolio coordination (Risk On positions vs Investment holdings)</step>
    <validation>Test with spreadsheet data, validate portfolio calculations against manual entries</validation>
    <rollback>Schema changes are additive; service layer maintains backward compatibility</rollback>
  </implementation>

  <deliverables>
    <deliverable>ManualAccountBalanceService for IBKR/Bybit/Cash entry → Net Worth calculation</deliverable>
    <deliverable>PositionValueTracker for manual IBKR trade fill amounts</deliverable>
    <deliverable>DrawdownCalculator using manual stop-loss distance entries</deliverable>
    <deliverable>StrategiesCountIntegration sourcing Total Strategies from @json/concurrency/portfolio.json</deliverable>
    <deliverable>DualPortfolioManager separating Risk On positions vs Investment holdings</deliverable>
    <deliverable>Extended portfolio schema supporting manual data entry and automated metrics</deliverable>
  </deliverables>

  <risks>
    <risk>Schema migration complexity → Use existing schema evolution patterns</risk>
    <risk>Portfolio calculation accuracy → Extensive validation against Excel outputs</risk>
    <risk>Service integration complexity → Follow existing ServiceCoordinator patterns</risk>
  </risks>
</phase>

### Phase 3: API Integration & Service Orchestration (5 days)

<phase number="3" estimated_effort="5 days">
  <objective>Integrate position sizing with existing strategy analysis pipeline</objective>
  <scope>
    Included: PositionSizingOrchestrator, API endpoints, ServiceCoordinator integration
    Excluded: Web interface, real-time feeds, broker integrations
  </scope>
  <dependencies>
    - Phase 1 & 2 components
    - Existing StrategyExecutionEngine
    - API router infrastructure
  </dependencies>

  <implementation>
    <step>Create PositionSizingOrchestrator coordinating all components</step>
    <step>Extend ServiceCoordinator with position sizing capabilities</step>
    <step>Add position sizing API endpoints to existing router structure</step>
    <step>Integrate with StrategyExecutionEngine for real-time position sizing</step>
    <validation>End-to-end API testing, integration with existing strategy analysis</validation>
    <rollback>New endpoints are additive; existing API functionality preserved</rollback>
  </implementation>

  <deliverables>
    <deliverable>PositionSizingOrchestrator implementing full Excel logic flow</deliverable>
    <deliverable>Enhanced ServiceCoordinator with position sizing integration</deliverable>
    <deliverable>RESTful API endpoints for portfolio dashboard, position analysis</deliverable>
    <deliverable>Integration layer connecting position sizing to strategy analysis</deliverable>
  </deliverables>

  <risks>
    <risk>Service coordination complexity → Follow existing modular patterns</risk>
    <risk>API performance concerns → Use existing async patterns and optimization</risk>
    <risk>Integration breaking existing workflows → Maintain backward compatibility</risk>
  </risks>
</phase>

### Phase 4: Position Sizing Dashboard & Production Readiness (6 days)

<phase number="4" estimated_effort="6 days">
  <objective>Create Position Sizing Dashboard as new web application page and complete production readiness</objective>
  <scope>
    Included: React dashboard page, GraphQL queries, real-time interface, data migration, validation
    Excluded: Mobile app, advanced charting, broker integrations
  </scope>
  <dependencies>
    - Phases 1-3 backend services complete
    - Existing React/Apollo Client architecture
    - GraphQL schema extensions
    - Excel spreadsheet final data export
  </dependencies>

  <implementation>
    <step>Add "Position Sizing" navigation item to existing Navbar component</step>
    <step>Create PositionSizingDashboard React component matching Excel layout</step>
    <step>Implement GraphQL queries for portfolio data, risk metrics, Kelly calculations</step>
    <step>Build real-time dashboard with tables matching Excel screenshots</step>
    <step>Implement Excel data import utilities for historical migration</step>
    <step>Create comprehensive validation framework comparing system vs Excel outputs</step>
    <step>Add monitoring and alerting for position sizing calculations</step>
    <validation>Cross-browser testing, responsive design validation, real-time data updates, full system validation against Excel</validation>
    <rollback>New navigation item can be hidden; existing functionality preserved; Excel spreadsheet maintained as backup</rollback>
  </implementation>

  <deliverables>
    <deliverable>PositionSizingDashboard.tsx component replicating Excel interface</deliverable>
    <deliverable>GraphQL schema extensions for position sizing data</deliverable>
    <deliverable>Real-time dashboard with Portfolio Risk, Active Positions, Incoming Signals, Strategic Holdings</deliverable>
    <deliverable>Responsive design working on desktop/tablet/mobile</deliverable>
    <deliverable>ExcelMigrationUtility for importing historical data and configurations</deliverable>
    <deliverable>ValidationFramework ensuring 100% accuracy vs Excel calculations</deliverable>
    <deliverable>Monitoring dashboard for position sizing system health</deliverable>
    <deliverable>Complete documentation and operational runbooks</deliverable>
  </deliverables>

  <risks>
    <risk>Frontend complexity → Leverage existing React/Bootstrap patterns and components</risk>
    <risk>Real-time updates performance → Use Apollo Client subscriptions and caching</risk>
    <risk>Data migration accuracy → Extensive validation and parallel operation period</risk>
    <risk>Production performance → Load testing and optimization using existing patterns</risk>
    <risk>User adoption resistance → Gradual transition with Excel backup available</risk>
  </risks>
</phase>

## Technical Implementation Details

### Core Components Architecture

```python
# app/tools/risk/cvar_calculator.py
class CVaRCalculator:
    """Implements Excel B12/E11 CVaR calculations using @json/concurrency/ data and @csv/strategies/ backtests"""
    def calculate_trading_cvar(self) -> float:
        """Sources CVaR 95% from @json/concurrency/trades.json: portfolio_metrics.risk.combined_risk.cvar_95
        Cross-references with @csv/strategies/trades.csv for backtest validation"""

    def calculate_investment_cvar(self) -> float:
        """Sources CVaR 95% from @json/concurrency/portfolio.json: portfolio_metrics.risk.combined_risk.cvar_95
        Cross-references with @csv/strategies/portfolio.csv for backtest validation"""

    def get_portfolio_risk_metrics(self) -> Dict[str, float]
    def load_backtest_data(self, strategy_name: str) -> pl.DataFrame:
        """Loads corresponding backtest results from @csv/strategies/ for validation"""

# app/tools/position_sizing/kelly_criterion.py
class KellyCriterionSizer:
    """Implements Excel B17-B21 Kelly calculations using manual trading journal inputs"""
    def calculate_kelly_position(self, num_primary: int, num_outliers: int, kelly_criterion: float) -> float:
        """Uses manually entered values: No. Primary, No. Outliers, Kelly Criterion from trading journal"""

    def calculate_confidence_metrics(self, num_primary: int, num_outliers: int) -> ConfidenceMetrics
    def get_max_risk_per_position(self, portfolio_value: float) -> float

# app/tools/allocation/efficient_frontier_integration.py
class AllocationOptimizer:
    """Integrates with @app/portfolio_review/efficient_frontier.py for automated allocation calculations"""
    def calculate_max_allocation_percentage(self, assets: List[str]) -> Dict[str, float]:
        """Runs efficient frontier analysis and returns optimized allocation percentages"""

    def get_price_data(self, symbol: str) -> float:
        """Fetches current price using existing @app/tools/get_data.py infrastructure"""

# app/api/services/position_sizing_orchestrator.py
class PositionSizingOrchestrator:
    """Coordinates all position sizing operations"""
    def __init__(self):
        self.risk_calculator = CVaRCalculator()
        self.kelly_sizer = KellyCriterionSizer()
        self.account_coordinator = AccountCoordinationService()
        self.allocation_optimizer = AllocationOptimizer()
```

### Database Extensions

```sql
-- Extend existing schema for position sizing
ALTER TABLE portfolio_strategies ADD COLUMN account_type VARCHAR(20);
ALTER TABLE portfolio_strategies ADD COLUMN risk_bucket_level DECIMAL(5,3);

-- New tables for manual data entry and position sizing
CREATE TABLE account_balances (
    id SERIAL PRIMARY KEY,
    account_type VARCHAR(20) NOT NULL, -- 'IBKR', 'Bybit', 'Cash'
    balance DECIMAL(15,2) NOT NULL,     -- Manually entered balance
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE trading_journal_params (
    id SERIAL PRIMARY KEY,
    num_primary INTEGER NOT NULL,       -- Manual entry from trading journal
    num_outliers INTEGER NOT NULL,      -- Manual entry from trading journal
    kelly_criterion DECIMAL(8,6) NOT NULL, -- Manual entry from trading journal
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE position_entries (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    position_value DECIMAL(15,2) NOT NULL,  -- Manual entry from IBKR fill
    max_drawdown DECIMAL(8,6),              -- Manual entry: distance to stop loss
    current_position DECIMAL(15,2),         -- Manual entry from broker positions
    entry_date TIMESTAMP DEFAULT NOW()
);

CREATE TABLE risk_allocations (
    id SERIAL PRIMARY KEY,
    portfolio_id VARCHAR(50) NOT NULL,
    risk_level DECIMAL(5,3) NOT NULL,        -- Currently 0.118 (11.8%)
    allocation_amount DECIMAL(15,2) NOT NULL,
    calculated_at TIMESTAMP DEFAULT NOW()
);
```

### API Integration

```python
# app/api/routers/position_sizing.py
@router.get("/position-sizing/dashboard")
async def get_position_sizing_dashboard():
    """Replaces Excel Screenshot 1 - Portfolio Risk Dashboard"""

@router.get("/position-sizing/positions")
async def get_position_analysis():
    """Replaces Excel Screenshot 2 - Position Analysis"""

@router.post("/position-sizing/calculate")
async def calculate_position_size(request: PositionSizingRequest):
    """Calculate optimal position size for new signals"""
```

### Frontend Dashboard Implementation

```typescript
// app/frontend/sensylate/src/components/PositionSizing/
├── PositionSizingDashboard.tsx        // Main dashboard page
├── PortfolioRiskPanel.tsx             // Screenshot 1 equivalent
├── ActivePositionsTable.tsx           // Screenshot 2 top section
├── IncomingSignalsTable.tsx           // Screenshot 2 middle section
├── StrategicHoldingsTable.tsx         // Screenshot 2 bottom section
└── RiskAllocationBuckets.tsx          // Risk bucket visualization
```

### GraphQL Schema Extensions

```graphql
# Add to existing schema
type PositionSizingDashboard {
  portfolioRisk: PortfolioRiskMetrics
  activePositions: [TradingPosition!]!
  incomingSignals: [SignalAnalysis!]!
  strategicHoldings: [InvestmentHolding!]!
  accountBalances: AccountBalances
  riskAllocationBuckets: [RiskBucket!]!
}

type PortfolioRiskMetrics {
  netWorth: Float!
  cvarTrading: Float!
  cvarInvestment: Float!
  riskAmount: Float!
  kellyMetrics: KellyMetrics!
}

type AccountBalances {
  ibkr: Float!
  bybit: Float!
  cash: Float!
  total: Float!
}

type RiskBucket {
  riskLevel: Float!
  allocationAmount: Float!
  percentage: Float!
}
```

### Integration with Existing Architecture

**Leverage Current Features:**

- **TanStack React Table**: For all data tables (positions, signals, holdings)
- **Apollo Client**: Real-time GraphQL subscriptions for live updates
- **Bootstrap**: Consistent styling with existing application
- **PWA**: Offline position sizing calculations
- **Responsive Design**: Mobile-friendly dashboard

**New Dashboard Route:**

```typescript
// Update App.tsx navigation
const views = [
  { key: 'csv', label: 'CSV Viewer', component: <DataTable /> },
  { key: 'params', label: 'Parameter Testing', component: <ParameterTestingContainer /> },
  { key: 'positions', label: 'Position Sizing', component: <PositionSizingDashboard /> } // NEW
];
```

## Migration Strategy

### Parallel Operation (Weeks 10-12)

1. **Dual System Operation**: Excel continues alongside new system
2. **Validation Period**: Compare outputs daily for accuracy verification
3. **Gradual User Transition**: Train users on new system while Excel remains available
4. **Data Synchronization**: Ensure both systems reflect same underlying data

### Cutover Plan (Week 13)

1. **Final Validation**: 48-hour comprehensive testing period
2. **Data Migration**: Import final Excel configurations and historical data
3. **Go-Live**: Switch primary operations to new system
4. **Monitor**: 72-hour intensive monitoring with Excel backup ready
5. **Excel Deprecation**: Formal retirement after 2-week stability period

## Success Metrics

### Technical Metrics

- **Calculation Accuracy**: 100% match with Excel formulas
- **Performance**: <500ms response time for position sizing calculations
- **Reliability**: 99.9% uptime for position sizing services
- **Data Integrity**: Zero calculation discrepancies during parallel operation

### Business Metrics

- **Operational Efficiency**: 40% reduction in manual Excel maintenance
- **Risk Management**: Real-time risk monitoring vs daily Excel updates
- **Scalability**: Support for unlimited accounts/positions vs Excel limitations
- **User Adoption**: 100% user transition within 4 weeks of go-live

## Risk Mitigation

### Technical Risks

- **Calculation Accuracy**: Comprehensive unit tests for all Excel formulas
- **Performance**: Use existing optimization suite for real-time calculations
- **Data Integrity**: Implement validation checks and audit trails
- **Frontend Complexity**: Leverage existing React/Bootstrap patterns

### Operational Risks

- **User Adoption**: Web interface mirrors Excel layout and workflow
- **Rollback Plan**: Excel remains available for 30 days post-migration
- **Training**: Documentation and tutorials for new system
- **Data Migration**: Extensive validation and parallel operation period

## Timeline Summary

- **Phase 1**: Core Risk Components (8 days)
- **Phase 2**: Multi-Account Coordination (6 days)
- **Phase 3**: API Integration (5 days)
- **Phase 4**: Dashboard & Production (6 days)
- **Total Implementation**: 25 days
- **Parallel Operation**: 3 weeks
- **Go-Live & Stabilization**: 2 weeks
- **Total Project Duration**: ~10 weeks

This architecture plan leverages the existing robust foundation while systematically replacing Excel functionality with scalable, maintainable code that integrates seamlessly with the current trading system infrastructure and provides a modern web-based interface for position sizing operations.
