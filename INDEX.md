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

### API Documentation

- [API README](docs/api/README.md) - Complete API documentation
- [API Getting Started](docs/api/GETTING_STARTED.md) - API setup guide

### Development

- [Development Guide](docs/development/DEVELOPMENT_GUIDE.md) - Dev environment
- [Code Quality](docs/development/CODE_QUALITY.md) - Linting and formatting
- [Code Quality Improvement](docs/development/CODE_QUALITY_IMPROVEMENT.md) - Gradual improvement
- [SSH Guide](docs/development/SSH_GUIDE.md) - Remote development
- [AI Assistant Guide](docs/development/AI_ASSISTANT_GUIDE.md) - Using Claude/AI

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

### Reference

- [Command Reference](docs/reference/COMMAND_REFERENCE.md) - All CLI commands
- [Configuration Guide](docs/CONFIGURATION_GUIDE.md) - Configuration options
- [CSV Schemas](docs/csv_schemas.md) - Data format reference

### Performance

- [Performance Optimization](docs/PERFORMANCE_OPTIMIZATION_GUIDE.md) - System optimization
- [Memory Optimization](docs/memory_optimization_examples.md) - Memory techniques

### Troubleshooting

- [Common Issues](docs/troubleshooting/COMMON_ISSUES.md) - FAQ and solutions

### Specialized Documentation

- [SBC Research](docs/research/sbc/) - DeFi protocol research papers
- [AI Prompts](docs/ai/prompts/) - AI assistant prompt templates

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

## Project Components

### Command-Line Interface (CLI)

- **Status**: Production ready
- **Commands**: 47+ across 9 groups
- **Entry**: `trading-cli`

### REST API

- **Status**: Operational
- **Endpoints**: 33 working endpoints
- **URL**: http://localhost:8000
- **Docs**: http://localhost:8000/api/docs

### Core Systems

- Strategy analysis (SMA, EMA, MACD, RSI)
- Portfolio management and optimization
- Statistical Performance Divergence System (SPDS)
- Concurrency and correlation analysis
- Seasonality analysis
- Trade history tracking

---

**Last Updated**: October 19, 2025
**Version**: 1.0.0
**Status**: Operational (CLI + API)
