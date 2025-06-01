# Trading Application

A comprehensive trading strategy analysis platform with GraphQL API, PostgreSQL database, and React frontend.

## Features

- **Strategy Analysis**: Moving average crossovers, MACD, RSI, and more
- **Portfolio Management**: Risk analysis, performance metrics, and optimization
- **Data Management**: Historical price data, backtesting results, and real-time monitoring
- **GraphQL API**: Type-safe API with comprehensive schema
- **React Frontend**: Modern PWA with offline capabilities

## Development Setup

### Prerequisites

- Python 3.10+
- Poetry
- PostgreSQL 15+
- Redis
- Node.js 18+ (for frontend)

### Quick Start

```bash
# Install dependencies
make install

# Install databases (macOS with Homebrew)
make install-db

# Start local development
make dev-local

# Or use Docker
make docker-up
```

### Available Commands

```bash
make help           # Show all available commands
make check-deps     # Check system dependencies
make install-db     # Install PostgreSQL and Redis
make start-local    # Start local database services
make dev-local      # Start API with local databases
make setup-db       # Setup database schema and migrate data
make test-db        # Test database setup
make backup         # Create database backup
```

## Architecture

- **Backend**: FastAPI + Strawberry GraphQL + PostgreSQL + Redis
- **Frontend**: React 18 + TypeScript + Apollo Client + Vite
- **Database**: PostgreSQL with Prisma ORM
- **Caching**: Redis for session and query caching
- **Deployment**: Docker containers with Docker Compose

## API Documentation

- **REST API**: http://localhost:8000/docs
- **GraphQL Playground**: http://localhost:8000/graphql
- **Health Checks**: http://localhost:8000/health

## Project Structure

```
app/
├── api/           # FastAPI REST API
├── database/      # Database configuration and migrations
├── sensylate/     # React frontend application
└── tools/         # Shared utilities and tools

csv/               # Historical data storage
json/              # Configuration files
scripts/           # Setup and utility scripts
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License