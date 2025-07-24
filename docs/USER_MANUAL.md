# Trading Strategy Platform - User Manual

## Table of Contents

1. [Quick Start Guide](#quick-start-guide)
2. [Installation Guide](#installation-guide)
3. [Operator Manual](#operator-manual)
4. [Reference Manual](#reference-manual)
5. [Advanced Features](#advanced-features)
6. [GraphQL API Guide](#graphql-api-guide)
7. [Testing Infrastructure](#testing-infrastructure)
8. [Production Deployment](#production-deployment)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start Guide

### 30-Second Setup

Get started with the trading platform in minutes:

```bash
# 1. Check dependencies
make check-deps

# 2. Install databases (macOS)
make install-db

# 3. Setup full-stack development environment
make setup-fullstack

# 4. Start both backend and frontend
make dev-fullstack

# 5. Run comprehensive test suite
make test
```

**Access the platform:**

- Frontend App: http://localhost:5173
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- GraphQL Playground: http://localhost:8000/graphql
- Health Dashboard: http://localhost:8000/health/detailed
- Metrics: http://localhost:8000/health/metrics

### Quick Test

Test the platform with a simple analysis:

```bash
curl -X POST http://localhost:8000/api/ma-cross/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "BTC-USD", "windows": 12}'
```

### What You Get

This platform provides:

- **Frontend Web App**: React PWA with real-time analysis interface
- **Strategy Backtesting**: Test moving average, MACD, RSI strategies
- **Portfolio Optimization**: Modern portfolio theory tools
- **Risk Analysis**: 40+ performance metrics
- **Data Management**: PostgreSQL database with automated backups
- **API Access**: RESTful and GraphQL interfaces
- **Production Ready**: Docker containerization with CI/CD pipeline
- **Real-time Monitoring**: Health checks, metrics, and performance tracking

---

## Installation Guide

### Prerequisites

**Required Software:**

- Python 3.10 or higher
- Poetry (dependency management)
- Node.js 18+ and npm (for frontend)
- Git

**Database Options:**

- **Option A**: PostgreSQL 15+ and Redis (local installation)
- **Option B**: Docker and Docker Compose (containerized)

### Method 1: Local Development (Recommended)

#### Step 1: Clone and Setup

```bash
git clone <repository-url>
cd trading
poetry install
```

#### Step 2: Database Installation (macOS)

```bash
# Install databases via Homebrew
make install-db

# Alternative manual installation
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis
```

#### Step 3: Database Configuration

```bash
# Setup database and schema
make setup-db

# Verify installation
make test-db
```

#### Step 4: Frontend Setup

```bash
# Install frontend dependencies and generate GraphQL types
make setup-frontend
```

#### Step 5: Start Development Environment

```bash
# Start both backend and frontend
make dev-fullstack

# Or start individually:
make dev-local      # Backend only
make frontend-dev   # Frontend only
```

### Method 2: Docker Installation (Recommended for Production)

#### Prerequisites

```bash
# Check Docker installation
make check-deps
```

#### Development Setup

```bash
# Build and start all services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

#### Production Setup

```bash
# Copy production environment template
cp .env.production.example .env.production
# Edit .env.production with your values

# Build production images
docker compose -f docker-compose.prod.yml build

# Start production services
docker compose -f docker-compose.prod.yml up -d

# Check health
curl http://localhost/health/detailed
```

### Environment Configuration

Create `.env` file (copy from `.env.example`):

```env
# Database Configuration
DATABASE_URL=postgresql://colemorton@localhost:5432/trading_db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=trading_db
DATABASE_USER=colemorton

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379

# API Configuration
API_HOST=127.0.0.1
API_PORT=8000

# GraphQL Configuration
ENABLE_GRAPHQL=true
VITE_USE_GRAPHQL=true

# Architecture Configuration
ENVIRONMENT=development
ENABLE_DEPENDENCY_INJECTION=true
LOG_LEVEL=INFO
```

### Verification

Validate your installation:

```bash
# Run comprehensive validation
poetry run python scripts/validate_phase1.py

# Should show: 7/7 validations passed

# Test dependency injection
poetry run python app/api/test_dependency_injection.py
```

---

## Operator Manual

### Core Operations

#### Starting the System

**Local Development:**

```bash
# Start full-stack (recommended)
make dev-fullstack

# Or start components individually:
make start-local    # Databases only
make dev           # Backend API only
make frontend-dev  # Frontend only
```

**Production:**

```bash
# Start all services
make docker-up

# Check health
curl http://localhost:8000/health
```

#### Strategy Analysis

**Basic Moving Average Analysis:**

```bash
curl -X POST http://localhost:8000/api/ma-cross/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "windows": 89,
    "strategy_types": ["SMA", "EMA"],
    "min_criteria": {
      "sharpe_ratio": 1.0,
      "profit_factor": 1.5
    }
  }'
```

**Multiple Ticker Analysis:**

```bash
curl -X POST http://localhost:8000/api/ma-cross/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": ["BTC-USD", "ETH-USD", "SPY"],
    "windows": 50,
    "async_execution": true
  }'
```

#### Data Management

**Price Data Download:**

```python
# Using Python tools
from app.tools.download_data import download_ticker_data

# Download historical data
download_ticker_data("AAPL", "1d", "2020-01-01", "2024-01-01")
```

**CSV Export Locations:**

- `data/outputs/portfolio_analysis/` - All analyzed portfolios (59-column canonical schema)
- `data/outputs/portfolio_analysis/filtered/` - Filtered results (59-column canonical schema)
- `data/outputs/portfolio_analysis/best/` - Top performing strategies (59-column canonical schema)
- `data/outputs/strategies/` - Strategy export files (59-column canonical schema)
- `data/raw/prices/` - Historical price data (OHLCV format)

**CSV Schema Standardization:**

All portfolio CSV exports now use a standardized 59-column canonical schema for consistency and enhanced analytical capabilities. This includes comprehensive risk metrics, trade analysis, and performance indicators. See `docs/CSV_SCHEMA_MIGRATION_GUIDE.md` for migration details.

#### Portfolio Management

**Load Portfolio Results:**

```python
from app.tools.portfolio import load_portfolio_results

# Load and analyze results
results = load_portfolio_results("data/raw/portfolios/BTC-USD_D_SMA.csv")
```

**Filter Portfolios:**

```python
from app.tools.portfolio.filters import apply_filters

# Apply performance filters
filtered = apply_filters(results, {
    "sharpe_ratio": 1.5,
    "max_drawdown": 0.2,
    "trades": 20
})
```

### Monitoring and Health Checks

**System Health:**

```bash
# Check all systems
curl http://localhost:8000/health/detailed

# Kubernetes-style checks
curl http://localhost:8000/health/live    # Liveness probe
curl http://localhost:8000/health/ready   # Readiness probe

# Prometheus metrics
curl http://localhost:8000/health/metrics
```

**Log Monitoring:**

```bash
# API logs
tail -f logs/api.log

# Database logs (PostgreSQL)
tail -f /opt/homebrew/var/log/postgresql@15.log

# Service status
brew services list | grep -E "(postgres|redis)"
```

### Backup and Recovery

**Create Backup:**

```bash
# Full system backup
make backup

# Database only
poetry run python app/database/backup_simple.py create
```

**Restore Backup:**

```bash
# Restore from backup
make restore BACKUP_FILE=backups/backup_20240601_120000.tar.gz
```

### Performance Tuning

**Database Optimization:**

```sql
-- Connect to PostgreSQL
psql trading_db

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_price_data_symbol_date ON price_data(symbol, date);
CREATE INDEX IF NOT EXISTS idx_portfolios_performance ON portfolios(total_return, sharpe_ratio);
```

**Memory Configuration:**

```bash
# Increase shared memory (PostgreSQL)
echo "shared_preload_libraries = 'pg_stat_statements'" >> postgresql.conf

# Redis memory optimization
redis-cli CONFIG SET maxmemory 1gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

---

## Architecture and Design Patterns

### Dependency Injection Framework

The platform implements a comprehensive dependency injection (DI) system to reduce coupling and improve testability. This enterprise-grade pattern ensures clean separation of concerns and makes the codebase more maintainable.

#### Core Interfaces

All major services are defined by abstract interfaces in `/app/core/interfaces/`:

- **LoggingInterface** - Logging operations
- **ProgressTrackerInterface** - Async progress tracking
- **StrategyExecutorInterface** - Strategy execution
- **StrategyAnalyzerInterface** - Strategy analysis
- **PortfolioManagerInterface** - Portfolio management
- **DataAccessInterface** - Data access and storage
- **CacheInterface** - Caching operations
- **MonitoringInterface** - Metrics and monitoring
- **ConfigurationInterface** - Configuration management

#### Using Dependency Injection

**In API Routes:**

```python
from fastapi import Depends
from app.api.dependencies import get_logger, get_strategy_executor
from app.core.interfaces import LoggingInterface, StrategyExecutorInterface

@router.post("/analyze")
async def analyze(
    request: AnalysisRequest,
    logger: LoggingInterface = Depends(get_logger),
    executor: StrategyExecutorInterface = Depends(get_strategy_executor)
):
    log = logger.get_logger(__name__)
    log.info(f"Processing analysis for {request.ticker}")

    result = await executor.execute(
        strategy_type="ma_cross",
        tickers=[request.ticker],
        config=request.dict()
    )
    return result
```

**Creating Custom Services:**

```python
from app.core.interfaces import DataAccessInterface
from app.api.dependencies import get_service

class MyCustomService:
    def __init__(self, data_access: DataAccessInterface):
        self.data_access = data_access

    async def process_data(self, ticker: str):
        # Service uses injected data access
        data = await self.data_access.get_price_data(ticker)
        return self.analyze(data)

# Register in dependencies.py
_container.register(
    MyCustomServiceInterface,
    lambda: MyCustomService(
        data_access=_container.get(DataAccessInterface)
    )
)
```

#### Testing with Mock Services

```python
import pytest
from unittest.mock import Mock
from app.api.dependencies import get_service, _container
from app.core.interfaces import LoggingInterface

@pytest.fixture
def mock_logger():
    mock = Mock(spec=LoggingInterface)
    _container.register_singleton(LoggingInterface, mock)
    yield mock
    # Cleanup after test
    _container._instances.pop(LoggingInterface, None)

def test_my_function(mock_logger):
    # Your test uses the mock automatically
    service = get_service(LoggingInterface)
    assert service == mock_logger
```

### Shared Type System

The platform uses a centralized type system in `/app/core/types/` to ensure consistency:

**Common Types:**

```python
from app.core.types import (
    TimeFrame,      # Trading timeframes (1m, 5m, 1h, 1d, etc.)
    SignalType,     # BUY, SELL, HOLD, CLOSE
    OrderType,      # MARKET, LIMIT, STOP, STOP_LIMIT
    StrategyType,   # MA_CROSS, MACD, RSI, etc.
    TaskStatus,     # PENDING, RUNNING, COMPLETED, FAILED
)

# Using types in your code
async def create_order(
    ticker: str,
    signal: SignalType,
    order_type: OrderType = OrderType.MARKET
):
    if signal == SignalType.BUY:
        # Process buy order
        pass
```

**Data Types:**

```python
from app.core.types import PriceData, Signal, Trade

# Create a signal
signal = Signal(
    timestamp=datetime.now(),
    ticker="BTC-USD",
    signal_type=SignalType.BUY,
    price=45000.0,
    confidence=0.85
)

# Create a trade record
trade = Trade(
    id="trade_123",
    ticker="BTC-USD",
    entry_time=datetime.now(),
    entry_price=45000.0,
    quantity=0.1,
    side=PositionSide.LONG
)
```

### Benefits of the Architecture

1. **Reduced Coupling** - Services depend on interfaces, not concrete implementations
2. **Better Testability** - Easy to inject mock services for unit testing
3. **Clear Contracts** - Interfaces define exact expectations between layers
4. **Flexibility** - Swap implementations without changing dependent code
5. **No Circular Dependencies** - DI pattern prevents circular imports
6. **Async Integration** - Services use async/await for non-blocking operations and efficient caching

---

## Reference Manual

### API Endpoints

#### REST API Endpoints

**Core Analysis:**

- `POST /api/ma-cross/analyze` - Moving average analysis (async with caching)
- `GET /api/ma-cross/status/{execution_id}` - Check analysis status
- `GET /api/ma-cross/stream/{execution_id}` - Real-time progress (SSE)

**API Versioning:**

- `GET /api/versions` - List all API versions and their status
- `GET /api/migration/{from_version}/to/{to_version}` - Get migration guide between versions
- `GET /api/deprecation/{version}` - Get deprecation notice for a version
- `GET /api/v1/*` - Version 1 API endpoints (current stable)

**Service Management:**

- `GET /api/container/health` - Health status of all services in DI container
- `GET /api/container/registrations` - Information about all service registrations
- `POST /api/services/initialize` - Initialize all registered services
- `POST /api/services/shutdown` - Shutdown all services gracefully
- `GET /api/services/health` - Health status via service orchestrator

**Event Bus and Messaging:**

- `GET /api/events/metrics` - Event bus metrics and statistics
- `GET /api/events/subscriptions` - Current event subscriptions
- `GET /api/events/history?limit=50` - Recent event history
- `POST /api/events/publish` - Publish a test event

**Long Operations Management:**

- `GET /api/operations/metrics` - Operation queue metrics
- `GET /api/operations?status=running` - List operations with optional status filter
- `GET /api/operations/{operation_id}` - Get status of specific operation
- `POST /api/operations/data-analysis` - Start data analysis operation
- `POST /api/operations/portfolio-optimization` - Start portfolio optimization
- `DELETE /api/operations/{operation_id}` - Cancel a running operation

**Data Management:**

- `GET /api/data/tickers` - List available tickers
- `GET /api/data/price/{ticker}` - Get price data
- `POST /api/data/upload` - Upload custom data

**Scripts and Tools:**

- `GET /api/scripts/list` - List available scripts
- `POST /api/scripts/execute` - Execute analysis scripts

**Health and Status:**

- `GET /health` - Basic health check
- `GET /health/detailed` - Comprehensive system status with all subsystems
- `GET /health/live` - Kubernetes liveness probe
- `GET /health/ready` - Kubernetes readiness probe
- `GET /health/metrics` - Prometheus-compatible metrics endpoint

#### GraphQL Schema

**Core Types:**

```graphql
type Portfolio {
  id: ID!
  name: String!
  strategy: Strategy!
  timeframe: Timeframe!
  parameters: JSON!
  performance: PerformanceMetrics!
  signals: [Signal!]!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Strategy {
  id: ID!
  name: String!
  type: StrategyType!
  config: JSON!
  performance: PerformanceMetrics!
}

type PerformanceMetrics {
  totalReturn: Float!
  sharpeRatio: Float!
  sortinoRatio: Float!
  calmarRatio: Float!
  maxDrawdown: Float!
  winRate: Float!
  profitFactor: Float!
  numTrades: Int!
}
```

**Queries:**

```graphql
query GetPortfolios($filter: PortfolioFilter) {
  portfolios(filter: $filter) {
    id
    name
    strategy {
      name
      type
    }
    performance {
      totalReturn
      sharpeRatio
      maxDrawdown
    }
  }
}

query GetPriceData($symbol: String!, $timeframe: Timeframe!) {
  priceData(symbol: $symbol, timeframe: $timeframe) {
    date
    open
    high
    low
    close
    volume
  }
}
```

**Mutations:**

```graphql
mutation CreatePortfolio($input: CreatePortfolioInput!) {
  createPortfolio(input: $input) {
    id
    name
    performance {
      totalReturn
      sharpeRatio
    }
  }
}

mutation ExecuteStrategy($portfolioId: ID!) {
  executeStrategy(portfolioId: $portfolioId) {
    success
    executionId
    result {
      performance {
        totalReturn
        sharpeRatio
      }
    }
  }
}
```

### Database Schema

**Core Tables:**

```sql
-- Tickers and assets
CREATE TABLE tickers (
    id TEXT PRIMARY KEY,
    symbol TEXT UNIQUE NOT NULL,
    name TEXT,
    asset_class TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Price data storage
CREATE TABLE price_data (
    id TEXT PRIMARY KEY,
    ticker_id TEXT REFERENCES tickers(id),
    timeframe TEXT NOT NULL,
    date TIMESTAMP NOT NULL,
    open DECIMAL NOT NULL,
    high DECIMAL NOT NULL,
    low DECIMAL NOT NULL,
    close DECIMAL NOT NULL,
    volume BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Strategy definitions
CREATE TABLE strategies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    config JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Portfolio definitions
CREATE TABLE portfolios (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Backtest results
CREATE TABLE backtest_results (
    id TEXT PRIMARY KEY,
    portfolio_id TEXT REFERENCES portfolios(id),
    strategy_id TEXT REFERENCES strategies(id),
    ticker_id TEXT REFERENCES tickers(id),
    metrics JSONB NOT NULL,
    signals JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Configuration Files

**Environment Variables (.env):**

```env
# Database
DATABASE_URL=postgresql://user@localhost:5432/trading_db
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=trading_db
DATABASE_USER=user

# Redis
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379

# API
API_HOST=127.0.0.1
API_PORT=8000
DEBUG=true

# Feature Flags
ENABLE_GRAPHQL=true
ENABLE_ASYNC_EXECUTION=true
ENABLE_PROGRESS_TRACKING=true

# Architecture Configuration
ENVIRONMENT=development
ENABLE_DEPENDENCY_INJECTION=true
ENABLE_ENHANCED_DI=true
ENABLE_EVENT_BUS=true
ENABLE_ASYNC_MESSAGING=true
LOG_LEVEL=INFO
LOG_FORMAT=json

# API Versioning
API_VERSION_DEFAULT=v1
API_VERSION_DEPRECATION_WARNINGS=true

# Service Configuration
SERVICE_HEALTH_CHECK_INTERVAL=60
SERVICE_STARTUP_TIMEOUT=30
SERVICE_SHUTDOWN_TIMEOUT=10

# Event Bus Configuration
EVENT_BUS_MAX_WORKERS=4
EVENT_BUS_MAX_HISTORY=1000

# Long Operations
OPERATION_QUEUE_MAX_CONCURRENT=4
OPERATION_DEFAULT_TIMEOUT=300

# Production Settings
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=your-domain.com
CORS_ORIGINS=https://your-domain.com
RATE_LIMIT_PER_MINUTE=60
```

**Strategy Configuration:**

```json
{
  "ma_cross": {
    "default_windows": 89,
    "strategy_types": ["SMA", "EMA"],
    "timeframes": ["1d", "1h"],
    "min_criteria": {
      "trades": 10,
      "win_rate": 0.5,
      "profit_factor": 1.0,
      "sharpe_ratio": 0.5
    }
  },
  "macd": {
    "fast_period": 12,
    "slow_period": 26,
    "signal_period": 9
  },
  "rsi": {
    "period": 14,
    "overbought": 70,
    "oversold": 30
  }
}
```

### CLI Tools and Scripts

**Available Make Commands:**

**Setup & Dependencies:**

```bash
make help               # Show all commands
make check-deps         # Check system dependencies
make install            # Install backend dependencies
make install-db         # Install databases locally
make setup-db           # Setup database schema
make setup-frontend     # Setup frontend (install + codegen)
make setup-fullstack    # Setup both backend and frontend
```

**Development:**

```bash
make dev                # Start backend development server
make dev-local          # Start backend with local databases
make frontend-dev       # Start frontend development server
make dev-fullstack      # Start both backend and frontend
make frontend-codegen   # Generate GraphQL TypeScript types
```

**Testing Commands:**

```bash
make test               # Run comprehensive test suite with unified runner
make test-quick         # Quick smoke and unit tests
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-full          # All test categories
```

**Frontend Commands:**

```bash
make frontend-install   # Install frontend dependencies
make frontend-build     # Build frontend for production
make frontend-test      # Run frontend E2E tests (requires dev servers running)
make test-fullstack     # Run E2E tests with automatic server startup
make frontend-lint      # Run frontend linting
make frontend-clean     # Clean frontend build artifacts
```

**Database & Services:**

```bash
make start-local        # Start local database services
make test-db           # Test database connectivity
make backup            # Create database backup
make restore           # Restore from backup
```

**Docker & Production:**

```bash
make docker-up         # Start with Docker Compose
make docker-down       # Stop Docker services
make docker-logs       # View service logs
```

**Python Scripts:**

```bash
# Testing and validation
poetry run python tests/run_unified_tests.py quick           # Enhanced unified test runner
poetry run python scripts/validate_phase1.py               # System validation
poetry run python scripts/test_api_startup.py              # API startup test
poetry run python scripts/simple_db_test.py                # Database connectivity

# Test infrastructure management
poetry run python tests/infrastructure/phase2_runner_migration.py  # Test runner health check

# Database management
poetry run python app/database/backup_simple.py create
poetry run python app/database/migrations.py

# Strategy analysis
poetry run python app/ma_cross/1_get_portfolios.py
poetry run python app/strategies/update_portfolios.py
```

### Performance Metrics

**Available Metrics (40+):**

**Return Metrics:**

- `total_return` - Total portfolio return
- `annualized_return` - Annualized return
- `risk_free_return` - Risk-free rate adjusted return
- `excess_return` - Return above risk-free rate

**Risk Metrics:**

- `sharpe_ratio` - Risk-adjusted return
- `sortino_ratio` - Downside risk-adjusted return
- `calmar_ratio` - Return vs maximum drawdown
- `max_drawdown` - Maximum peak-to-trough loss
- `volatility` - Price volatility
- `downside_volatility` - Downside volatility only

**Trade Statistics:**

- `num_trades` - Total number of trades
- `win_rate` - Percentage of winning trades
- `avg_trade_return` - Average return per trade
- `avg_trade_duration` - Average holding period
- `profit_factor` - Gross profit / gross loss
- `expectancy` - Expected value per trade

**Advanced Risk:**

- `var_95` - Value at Risk (95% confidence)
- `cvar_95` - Conditional Value at Risk
- `kelly_criterion` - Optimal position sizing
- `beta` - Market sensitivity
- `alpha` - Excess return vs benchmark
- `information_ratio` - Active return vs tracking error

---

## Enhanced Architecture Features

### API Versioning

The platform supports full API versioning with safe evolution and migration support:

**Version Management:**

```bash
# Check all available API versions
curl http://localhost:8000/api/versions

# Access v1 API (current stable)
curl http://localhost:8000/api/v1/

# Get migration guide when upgrading
curl http://localhost:8000/api/migration/v1/to/v2

# Check deprecation status
curl http://localhost:8000/api/deprecation/v1
```

**Version Headers:**

```bash
# Specify version via header
curl -H "API-Version: v1" http://localhost:8000/api/scripts/list

# Use Accept header
curl -H "Accept: application/vnd.trading-api;version=v1" http://localhost:8000/api/data/tickers
```

**Frontend Integration:**

```javascript
// Automatic version detection
const response = await fetch('/api/v1/ma-cross/analyze', {
  method: 'POST',
  headers: {
    'API-Version': 'v1',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(analysisRequest),
});

// Handle deprecation warnings
if (response.headers.get('Deprecation') === 'true') {
  const sunsetDate = response.headers.get('Sunset');
  console.warn(`API version deprecated. Sunset: ${sunsetDate}`);
}
```

### Event-Driven Architecture

**Publishing Events:**

```python
from app.api.event_bus import publish_event, TradingEvents

# Publish portfolio events
event_id = await publish_event(
    event_type=TradingEvents.PORTFOLIO_CREATED,
    data={'portfolio_id': 'pf_123', 'strategy': 'ma_cross'},
    source='portfolio_service'
)
```

**Event Subscriptions:**

```python
from app.api.event_bus import EventHandler, subscribe_to_events

class PortfolioNotificationHandler(EventHandler):
    async def handle(self, event):
        if event.event_type == TradingEvents.PORTFOLIO_CREATED:
            # Send notification
            await send_notification(event.data)

    def get_event_types(self):
        return [TradingEvents.PORTFOLIO_CREATED, TradingEvents.PORTFOLIO_UPDATED]

# Subscribe to events
handler = PortfolioNotificationHandler()
subscription_id = subscribe_to_events(handler)
```

**Event Monitoring:**

```bash
# Check event bus metrics
curl http://localhost:8000/api/events/metrics

# View recent events
curl http://localhost:8000/api/events/history?limit=20

# See active subscriptions
curl http://localhost:8000/api/events/subscriptions

# Publish test event
curl -X POST http://localhost:8000/api/events/publish \
  -H "Content-Type: application/json" \
  -d '{"event_type": "test.event", "data": {"message": "hello"}, "source": "manual"}'
```

### Long Operation Management

**Starting Long Operations:**

```bash
# Start data analysis
curl -X POST http://localhost:8000/api/operations/data-analysis \
  -H "Content-Type: application/json" \
  -d '{"dataset_size": 10000, "timeout": 600}'

# Start portfolio optimization
curl -X POST http://localhost:8000/api/operations/portfolio-optimization \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BTC-USD", "ETH-USD", "SPY"], "timeout": 300}'
```

**Monitoring Operations:**

```bash
# Check operation status
curl http://localhost:8000/api/operations/op_123456

# List all running operations
curl http://localhost:8000/api/operations?status=running

# View operation queue metrics
curl http://localhost:8000/api/operations/metrics

# Cancel an operation
curl -X DELETE http://localhost:8000/api/operations/op_123456
```

**Progress Streaming (JavaScript):**

```javascript
// Monitor operation progress with Server-Sent Events
function monitorOperation(operationId) {
  const eventSource = new EventSource(`/api/operations/${operationId}/stream`);

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
      case 'progress':
        updateProgressBar(data.data.progress.percentage);
        updateStatusMessage(data.data.progress.message);
        break;
      case 'completed':
        displayResults(data.data.result);
        eventSource.close();
        break;
      case 'failed':
        showError(data.data.error);
        eventSource.close();
        break;
    }
  };

  return eventSource;
}
```

### Enhanced Service Management

**Service Health Monitoring:**

```bash
# Check enhanced DI container health
curl http://localhost:8000/api/container/health

# View service registrations
curl http://localhost:8000/api/container/registrations

# Check service orchestrator
curl http://localhost:8000/api/services/health
```

**Service Lifecycle Management:**

```bash
# Initialize all services
curl -X POST http://localhost:8000/api/services/initialize

# Graceful shutdown
curl -X POST http://localhost:8000/api/services/shutdown
```

**Custom Service Registration:**

```python
from app.api.service_patterns import ServiceOrchestrator, BaseService

class CustomAnalyticsService(BaseService):
    @property
    def metadata(self):
        return ServiceMetadata(
            name="analytics",
            version="1.0.0",
            description="Custom analytics service",
            dependencies=["logging", "data_access"]
        )

    async def _initialize_impl(self):
        # Custom initialization
        self.analytics_engine = AnalyticsEngine()
        await self.analytics_engine.connect()

    async def _health_check_impl(self):
        return self.analytics_engine.is_healthy()

# Register with orchestrator
orchestrator = service_orchestrator
orchestrator.register_service(
    "analytics",
    CustomAnalyticsService,
    dependencies=["logging", "data_access"]
)
```

---

## Advanced Features

### Service Extension with Dependency Injection

The platform's dependency injection framework makes it easy to extend functionality:

**Creating a Custom Strategy Analyzer:**

```python
from app.core.interfaces import StrategyAnalyzerInterface
from app.infrastructure.strategy import StrategyAnalyzer

class CustomStrategyAnalyzer(StrategyAnalyzer):
    """Extended analyzer with custom indicators."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._register_custom_strategies()

    def _register_custom_strategies(self):
        # Add custom strategy implementations
        self._strategy_implementations['bollinger'] = self._analyze_bollinger
        self._strategy_implementations['mean_reversion'] = self._analyze_mean_reversion

    def _analyze_bollinger(self, ticker, data, config):
        # Custom Bollinger Bands implementation
        pass

# Register in dependencies
from app.api.dependencies import _container
_container.register(
    StrategyAnalyzerInterface,
    lambda: CustomStrategyAnalyzer(
        data_access=_container.get(DataAccessInterface),
        logger=_container.get(LoggingInterface)
    )
)
```

**Creating a Custom Data Source:**

```python
from app.core.interfaces import DataAccessInterface
from app.infrastructure.data import DataAccessService

class AlphaVantageDataService(DataAccessService):
    """Data service using Alpha Vantage API."""

    def __init__(self, api_key: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = api_key

    async def download_data(self, ticker, start_date, end_date, interval="1d"):
        # Custom implementation using Alpha Vantage
        url = f"https://api.alphavantage.co/query?symbol={ticker}&apikey={self.api_key}"
        # ... download and process data
        return data

# Use the custom service
data_service = get_service(DataAccessInterface)
data = await data_service.download_data("AAPL", start, end)
```

### Async Analysis with Progress Tracking

**Start Asynchronous Analysis:**

```javascript
// Frontend implementation
async function startAnalysis(ticker) {
  const response = await fetch('/api/ma-cross/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ticker: ticker,
      windows: 252,
      async_execution: true,
    }),
  });

  const data = await response.json();
  return data.execution_id;
}

// Monitor progress with Server-Sent Events
function monitorProgress(executionId) {
  const eventSource = new EventSource(`/api/ma-cross/stream/${executionId}`);

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data === '[DONE]') {
      eventSource.close();
      return;
    }

    updateProgressBar(data.progress);
    updateStatus(data.message);

    if (data.status === 'completed') {
      displayResults(data.result);
      eventSource.close();
    }
  };
}
```

### Portfolio Optimization

**Modern Portfolio Theory:**

```python
from app.portfolio_optimization.tools.portfolio_analysis import optimize_portfolio

# Define portfolio
assets = ["BTC-USD", "ETH-USD", "SPY", "QQQ"]
weights = [0.4, 0.3, 0.2, 0.1]

# Run optimization
optimization_result = optimize_portfolio(
    assets=assets,
    start_date="2023-01-01",
    end_date="2024-01-01",
    method="max_sharpe",
    constraints={
        "max_weight": 0.5,
        "min_weight": 0.05
    }
)

print(f"Optimized weights: {optimization_result.weights}")
print(f"Expected return: {optimization_result.expected_return:.4f}")
print(f"Risk: {optimization_result.risk:.4f}")
print(f"Sharpe ratio: {optimization_result.sharpe_ratio:.4f}")
```

### Custom Strategy Development

**Create Custom Strategy:**

```python
from app.tools.strategy.base import BaseStrategy
from app.tools.data_types import SignalType

class CustomStrategy(BaseStrategy):
    def __init__(self, fast_period=10, slow_period=30):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signals(self, price_data):
        # Calculate indicators
        fast_ma = price_data['close'].rolling(self.fast_period).mean()
        slow_ma = price_data['close'].rolling(self.slow_period).mean()

        # Generate signals
        signals = []
        for i in range(len(price_data)):
            if fast_ma.iloc[i] > slow_ma.iloc[i]:
                signals.append(SignalType.BUY)
            elif fast_ma.iloc[i] < slow_ma.iloc[i]:
                signals.append(SignalType.SELL)
            else:
                signals.append(SignalType.HOLD)

        return signals

    def backtest(self, price_data, signals):
        # Implement backtesting logic
        return self.calculate_performance_metrics(price_data, signals)

# Register and use
strategy = CustomStrategy(fast_period=5, slow_period=20)
results = strategy.run_backtest("AAPL", "2023-01-01", "2024-01-01")
```

### Synthetic Data Generation

**Generate Synthetic Pairs:**

```python
from app.tools.synthetic_ticker import create_synthetic_pair

# Create BTC/Gold ratio
synthetic_data = create_synthetic_pair(
    ticker1="BTC-USD",
    ticker2="GLD",
    operation="ratio",
    start_date="2023-01-01",
    end_date="2024-01-01"
)

# Analyze synthetic instrument
results = analyze_ma_cross(
    ticker="BTC-USD_GLD_RATIO",
    data=synthetic_data,
    windows=50
)
```

### Risk Management

**Implement Stop Loss:**

```python
from app.tools.stop_loss_simulator import apply_stop_loss

# Configure stop loss
stop_loss_config = {
    "method": "atr",
    "multiplier": 2.0,
    "lookback": 14
}

# Apply to portfolio
portfolio_with_sl = apply_stop_loss(
    portfolio_data=portfolio,
    config=stop_loss_config
)

print(f"Max drawdown without SL: {portfolio.max_drawdown:.2%}")
print(f"Max drawdown with SL: {portfolio_with_sl.max_drawdown:.2%}")
```

---

## GraphQL API Guide

### Overview

The platform now includes a complete GraphQL API alongside the REST API, providing:

- Type-safe queries and mutations
- Efficient data fetching (request only what you need)
- Real-time subscriptions support (future)
- Auto-generated TypeScript types
- GraphiQL interactive playground

### Accessing GraphQL

**Endpoints:**

- GraphQL API: `http://localhost:8000/graphql`
- GraphiQL Playground: `http://localhost:8000/graphql` (browser)

### Example Queries

**Get Portfolios with Performance:**

```graphql
query GetPortfolios($limit: Int) {
  portfolios(filter: { limit: $limit }) {
    id
    name
    type
    ticker {
      symbol
      name
    }
    performance {
      totalReturn
      sharpeRatio
      maxDrawdown
      winRate
      profitFactor
    }
    createdAt
  }
}
```

**Get Price Data:**

```graphql
query GetPriceData($symbol: String!, $startDate: DateTime) {
  priceData(symbol: $symbol, filter: { startDate: $startDate }) {
    date
    open
    high
    low
    close
    volume
  }
}
```

### Example Mutations

**Execute MA Cross Analysis:**

```graphql
mutation RunMACrossAnalysis($input: MACrossAnalysisInput!) {
  executeMaCrossAnalysis(input: $input) {
    ... on MACrossAnalysisResponse {
      status
      totalPortfoliosAnalyzed
      executionTime
      portfolios {
        ticker
        strategyType
        shortWindow
        longWindow
        performance {
          totalReturn
          sharpeRatio
          maxDrawdown
          winRate
        }
      }
    }
    ... on AsyncAnalysisResponse {
      executionId
      statusUrl
      estimatedTime
    }
  }
}

# Variables
{
  "input": {
    "ticker": ["BTC-USD", "ETH-USD"],
    "windows": 50,
    "strategyTypes": ["MA_CROSS"],
    "asyncExecution": false
  }
}
```

**Create Portfolio:**

```graphql
mutation CreatePortfolio($input: PortfolioInput!) {
  createPortfolio(input: $input) {
    id
    name
    type
    performance {
      totalReturn
      sharpeRatio
    }
  }
}
```

### Frontend Integration

**Enable GraphQL in Sensylate App:**

```bash
# Using make commands (recommended)
make frontend-install
make frontend-codegen
make frontend-dev

# Or manual setup
cd app/frontend/sensylate
echo "VITE_USE_GRAPHQL=true" > .env
npm install
npm run codegen
npm run dev
```

**Using Generated Hooks:**

```typescript
import { useGetPortfoliosQuery } from './graphql/generated';

function PortfolioList() {
  const { data, loading, error } = useGetPortfoliosQuery({
    variables: { limit: 10 }
  });

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <ul>
      {data?.portfolios.map(portfolio => (
        <li key={portfolio.id}>
          {portfolio.name} - Return: {portfolio.performance.totalReturn}%
        </li>
      ))}
    </ul>
  );
}
```

### GraphQL vs REST

**When to use GraphQL:**

- Need specific fields only (avoid over-fetching)
- Multiple related resources in one request
- Type safety is critical
- Building modern React applications

**When to use REST:**

- Simple CRUD operations
- File uploads/downloads
- Legacy system integration
- Streaming responses (SSE)

---

## Testing Infrastructure

### Overview

The platform features an enterprise-grade testing infrastructure with intelligent unified test execution. The testing framework provides:

- **Intelligent Parallel Execution** - Auto-scaling workers based on system resources
- **Smart Test Categorization** - Automatic test discovery and categorization
- **Performance Monitoring** - Real-time resource usage and execution metrics
- **Concurrent Category Execution** - Safe concurrent execution with isolation management
- **Enhanced Reporting** - Comprehensive performance insights and recommendations

### Unified Test Runner

The core testing infrastructure is built around `/tests/run_unified_tests.py`, which provides comprehensive test execution capabilities:

**Quick Test Execution:**

```bash
# Run comprehensive test suite
make test

# Run quick tests (smoke + unit)
poetry run python tests/run_unified_tests.py quick

# Run specific test category
poetry run python tests/run_unified_tests.py unit

# Run with parallel execution
poetry run python tests/run_unified_tests.py unit --parallel

# Run multiple categories concurrently
poetry run python tests/run_unified_tests.py unit integration --concurrent

# Run with coverage
poetry run python tests/run_unified_tests.py api --coverage

# Show what would be executed (dry run)
poetry run python tests/run_unified_tests.py all --dry-run
```

### Test Categories

The testing system automatically categorizes tests based on markers and paths:

#### **Unit Tests**

- **Description**: Fast unit tests for individual components
- **Execution**: Parallel with auto-scaling workers
- **Isolation Level**: Low (minimal resource conflicts)
- **Max Duration**: 5 minutes
- **Markers**: `unit`, `fast`

#### **Integration Tests**

- **Description**: Integration tests for component interactions
- **Execution**: Sequential for data integrity
- **Isolation Level**: Medium (database/service interactions)
- **Max Duration**: 15 minutes
- **Markers**: `integration`

#### **API Tests**

- **Description**: API endpoint and service tests
- **Execution**: Parallel with 4 workers
- **Isolation Level**: High (full test isolation)
- **Max Duration**: 10 minutes
- **Markers**: `api`

#### **Strategy Tests**

- **Description**: Trading strategy validation tests
- **Execution**: Parallel with 2 workers
- **Isolation Level**: High (financial calculations need isolation)
- **Max Duration**: 20 minutes
- **Markers**: `strategy`

#### **E2E Tests**

- **Description**: End-to-end system validation tests
- **Execution**: Sequential for system-wide tests
- **Isolation Level**: Maximum (full system isolation)
- **Max Duration**: 30 minutes
- **Markers**: `e2e`

#### **Performance Tests**

- **Description**: Performance and regression tests
- **Execution**: Sequential for accurate benchmarking
- **Isolation Level**: Maximum (no interference)
- **Max Duration**: 1 hour
- **Markers**: `performance`, `slow`

#### **Smoke Tests**

- **Description**: Quick smoke tests for basic functionality
- **Execution**: Parallel with auto-scaling
- **Isolation Level**: Low (fast and simple)
- **Max Duration**: 2 minutes
- **Markers**: `fast`, `smoke`

### Intelligent Features

#### **Auto-Scaling Workers**

The test runner automatically calculates optimal worker counts based on:

- CPU core availability (reserves 1 core for system)
- Memory requirements per test category
- System load and resource constraints
- Test isolation requirements

```bash
# System with 10 CPU cores, 16GB RAM
# Automatically allocates 8 workers for unit tests
# Reduces to 2 workers for memory-intensive strategy tests
poetry run python tests/run_unified_tests.py unit
# Output: 🧪 Running unit tests: Fast unit tests for individual components
# ⚡8w | ⏱️ Max: 5m0s | 💾 Memory: 100MB | 🖥️ CPU: 0.5 cores
```

#### **Performance Monitoring**

Real-time system monitoring tracks:

- CPU and memory usage during test execution
- Test execution performance (tests per second)
- Parallel execution efficiency
- Memory efficiency (tests per MB used)
- Slow test identification

#### **Smart Coverage Detection**

The runner automatically detects which modules to cover based on test paths:

- API tests → `app.api`, `app.api.services`, `app.api.routers`
- Strategy tests → `app.strategies`, `app.concurrency`
- Tools tests → `app.tools`

### Advanced Usage

#### **Custom Test Execution**

```bash
# List available test categories
poetry run python tests/run_unified_tests.py --list

# Run all tests with enhanced reporting
poetry run python tests/run_unified_tests.py all --verbose --concurrent

# Override worker count
poetry run python tests/run_unified_tests.py unit --parallel --workers 4

# Stop on first failure
poetry run python tests/run_unified_tests.py integration --fail-fast

# Save results to JSON
poetry run python tests/run_unified_tests.py ci --save results.json
```

#### **Predefined Test Suites**

```bash
# Quick development feedback
poetry run python tests/run_unified_tests.py quick
# Runs: smoke + unit tests

# CI/CD pipeline
poetry run python tests/run_unified_tests.py ci
# Runs: unit + integration + api tests

# Full test suite
poetry run python tests/run_unified_tests.py all
# Runs: all test categories
```

#### **Performance Analysis**

The test runner provides comprehensive performance insights:

```bash
# Example output with performance metrics
🚀 Starting test execution for categories: unit, integration
⚡ Execution mode: Concurrent
🖥️ System: 10 cores, 16.0GB RAM
💾 Available: 12.5GB (78.1%)

✅ unit: PASSED (45.2s) ⚡8w
   📊 142 tests, 3.1 tests/sec
   🐌 Slowest: test_complex_calculation (2.45s)

✅ integration: PASSED (67.8s) 🔄1w
   📊 28 tests, 0.4 tests/sec

📊 ENHANCED TEST EXECUTION SUMMARY
🔄 Execution Mode: Concurrent
⏱️ Total Duration: 82.1 seconds
📈 Success Rate: 100.0%
⚡ Tests/Second: 2.1
🚀 Parallel Efficiency: 85.2%
💾 Memory Used: 245MB (1.4 tests/MB)
```

### Integration with Development Workflow

#### **Make Commands**

The testing infrastructure integrates with the standard development workflow:

```bash
# Standard test execution
make test                    # Run comprehensive test suite
make test-quick             # Quick smoke and unit tests
make test-unit              # Unit tests only
make test-integration       # Integration tests only
make test-full              # All test categories

# Advanced test options (planned)
make test-parallel          # Force parallel execution
make test-coverage          # Run with coverage reporting
make test-performance       # Performance regression tests
```

#### **CI/CD Integration**

The unified test runner supports CI/CD pipelines:

```yaml
# Example GitHub Actions integration
- name: Run Test Suite
  run: |
    poetry run python tests/run_unified_tests.py ci --coverage --save ci_results.json

- name: Performance Tests
  run: |
    poetry run python tests/run_unified_tests.py performance --save perf_results.json
```

### Test Execution Features

The unified test runner provides advanced capabilities:

- **Intelligent parallel execution** with auto-scaling workers
- **Smart resource management** and system awareness
- **Enhanced reporting** with actionable insights
- **Concurrent category execution** for compatible test types
- **Performance optimization** with up to 40% faster execution

### Performance Benefits

**Key Improvements:**

- **40%+ Faster Execution** - Through intelligent parallel execution
- **Smart Resource Usage** - Auto-scaling based on system capacity
- **Enhanced Reliability** - Isolation-level management prevents test pollution
- **Better Insights** - Comprehensive performance metrics and recommendations
- **Simplified Usage** - Single unified command interface

**System Requirements:**

- Minimum: 4 CPU cores, 8GB RAM
- Recommended: 8+ CPU cores, 16GB+ RAM
- Python 3.10+ with Poetry
- pytest-xdist for parallel execution

---

## Production Deployment

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- Domain name with DNS configured
- SSL certificates (Let's Encrypt recommended)
- PostgreSQL backup storage
- Monitoring infrastructure (optional)

### Quick Deployment

**1. Environment Setup:**

```bash
# Copy production configuration
cp .env.production.example .env.production

# Edit configuration
vim .env.production

# Required variables:
# - POSTGRES_PASSWORD
# - REDIS_PASSWORD
# - SECRET_KEY
# - ALLOWED_HOSTS
# - CORS_ORIGINS
```

**2. Build and Deploy:**

```bash
# Build production images
docker compose -f docker-compose.prod.yml build

# Run database migrations
docker compose -f docker-compose.prod.yml up -d postgres
docker compose -f docker-compose.prod.yml run --rm api ./scripts/migrate.sh

# Start all services
docker compose -f docker-compose.prod.yml up -d

# Verify deployment
curl https://your-domain.com/health/detailed
```

### Production Architecture

```
Internet
    |
    ↓
Nginx (SSL, Rate Limiting)
    |
    ├─→ Frontend (React PWA)
    |
    └─→ API (FastAPI + GraphQL)
         |
         ├─→ PostgreSQL (Primary DB)
         └─→ Redis (Cache & Sessions)
```

### Security Features

**Network Security:**

- Rate limiting (60 req/min default, configurable)
- CORS configuration
- Security headers (HSTS, CSP, XSS Protection)
- API key authentication (optional)

**Application Security:**

- SQL injection prevention (Prisma ORM)
- Input validation
- Request size limits (10MB default)
- Non-root container users

### Monitoring

**Built-in Monitoring:**

```bash
# Prometheus metrics
curl https://your-domain.com/health/metrics

# Grafana dashboards (optional)
docker compose -f docker-compose.prod.yml --profile monitoring up -d
# Access at http://your-domain.com:3000
```

**Health Endpoints:**

- `/health` - Basic check
- `/health/ready` - All services ready
- `/health/live` - Application alive
- `/health/detailed` - Full system status

### Backup and Recovery

**Automated Backups:**

```bash
# Enable backup service
docker compose -f docker-compose.prod.yml --profile backup up -d

# Manual backup
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > backup_$(date +%Y%m%d).sql.gz
```

**Restore Process:**

```bash
# Stop API service
docker compose -f docker-compose.prod.yml stop api

# Restore database
gunzip < backup_20240101.sql.gz | docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U $POSTGRES_USER $POSTGRES_DB

# Restart services
docker compose -f docker-compose.prod.yml up -d
```

### CI/CD Pipeline

The platform includes a complete GitHub Actions CI/CD pipeline:

**Pipeline Stages:**

1. **Linting** - Code quality checks
2. **Testing** - Unit and integration tests
3. **Security** - Vulnerability scanning
4. **Build** - Docker image creation
5. **Deploy** - Automated deployment

**Triggering Deployment:**

```bash
# Deploy to staging (develop branch)
git push origin develop

# Deploy to production (main branch)
git push origin main
```

### SSL/TLS Configuration

**Using Let's Encrypt:**

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com

# Copy to nginx
sudo cp /etc/letsencrypt/live/your-domain.com/*.pem nginx/ssl/

# Restart nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### Performance Optimization

**Database Indexes:**

```sql
-- Already included in migration
-- Run manually if needed:
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U $POSTGRES_USER -d $POSTGRES_DB -f /database/indexes.sql
```

**Redis Optimization:**

```bash
# Set memory limit
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli CONFIG SET maxmemory 512mb

# Enable persistence
docker compose -f docker-compose.prod.yml exec redis \
  redis-cli CONFIG SET save "900 1 300 10 60 10000"
```

### Troubleshooting Production

**Check Service Status:**

```bash
# View all services
docker compose -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f nginx

# Restart service
docker compose -f docker-compose.prod.yml restart api
```

**Common Issues:**

1. **502 Bad Gateway**

   - Check if API is running: `docker compose -f docker-compose.prod.yml ps api`
   - Check API logs: `docker compose -f docker-compose.prod.yml logs api`

2. **Database Connection Failed**

   - Verify credentials in `.env.production`
   - Check database logs: `docker compose -f docker-compose.prod.yml logs postgres`

3. **High Memory Usage**
   - Check resource limits in `docker-compose.prod.yml`
   - Monitor with: `docker stats`

---

## Troubleshooting

### Common Issues

#### Database Connection Errors

**Symptom:** `psycopg2.OperationalError: could not connect`

**Solutions:**

```bash
# Check PostgreSQL status
brew services list | grep postgres

# Restart PostgreSQL
brew services restart postgresql@15

# Check if database exists
psql -l | grep trading_db

# Create database if missing
createdb trading_db

# Update connection string in .env
DATABASE_URL=postgresql://$(whoami)@localhost:5432/trading_db
```

#### Redis Connection Errors

**Symptom:** `redis.exceptions.ConnectionError`

**Solutions:**

```bash
# Check Redis status
brew services list | grep redis

# Start Redis
brew services start redis

# Test connection
redis-cli ping

# Should return "PONG"
```

#### API Server Won't Start

**Symptom:** `ImportError` or `ModuleNotFoundError`

**Solutions:**

```bash
# Reinstall dependencies
poetry install

# Check Python version
python --version  # Should be 3.10+

# Try manual start
poetry run python -m app.api.run

# Check for port conflicts
lsof -i :8000
```

#### Frontend Won't Start

**Symptom:** `Module not found` or `npm command not found`

**Solutions:**

```bash
# Check Node.js and npm
make frontend-check-deps

# Install frontend dependencies
make frontend-install

# Regenerate GraphQL types
make frontend-codegen

# Try manual start
cd app/frontend/sensylate && npm run dev

# Check for port conflicts
lsof -i :5173
```

#### Frontend Tests Failing

**Symptom:** `ERR_CONNECTION_REFUSED` when running `make frontend-test`

**Solutions:**

```bash
# Frontend tests require both backend and frontend servers to be running

# Option 1: Start servers manually in separate terminals
# Terminal 1: Start backend
make dev-local

# Terminal 2: Start frontend
make frontend-dev

# Terminal 3: Run tests
make frontend-test

# Option 2: Use full-stack development setup
make dev-fullstack  # Starts both servers
# Then in another terminal:
make frontend-test

# Option 3: Automated test with server startup (recommended)
make test-fullstack  # Automatically starts servers, runs tests, stops servers

# Check server status
curl http://localhost:8000/health  # Backend
curl http://localhost:5173        # Frontend
```

#### Test Execution Issues

**Symptom:** Test runner fails or shows poor performance

**Solutions:**

```bash
# Check test infrastructure health
poetry run python tests/infrastructure/phase2_runner_migration.py

# Run tests with dry-run to validate configuration
poetry run python tests/run_unified_tests.py all --dry-run

# Check system resources for optimal worker allocation
poetry run python tests/run_unified_tests.py unit --verbose

# Run specific test category to isolate issues
poetry run python tests/run_unified_tests.py smoke

# Force sequential execution if parallel fails
poetry run python tests/run_unified_tests.py unit --parallel false
```

#### Empty Analysis Results

**Symptom:** `portfolios: []` in API response

**Solutions:**

```bash
# Check if price data exists
ls data/raw/price_data/

# Download missing data
poetry run python app/tools/download_data.py AAPL

# Reduce filtering criteria
{
  "min_criteria": {
    "trades": 5,
    "win_rate": 0.3,
    "profit_factor": 0.8
  }
}

# Check data quality
poetry run python app/tools/data_processing.py validate AAPL
```

#### Memory Issues with Large Analyses

**Symptom:** `MemoryError` or slow performance

**Solutions:**

```bash
# Use smaller window sizes
"windows": 50  # instead of 252

# Analyze fewer tickers at once
"ticker": "BTC-USD"  # instead of array

# Enable async execution
"async_execution": true

# Increase system memory limits
ulimit -m unlimited
```

### Debug Mode

**Enable Detailed Logging:**

```bash
# Set debug level in .env
DEBUG=true
LOG_LEVEL=DEBUG

# Start with verbose logging
poetry run python -m app.api.run --reload --log-level debug

# Monitor logs
tail -f logs/api.log
tail -f logs/database.log
```

**Database Debug Queries:**

```sql
-- Check recent activity
SELECT * FROM backtest_results ORDER BY created_at DESC LIMIT 10;

-- Check data availability
SELECT ticker_id, COUNT(*) as records
FROM price_data
GROUP BY ticker_id
ORDER BY records DESC;

-- Check portfolio count
SELECT COUNT(*) as total_portfolios FROM portfolios;
```

### Performance Optimization

**Database Tuning:**

```sql
-- Add performance indexes
CREATE INDEX CONCURRENTLY idx_price_data_symbol_date
ON price_data(ticker_id, date DESC);

CREATE INDEX CONCURRENTLY idx_backtest_metrics
ON backtest_results USING GIN (metrics);

-- Update statistics
ANALYZE;
```

**API Optimization:**

```python
# Use connection pooling
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Enable caching
REDIS_CACHE_TTL=3600

# Use async execution for large requests
ASYNC_EXECUTION_THRESHOLD=100
```

### Getting Help

**Log Collection:**

```bash
# Collect system info
make system-info > debug_info.txt

# Collect logs
tar -czf logs.tar.gz logs/

# Run diagnostics
poetry run python scripts/diagnose_system.py
```

**Advanced Features Troubleshooting:**

**API Versioning Issues:**

```bash
# Check API version status
curl http://localhost:8000/api/versions

# Test v1 endpoints specifically
curl http://localhost:8000/api/v1/

# Check for deprecation warnings
curl -I http://localhost:8000/api/ma-cross/analyze
```

**Event Bus Issues:**

```bash
# Check event bus metrics
curl http://localhost:8000/api/events/metrics

# Verify event publishing works
curl -X POST http://localhost:8000/api/events/publish \
  -H "Content-Type: application/json" \
  -d '{"event_type": "test", "data": {}, "source": "debug"}'

# Check event history
curl http://localhost:8000/api/events/history?limit=10
```

**Long Operation Issues:**

```bash
# Check operation queue status
curl http://localhost:8000/api/operations/metrics

# List stuck operations
curl http://localhost:8000/api/operations?status=running

# Cancel problematic operations
curl -X DELETE http://localhost:8000/api/operations/{operation_id}
```

**Enhanced DI Container Issues:**

```bash
# Check container health
curl http://localhost:8000/api/container/health

# View service registrations
curl http://localhost:8000/api/container/registrations

# Test service orchestrator
curl http://localhost:8000/api/services/health
```

**Support Information:**

- **Documentation**: Check `docs/` directory for detailed guides
  - `dependency_injection_guide.md` - DI framework guide
  - `code_owner_architecture_review_2025.md` - Architecture overview
  - `csv_schemas.md` - Data format specifications
  - **Testing Infrastructure**: [Testing Infrastructure](#testing-infrastructure) section
- **API Reference**: http://localhost:8000/docs
- **GraphQL Playground**: http://localhost:8000/graphql
- **Health Check**: http://localhost:8000/health/detailed
- **Validation**: `poetry run python scripts/validate_phase1.py`
- **Testing**: `poetry run python tests/run_unified_tests.py quick`
- **Test Infrastructure**: `poetry run python tests/infrastructure/phase2_runner_migration.py`
- **DI Testing**: `poetry run python app/api/test_dependency_injection.py`
- **API Versioning**: http://localhost:8000/api/versions
- **Event Bus Metrics**: http://localhost:8000/api/events/metrics
- **Operations Queue**: http://localhost:8000/api/operations/metrics
- **Service Health**: http://localhost:8000/api/container/health

**Before Reporting Issues:**

1. Run system validation: `poetry run python scripts/validate_phase1.py`
2. Check test infrastructure: `poetry run python tests/infrastructure/phase2_runner_migration.py`
3. Check health endpoints: `curl http://localhost:8000/health/detailed`
4. Run quick test suite: `poetry run python tests/run_unified_tests.py quick`
5. Review recent logs: `tail -100 logs/api.log`
6. Test basic functionality: Simple API call with known ticker
7. Verify environment: Check `.env` file configuration

---

\*This manual covers the core functionality of the Trading Strategy Platform. The platform offers enterprise-grade features with:

- **Clean Architecture** - Dependency injection with interface-based design
- **Docker Containerization** - Production-ready deployment
- **Dual API Support** - Both REST and GraphQL interfaces
- **Type Safety** - Centralized type system with strict contracts
- **Automated Operations** - Backups, CI/CD pipeline, health monitoring
- **High Performance** - Polars-based data processing, Redis caching
- **Enterprise Security** - Rate limiting, CORS, input validation
- **Advanced Testing Infrastructure** - Intelligent parallel execution with enhanced performance

For architectural details, see the [Architecture and Design Patterns](#architecture-and-design-patterns) section and [Testing Infrastructure](#testing-infrastructure) for comprehensive testing capabilities.\*
