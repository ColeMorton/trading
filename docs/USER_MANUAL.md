# Trading Strategy Platform - User Manual

## Table of Contents

1. [Quick Start Guide](#quick-start-guide)
2. [Installation Guide](#installation-guide)
3. [Operator Manual](#operator-manual)
4. [Reference Manual](#reference-manual)
5. [Advanced Features](#advanced-features)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start Guide

### 30-Second Setup

Get started with the trading platform in minutes:

```bash
# 1. Check dependencies
make check-deps

# 2. Install databases (macOS)
make install-db

# 3. Start development environment
make dev-local
```

**Access the platform:**
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- GraphQL Playground: http://localhost:8000/graphql
- Health Check: http://localhost:8000/health

### Quick Test

Test the platform with a simple analysis:

```bash
curl -X POST http://localhost:8000/api/ma-cross/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "BTC-USD", "windows": 12}'
```

### What You Get

This platform provides:
- **Strategy Backtesting**: Test moving average, MACD, RSI strategies
- **Portfolio Optimization**: Modern portfolio theory tools
- **Risk Analysis**: 40+ performance metrics
- **Data Management**: Historical price data and results storage
- **API Access**: RESTful and GraphQL interfaces

---

## Installation Guide

### Prerequisites

**Required Software:**
- Python 3.10 or higher
- Poetry (dependency management)
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

#### Step 4: Start Development Server
```bash
make dev-local
```

### Method 2: Docker Installation

#### Prerequisites
```bash
# Check Docker installation
make check-deps
```

#### Setup
```bash
# Build and start all services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
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
```

### Verification

Validate your installation:

```bash
# Run comprehensive validation
poetry run python scripts/validate_phase1.py

# Should show: 7/7 validations passed
```

---

## Operator Manual

### Core Operations

#### Starting the System

**Local Development:**
```bash
# Start databases
make start-local

# Start API server
make dev

# Start with auto-reload
poetry run python -m app.api.run --reload
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
- `csv/portfolios/` - All analyzed portfolios
- `csv/portfolios_filtered/` - Filtered results
- `csv/portfolios_best/` - Top performing strategies
- `csv/price_data/` - Historical price data

#### Portfolio Management

**Load Portfolio Results:**
```python
from app.tools.portfolio import load_portfolio_results

# Load and analyze results
results = load_portfolio_results("csv/portfolios/BTC-USD_D_SMA.csv")
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

# Database health
curl http://localhost:8000/health/database

# Redis health
curl http://localhost:8000/health/redis
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

## Reference Manual

### API Endpoints

#### REST API Endpoints

**Core Analysis:**
- `POST /api/ma-cross/analyze` - Moving average analysis
- `GET /api/ma-cross/status/{execution_id}` - Check analysis status
- `GET /api/ma-cross/stream/{execution_id}` - Real-time progress (SSE)

**Data Management:**
- `GET /api/data/tickers` - List available tickers
- `GET /api/data/price/{ticker}` - Get price data
- `POST /api/data/upload` - Upload custom data

**Scripts and Tools:**
- `GET /api/scripts/list` - List available scripts
- `POST /api/scripts/execute` - Execute analysis scripts

**Health and Status:**
- `GET /health` - Basic health check
- `GET /health/detailed` - Comprehensive system status
- `GET /health/database` - Database connectivity
- `GET /health/redis` - Redis connectivity

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
```bash
make help           # Show all commands
make install        # Install dependencies
make dev            # Start development server
make test           # Run test suite
make docker-up      # Start with Docker
make docker-down    # Stop Docker services
make setup-db       # Setup database
make test-db        # Test database
make backup         # Create backup
make restore        # Restore backup
make check-deps     # Check dependencies
make install-db     # Install databases locally
make start-local    # Start local services
make dev-local      # Start with local databases
```

**Python Scripts:**
```bash
# Validation and testing
poetry run python scripts/validate_phase1.py
poetry run python scripts/test_api_startup.py
poetry run python scripts/simple_db_test.py

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

## Advanced Features

### Async Analysis with Progress Tracking

**Start Asynchronous Analysis:**
```javascript
// Frontend implementation
async function startAnalysis(ticker) {
  const response = await fetch('/api/ma-cross/analyze', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      ticker: ticker,
      windows: 252,
      async_execution: true
    })
  });
  
  const data = await response.json();
  return data.execution_id;
}

// Monitor progress with Server-Sent Events
function monitorProgress(executionId) {
  const eventSource = new EventSource(`/api/ma-cross/stream/${executionId}`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data === "[DONE]") {
      eventSource.close();
      return;
    }
    
    updateProgressBar(data.progress);
    updateStatus(data.message);
    
    if (data.status === "completed") {
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

#### Empty Analysis Results

**Symptom:** `portfolios: []` in API response

**Solutions:**
```bash
# Check if price data exists
ls csv/price_data/

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

**Support Information:**
- **Documentation**: Check `docs/` directory for detailed guides
- **API Reference**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health/detailed
- **Validation**: `poetry run python scripts/validate_phase1.py`

**Before Reporting Issues:**
1. Run system validation: `poetry run python scripts/validate_phase1.py`
2. Check health endpoints: `curl http://localhost:8000/health/detailed`
3. Review recent logs: `tail -100 logs/api.log`
4. Test basic functionality: Simple API call with known ticker
5. Verify environment: Check `.env` file configuration

---

*This manual covers the core functionality of the Trading Strategy Platform. For the latest updates and advanced features, refer to the API documentation and source code.*