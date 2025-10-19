# Quick Start Guide

Get up and running with the trading system in 5 minutes.

## Prerequisites

- Python 3.10+
- Poetry
- Docker (recommended) or PostgreSQL 15+ and Redis locally

## Choose Your Path

### Path A: Full Stack with API (Recommended)

Complete system with REST API, database, and async job execution.

### Path B: CLI Only

Just the command-line interface for local analysis.

---

## Path A: Full Stack Setup (Docker)

### Step 1: Install and Start Services

```bash
# Clone and install
git clone <repository-url>
cd trading
poetry install

# Start all services (API, PostgreSQL, Redis, Worker)
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head
```

### Step 2: Test the API

```bash
# Test health
curl http://localhost:8000/health

# Open interactive docs
open http://localhost:8000/api/docs
```

### Step 3: Execute a Strategy via API

```bash
curl -X POST http://localhost:8000/api/v1/strategy/run \
  -H "X-API-Key: dev-key-000000000000000000000000" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "BTC-USD",
    "fast_period": 20,
    "slow_period": 50
  }'
```

**Next**: See [API Documentation](../api/README.md) for complete guide.

---

## Path B: CLI Only Setup

### Step 1: Install Dependencies

```bash
# Clone and install
git clone <repository-url>
cd trading

# Install with Poetry
poetry install
poetry shell
```

### Step 2: Initialize System

```bash
# Verify installation
trading-cli --help

# Check status
trading-cli tools health
```

### Step 3: Run First Strategy Analysis

```bash
# Quick analysis with defaults
trading-cli strategy run --ticker AAPL --strategy SMA

# Preview with dry run
trading-cli strategy run --ticker AAPL --strategy SMA --dry-run
```

### Step 4: Check Results

```bash
# View generated portfolios
ls data/raw/portfolios/

# List recent results
trading-cli portfolio list --recent
```

---

## Path C: Local Development (No Docker)

### Prerequisites

- PostgreSQL 15+ running locally
- Redis running locally

### Step 1: Start Local Services

```bash
# Using Homebrew (macOS)
brew services start postgresql@15
brew services start redis

# Verify
pg_isready
redis-cli ping
```

### Step 2: Setup Database

```bash
# Create database
createdb trading_db

# Run migrations
poetry run alembic upgrade head
```

### Step 3: Configure Environment

Create `.env`:

```bash
DATABASE_URL=postgresql://$(whoami)@localhost:5432/trading_db
REDIS_URL=redis://localhost:6379
ENVIRONMENT=development
DEBUG=true
```

### Step 4: Start API and Worker

```bash
# Terminal 1: API
poetry run uvicorn app.api.main:app --reload --port 8000

# Terminal 2: Worker
poetry run arq app.api.jobs.worker.WorkerSettings
```

Or use the startup script:

```bash
./scripts/start_api.sh
```

---

## Common Commands

### Strategy Analysis

```bash
# Single ticker
trading-cli strategy run --ticker AAPL --strategy SMA

# Multiple tickers
trading-cli strategy run --ticker AAPL,MSFT,GOOGL --strategy SMA,EMA

# Using profile
trading-cli strategy run --profile ma_cross_crypto
```

### Portfolio Management

```bash
# Update portfolios
trading-cli portfolio update --validate

# Export data
trading-cli portfolio export --format json
```

### Statistical Analysis

```bash
# Analyze portfolio
trading-cli spds analyze risk_on.csv

# Interactive mode
trading-cli spds interactive
```

### Configuration

```bash
# List profiles
trading-cli config list

# Show profile
trading-cli config show ma_cross_crypto

# Validate
trading-cli config validate
```

## Understanding Output

```
data/raw/portfolios/          # Individual strategy results
data/raw/portfolios_best/     # Best performing strategies
data/raw/portfolios_filtered/ # Filtered by criteria
exports/statistical_analysis/ # Statistical exports
exports/backtesting_parameters/ # Backtesting results
```

## Troubleshooting

### Connection Issues

```bash
# Check Docker services
docker-compose ps

# Restart services
docker-compose restart

# View logs
docker-compose logs -f api
```

### Database Issues

```bash
# Run migrations
alembic upgrade head

# Check connection
trading-cli tools health
```

### Worker Not Processing Jobs

```bash
# Check worker logs
docker-compose logs -f arq_worker

# Restart worker
docker-compose restart arq_worker
```

## Next Steps

### For API Users

1. Read [API Documentation](../api/README.md)
2. Explore http://localhost:8000/api/docs
3. Try the 33 available endpoints

### For CLI Users

1. Read [User Guide](../USER_GUIDE.md)
2. Check [Command Reference](../reference/COMMAND_REFERENCE.md)
3. Explore [Strategy Analysis](../features/STRATEGY_ANALYSIS.md)

### For Developers

1. Read [Development Guide](../development/DEVELOPMENT_GUIDE.md)
2. Check [System Architecture](../architecture/SYSTEM_ARCHITECTURE.md)
3. Review [Code Quality Guide](../development/CODE_QUALITY.md)

---

You're ready to start! Choose your path above and follow the steps.
