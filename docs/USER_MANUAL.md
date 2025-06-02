# Trading Strategy Platform - User Manual

## Table of Contents

1. [Quick Start Guide](#quick-start-guide)
2. [Installation Guide](#installation-guide)
3. [Operator Manual](#operator-manual)
4. [Reference Manual](#reference-manual)
5. [Advanced Features](#advanced-features)
6. [GraphQL API Guide](#graphql-api-guide)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

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

# GraphQL Configuration (new)
ENABLE_GRAPHQL=true
VITE_USE_GRAPHQL=true
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

# Production Settings (new)
ENVIRONMENT=production
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

**Frontend Commands:**
```bash
make frontend-install   # Install frontend dependencies
make frontend-build     # Build frontend for production
make frontend-test      # Run frontend E2E tests
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

*This manual covers the core functionality of the Trading Strategy Platform, including the completed GraphQL + PostgreSQL migration (Phases 1-4). The platform now offers enterprise-grade features with Docker containerization, GraphQL API, automated backups, CI/CD pipeline, and production-ready deployment capabilities.*
