# Trading Platform - Master Index

Complete navigation guide for the trading strategy analysis platform.

## Quick Navigation

### New Users - Start Here!

1. [Quick Start Guide](docs/getting-started/QUICK_START.md) - Get running in 5 minutes
2. [User Guide](docs/USER_GUIDE.md) - Comprehensive user documentation

### API Users

1. [API Documentation](docs/api/README.md) - REST API reference
2. [API Getting Started](docs/api/GETTING_STARTED.md) - API setup guide
3. Interactive Docs: http://localhost:8000/api/docs (when running)

### Developers

1. [Development Guide](docs/development/DEVELOPMENT_GUIDE.md) - Dev environment setup
2. [Code Quality](docs/development/CODE_QUALITY.md) - Code standards and tools
3. [System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md) - Architecture overview

---

## Documentation Structure

### Getting Started

- [Quick Start](docs/getting-started/QUICK_START.md) - 5-minute setup (CLI or API)
- [Docker Setup](docs/getting-started/DOCKER_SETUP.md) - Docker Compose guide
- [Setup Summary](docs/getting-started/setup_summary.txt) - Installation notes

### API Documentation

- [API README](docs/api/README.md) - Complete API documentation
- [Sweep Results API](docs/api/SWEEP_RESULTS_API.md) - Sweep endpoint reference
- [API Data Flow](docs/api/API_DATA_FLOW.md) - How data flows through the system
- [Integration Guide](docs/api/INTEGRATION_GUIDE.md) - Best practices
- [Quick Reference](docs/api/QUICK_REFERENCE.md) - Quick syntax card
- [API Getting Started](docs/api/GETTING_STARTED.md) - API setup guide
- [Examples](docs/api/examples/) - Working code examples

### Development

- [Development Guide](docs/development/DEVELOPMENT_GUIDE.md) - Dev environment
- [Code Quality](docs/development/CODE_QUALITY.md) - Linting and formatting
- [Code Quality Improvement](docs/development/CODE_QUALITY_IMPROVEMENT.md) - Gradual improvement
- [SSH Guide](docs/development/SSH_GUIDE.md) - Remote development
- [AI Assistant Guide](docs/development/AI_ASSISTANT_GUIDE.md) - Using Claude/AI
- [Workflow Testing](docs/development/WORKFLOW_TESTING.md) - CI/CD workflows
- [Next Steps](docs/development/next_steps.md) - Upcoming improvements
- [Workflows Guide](docs/development/workflows.md) - GitHub Actions reference

### Database

- [Database Overview](docs/database/README.md) - Database documentation hub
- [Database Schema](docs/database/SCHEMA.md) - Complete schema reference
- [Migration Changelog](docs/database/CHANGELOG.md) - Migration history
- [SQL Views Guide](docs/database/SQL_VIEWS_GUIDE.md) - 19 database views + queries

### Architecture

- [System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md) - High-level design
- [Data Loader Extraction](docs/architecture/data_loader_extraction_summary.md)
- [Formatter Extraction](docs/architecture/formatter_extraction_summary.md)
- [Refactoring Results](docs/architecture/refactoring_integration_test_results.md)

### Features

- [Strategy Analysis](docs/features/STRATEGY_ANALYSIS.md) - Trading strategies

### Testing

- [Testing Best Practices](docs/testing/TESTING_BEST_PRACTICES.md)
- [TDD Guidelines](docs/testing/TDD_GUIDELINES.md)
- [TDD Workflow](docs/testing/DEVELOPER_TDD_WORKFLOW.md)
- [Test Organization](docs/testing/TEST_ORGANIZATION.md)
- [Test Suite Overview](docs/testing/TEST_SUITE_OVERVIEW.md)
- [Test Architecture Details](docs/testing/TEST_ARCHITECTURE_DETAILS.md)
- [API Test Guide](docs/testing/API_TEST_GUIDE.md)
- [Integration Test Guide](docs/testing/INTEGRATION_TEST_GUIDE.md)

### Reference

- [Command Reference](docs/reference/COMMAND_REFERENCE.md) - All CLI commands
- [Configuration Guide](docs/CONFIGURATION_GUIDE.md) - Configuration options
- [CSV Schemas](docs/csv_schemas.md) - Data format reference
- [Tools Reference](docs/reference/tools/README.md) - Trading tools and utilities
- [Concurrency Reference](docs/reference/concurrency/README.md) - Concurrency analysis
- [Strategies Reference](docs/reference/strategies/README.md) - Strategy implementations
- [Data Organization](docs/reference/DATA_ORGANIZATION.md) - Data directory structure
- [Data Refresh](docs/reference/data_refresh.md) - Data refresh procedures
- [TradingView Integration](docs/reference/TRADINGVIEW_INTEGRATION.md) - TradingView setup

### Performance

- [Performance Optimization](docs/PERFORMANCE_OPTIMIZATION_GUIDE.md) - System optimization
- [Memory Optimization](docs/memory_optimization_examples.md) - Memory techniques
- [Optimization Summary](docs/performance/optimization_summary.md) - Historical optimizations

### Troubleshooting

- [Common Issues](docs/troubleshooting/COMMON_ISSUES.md) - FAQ and solutions

### Specialized Documentation

- [SBC Research](docs/research/sbc/) - DeFi protocol research papers
- [AI Prompts](docs/ai/prompts/) - AI assistant prompt templates
- [Implementation Logs Archive](docs/archive/implementation-logs/README.md) - Historical session summaries

---

## Quick Start by Use Case

### I want to analyze trading strategies

→ [Quick Start Guide](docs/getting-started/QUICK_START.md) → Path B (CLI Only)

### I want to use the REST API

→ [Quick Start Guide](docs/getting-started/QUICK_START.md) → Path A (Full Stack)
→ Or see: [API Getting Started](docs/api/GETTING_STARTED.md)

### I want to develop new features

→ [Development Guide](docs/development/DEVELOPMENT_GUIDE.md)

### I want to understand the architecture

→ [System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)

### I want to improve code quality

→ Run: `make quality-analyze`
→ Read: [Code Quality](docs/development/CODE_QUALITY.md)

---

## Recent Updates

### October 2025 - Sweep Results API & Database Normalization

- ✅ Database normalization (tickers, strategy types)
- ✅ 19 analytical database views
- ✅ Sweep Results API (5 new endpoints)
- ✅ 42+ tests with comprehensive coverage
- ✅ 2,000+ lines of documentation

See [CHANGELOG.md](docs/CHANGELOG.md) for complete history.

---

## Project Components

### Command-Line Interface (CLI)

- **Status**: Production ready
- **Commands**: 47+ across 9 groups
- **Entry**: `trading-cli`

### REST API

- **Status**: Operational
- **Endpoints**: 38 working endpoints (33 original + 5 sweep results)
- **URL**: http://localhost:8000
- **Docs**: http://localhost:8000/api/docs

### Database

- **Status**: Production ready
- **Tables**: 10 (normalized schema)
- **Views**: 19 analytical views
- **Records**: 4,855 sweep results
- **Migrations**: 7 (all applied)

### Core Systems

- Strategy analysis (SMA, EMA, MACD, RSI)
- Portfolio management and optimization
- Statistical Performance Divergence System (SPDS)
- Concurrency and correlation analysis
- Seasonality analysis
- Trade history tracking

---

**Last Updated**: October 28, 2025
**Version**: 1.0.0
**Status**: Operational (CLI + API)
