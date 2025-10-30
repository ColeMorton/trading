# Trading Strategy Analysis Platform

[![CI/CD Pipeline](https://github.com/ColeMorton/trading/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/ColeMorton/trading/actions/workflows/ci-cd.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Pre-commit](https://github.com/ColeMorton/trading/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/ColeMorton/trading/actions/workflows/pre-commit.yml)
[![Security Scanning](https://github.com/ColeMorton/trading/actions/workflows/security.yml/badge.svg)](https://github.com/ColeMorton/trading/actions/workflows/security.yml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

A comprehensive platform for trading strategy analysis, backtesting, and portfolio optimization with both CLI and REST API interfaces.

## Features

- **Strategy Analysis**: Moving average crossovers, MACD, RSI, and custom strategies
- **Portfolio Management**: Risk analysis, performance metrics, optimization
- **Statistical Analysis**: Statistical Performance Divergence System (SPDS)
- **Concurrency Analysis**: Multi-strategy correlation and portfolio construction
- **REST API**: Full-featured async API with job queuing and real-time updates
- **CLI Tools**: 47+ commands for comprehensive trading analysis

## Quick Start

### Option 1: Full Stack (API + Database)

```bash
# Install dependencies
poetry install

# Start all services with Docker
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# Test the API
curl http://localhost:8000/health
open http://localhost:8000/api/docs
```

### Option 2: CLI Only

```bash
# Install dependencies
poetry install

# Run your first analysis
poetry run trading-cli strategy run --ticker AAPL --strategy SMA

# Check results
ls data/raw/portfolios/
```

## Documentation

- **[Master Index](INDEX.md)** - Complete navigation guide
- **[Quick Start](docs/getting-started/QUICK_START.md)** - Get running in 5 minutes
- **[API Documentation](docs/api/README.md)** - REST API reference
- **[User Guide](docs/USER_GUIDE.md)** - Comprehensive guide
- **[Development Guide](docs/development/DEVELOPMENT_GUIDE.md)** - For contributors

## Project Structure

```
trading/
├── app/
│   ├── api/              # REST API (FastAPI)
│   ├── cli/              # Command-line interface
│   ├── core/             # Core business logic
│   ├── strategies/       # Trading strategies
│   ├── tools/            # Analysis tools
│   └── contexts/         # Domain contexts
├── docs/                 # All documentation
├── tests/                # Test suite
├── data/                 # Data storage
├── scripts/              # Utility scripts
└── docker-compose.yml    # Docker configuration
```

## Available Commands

### Using Make

```bash
make help              # Show all commands
make install           # Install dependencies
make test              # Run test suite
make lint-all          # Run all linters and formatters
make docker-up         # Start Docker services
make dev-local         # Start API locally
```

### Using CLI

```bash
trading-cli --help              # Show all commands
trading-cli strategy run        # Run strategy analysis
trading-cli portfolio update    # Update portfolios
trading-cli spds analyze        # Statistical analysis
trading-cli concurrency analyze # Concurrency analysis
```

### Using API

```bash
# View interactive documentation
open http://localhost:8000/api/docs

# Create a strategy job
curl -X POST http://localhost:8000/api/v1/strategy/run \
  -H "X-API-Key: dev-key-000000000000000000000000" \
  -H "Content-Type: application/json" \
  -d '{"ticker":"BTC-USD","fast_period":20,"slow_period":50}'
```

## Key Technologies

[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Poetry](https://img.shields.io/badge/Poetry-60A5FA?logo=poetry&logoColor=white)](https://python-poetry.org/)

- **Python 3.11+** - Core language
- **Poetry** - Dependency management
- **FastAPI** - REST API framework
- **ARQ** - Async job queue
- **PostgreSQL** - Database
- **Redis** - Caching and queuing
- **Polars** - High-performance data processing
- **VectorBT** - Backtesting engine
- **Docker** - Containerization

## Development Setup

```bash
# Clone repository
git clone <repository-url>
cd trading

# Install dependencies
poetry install

# Install pre-commit hooks (for contributors)
make pre-commit-install

# Run tests
make test

# Format and lint code
make lint-all
```

## Code Quality

This project maintains high code quality standards:

- **Ruff** - Fast, modern linting and formatting (replaces Black, isort, Flake8)
- **mypy** - Static type checking
- **Bandit** - Security scanning
- **Pre-commit hooks** - Automated checks

See [Code Quality Guide](docs/development/CODE_QUALITY.md) for details.

## Testing

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration
make test-api

# Run with coverage
make test-full
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `make lint-all` and `make test`
5. Submit a pull request

See [Development Guide](docs/development/DEVELOPMENT_GUIDE.md) for detailed contribution guidelines.

## Resources

- **Documentation Hub**: [docs/README.md](docs/README.md)
- **Master Index**: [INDEX.md](INDEX.md)
- **API Docs**: http://localhost:8000/api/docs (when running)
- **Command Reference**: [docs/reference/COMMAND_REFERENCE.md](docs/reference/COMMAND_REFERENCE.md)

## License

See LICENSE file for details.

---

**Ready to start?** See [Quick Start Guide](docs/getting-started/QUICK_START.md)
**Need help?** Check [Master Index](INDEX.md) for complete navigation
