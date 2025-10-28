# Trading CLI API

FastAPI wrapper for the trading-cli application providing async job execution, SSE streaming, and API key authentication.

## Architecture

### Completed Components

#### Phase 1: Core Infrastructure ✅

- **Directory Structure**: Complete API directory structure created
- **Configuration** (`core/config.py`): API settings with environment variable support
- **Security** (`core/security.py`): API key generation, hashing, and validation
- **Database** (`core/database.py`): SQLAlchemy async session management
- **Redis** (`core/redis.py`): Redis connection pooling for caching and queues
- **Models**:
  - `models/auth.py`: APIKeyModel for authentication
  - `models/jobs.py`: JobModel and Pydantic schemas
  - `models/base.py`: Base response models
- **Migration**: Alembic migration for api_keys and jobs tables
- **Health Endpoints** (`routers/health.py`): Basic, detailed, readiness, and liveness checks
- **Main App** (`main.py`): FastAPI application with CORS, exception handlers, and lifecycle management

#### Phase 2: Job Queue System ✅

- **Progress Tracking** (`jobs/progress.py`): Redis-based progress tracking with ProgressTracker class
- **ARQ Worker** (`jobs/worker.py`): Worker configuration with startup/shutdown hooks

#### Phase 3: Service Layer ✅

- **Base Service** (`services/base.py`): BaseCommandService with common execution logic

### In Progress / TODO

#### Phase 2: Task Definitions

- `jobs/tasks.py`: Task wrappers for all 47+ subcommands (TO BE IMPLEMENTED)

#### Phase 3: Command Services

Create service files in `services/command_services/`:

- `strategy_service.py` - 4 subcommands
- `portfolio_service.py` - 5 subcommands
- `spds_service.py` - 7 subcommands
- `trade_history_service.py` - 6 subcommands
- `config_service.py` - 6 subcommands
- `tools_service.py` - 6 subcommands
- `concurrency_service.py` - 8 subcommands
- `positions_service.py` - 5 subcommands
- `seasonality_service.py` - 6 subcommands

#### Phase 4: API Routers

Create router files in `routers/`:

- `jobs.py` - Job management (create, status, stream, cancel, list)
- `strategy.py` - Strategy commands (run, sweep, review, sector-compare)
- `portfolio.py` - Portfolio commands (update, process, aggregate, synthesize, review)
- `spds.py` - SPDS commands (analyze, export, demo, health, configure, list-portfolios, interactive)
- `trade_history.py` - Trade history commands (close, add, update, list, validate, health)
- `config.py` - Config commands (list, show, verify-defaults, set-default, edit, validate)
- `tools.py` - Tools commands (schema, health, validate, export-ma-data, export-ma-data-sweep, pinescript)
- `concurrency.py` - Concurrency commands (analyze, export, review, construct, optimize, monte-carlo, health, demo)
- `positions.py` - Position commands (list, equity, validate, validate-equity, info)
- `seasonality.py` - Seasonality commands (run, list, results, clean, current, portfolio)

#### Phase 5: SSE Streaming

- `streaming/sse.py`: Server-Sent Events implementation for progress streaming

#### Phase 6: Request Models

Create request model files in `models/requests/`:

- `strategy.py` - StrategyRunRequest, StrategySweepRequest, etc.
- `portfolio.py` - PortfolioUpdateRequest, etc.
- `spds.py` - SPDSAnalyzeRequest, etc.
- `trade_history.py` - TradeHistoryCloseRequest, etc.
- `config.py` - ConfigRequest models
- `tools.py` - ToolsRequest models
- `concurrency.py` - ConcurrencyRequest models
- `positions.py` - PositionsRequest models
- `seasonality.py` - SeasonalityRequest models

#### Phase 7: Middleware

- `middleware/auth.py`: API key authentication middleware
- `middleware/rate_limit.py`: Redis-based rate limiting
- `middleware/logging.py`: Request/response logging

#### Phase 8-10: Deployment & Testing

- Integration tests
- Docker configuration updates
- Startup scripts
- Documentation enhancements

## Quick Start

### Prerequisites

```bash
# Install dependencies (already in pyproject.toml)
poetry install

# Set environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Database Setup

```bash
# Run migrations
alembic upgrade head

# Create a development API key (TODO: create management script)
# For now, use the dev key: dev-key-000000000000000000000000
```

### Running the API

```bash
# Development mode
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main module
python -m app.api.main
```

### Running the ARQ Worker

```bash
# Start ARQ worker (once tasks are implemented)
arq app.api.jobs.worker.WorkerSettings
```

### Testing the API

```bash
# Health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed

# API documentation
open http://localhost:8000/api/docs
```

## Implementation Patterns

### Command Service Pattern

Each command service should follow this pattern:

```python
from ..services.base import BaseCommandService
from ..jobs.progress import ProgressTracker

class CommandService(BaseCommandService):
    async def execute_subcommand(self, params: RequestModel) -> dict:
        """Execute specific subcommand."""
        # Update progress
        await self.update_progress(10, "Initializing...")

        # Build CLI command
        command = self._build_cli_command(params)

        # Execute
        await self.update_progress(50, "Executing command...")
        result = await self.execute_cli_command(command)

        # Process result
        await self.update_progress(90, "Processing results...")
        processed = self._process_result(result)

        # Complete
        await self.update_progress(100, "Complete")
        return processed
```

### Router Pattern

Each router should follow this pattern:

```python
from fastapi import APIRouter, Depends, BackgroundTasks
from ..core.security import require_scope
from ..models.jobs import JobResponse
from ..services.job_service import JobService

router = APIRouter()

@router.post("/subcommand", response_model=JobResponse)
async def subcommand(
    request: SubcommandRequest,
    background_tasks: BackgroundTasks,
    api_key = Depends(require_scope("command_group"))
):
    """Execute subcommand."""
    # Create job
    job = await JobService.create_job(
        api_key_id=api_key.id,
        command_group="group_name",
        command_name="subcommand",
        parameters=request.model_dump()
    )

    # Enqueue to ARQ
    await queue_job(job.id, request)

    return JobResponse(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        stream_url=f"/api/v1/jobs/{job.id}/stream",
        status_url=f"/api/v1/jobs/{job.id}"
    )
```

## Environment Variables

```bash
# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME="Trading CLI API"
VERSION=1.0.0

# Security
API_KEY_HEADER=X-API-Key
API_KEY_SECRET=your-secret-key-change-in-production

# Redis
REDIS_URL=redis://localhost:6379
ARQ_QUEUE_NAME=trading_jobs

# Database
DATABASE_URL=postgresql://trading_user:trading_password@localhost:5432/trading_db

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

## Next Steps

1. Implement `jobs/tasks.py` with all task wrappers
2. Implement `services/job_service.py` for job management
3. Implement `streaming/sse.py` for progress streaming
4. Implement `routers/jobs.py` for job management endpoints
5. Implement command services (start with strategy as example)
6. Implement routers (start with strategy as example)
7. Implement request models
8. Add middleware
9. Write tests
10. Update deployment configuration

## Dependencies

Required packages (already in pyproject.toml):

- fastapi
- uvicorn
- pydantic
- pydantic-settings
- sqlalchemy
- asyncpg
- alembic
- redis
- arq
- bcrypt

## API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json
