# Logging Guide

## Overview

The trading-cli uses a unified logging system based on **structlog** for structured, searchable logs with consistent formatting across all components.

## Quick Start

### Basic Usage

```python
from app.core.logging_factory import get_logger

# Get a logger
logger = get_logger(__name__)

# Log events with structured data
logger.info("user_login", user_id="12345", ip="192.168.1.1")
logger.warning("api_rate_limit_approaching", usage=95, limit=100)
logger.error("database_connection_failed", error=str(e), retry_count=3)
```

### With Context Binding

```python
from app.core.logging_factory import get_logger, bind_context, clear_context

logger = get_logger(__name__)

# Bind context for all subsequent logs
bind_context(request_id="abc123", user_id="user456")

logger.info("processing_request")  # Automatically includes request_id and user_id
logger.info("validating_input")     # Also includes context
logger.info("request_completed")    # Also includes context

# Clear context when done
clear_context()
```

## Log Levels

Use appropriate log levels:

- **DEBUG**: Detailed diagnostic information (disabled in production)
- **INFO**: General informational messages about application flow
- **WARNING**: Warning messages for recoverable issues
- **ERROR**: Error messages for failures that don't stop the application
- **CRITICAL**: Critical errors that may cause application failure

## Structured Logging Best Practices

### DO: Use Structured Data

```python
# GOOD - Structured, searchable
logger.info("order_placed",
    order_id="12345",
    symbol="AAPL",
    quantity=100,
    price=150.25
)
```

### DON'T: Use String Formatting

```python
# BAD - Unstructured, hard to search
logger.info(f"Order {order_id} placed for {quantity} shares of {symbol} at ${price}")
```

### Event Names

Use snake_case event names that describe what happened:

```python
# GOOD
logger.info("strategy_execution_started")
logger.info("parameter_sweep_completed")
logger.info("data_download_failed")

# BAD
logger.info("Starting strategy")
logger.info("Done")
logger.info("Failed!")
```

### Including Context

Always include relevant context as keyword arguments:

```python
logger.info("strategy_execution_completed",
    ticker="AAPL",
    strategy="ma_cross",
    duration_ms=1234,
    portfolios_generated=50,
    success=True
)
```

## Logger Names

Always use `__name__` as the logger name:

```python
logger = get_logger(__name__)
```

This creates a hierarchical logger namespace:

- `app.cli.commands.strategy`
- `app.api.services.strategy_service`
- `app.tools.portfolio_analyzer`

## Error Logging

When logging exceptions, include exception info:

```python
try:
    process_data()
except Exception as e:
    logger.error("data_processing_failed",
        error=str(e),
        error_type=type(e).__name__,
        exc_info=True  # Includes full traceback
    )
    raise
```

## Performance Considerations

### Expensive Operations

For expensive operations (like formatting large objects), use lazy evaluation:

```python
# GOOD - Only evaluated if log level is DEBUG
logger.debug("data_state", data=lambda: expensive_format(data))

# BAD - Always evaluated even if DEBUG is disabled
logger.debug("data_state", data=expensive_format(data))
```

### High-Frequency Logs

For logs in tight loops, consider:

1. Using DEBUG level (disabled in production)
2. Sampling (log every Nth iteration)
3. Aggregating data before logging

```python
# Sample logging in loop
for i, item in enumerate(items):
    if i % 100 == 0:  # Log every 100 items
        logger.debug("processing_progress", processed=i, total=len(items))
```

## Environment Configuration

Configure logging via environment variables:

```bash
# Log level
export LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Environment
export ENVIRONMENT=production  # development, production

# JSON logs (for production)
export JSON_LOGS=true

# Docker container flag
export DOCKER_CONTAINER=true
```

## Output Formats

### Development (Console)

Pretty-printed, colored output:

```
2025-10-25 14:30:00 [info     ] user_login                    user_id=12345 ip=192.168.1.1
2025-10-25 14:30:01 [warning  ] api_rate_limit_approaching   usage=95 limit=100
2025-10-25 14:30:02 [error    ] database_connection_failed   error=Connection timeout retry_count=3
```

### Production (JSON)

Machine-readable JSON:

```json
{
  "event": "user_login",
  "user_id": "12345",
  "ip": "192.168.1.1",
  "timestamp": "2025-10-25T14:30:00.123456Z",
  "level": "info",
  "logger": "app.api.auth"
}
```

## Integration with Services

### In Service Classes

```python
from app.core.logging_factory import get_logger

class StrategyService:
    def __init__(self):
        self.logger = get_logger(__name__)

    def execute(self, ticker: str, params: dict):
        self.logger.info("strategy_execution_started",
            ticker=ticker,
            params=params
        )

        try:
            result = self._execute_strategy(ticker, params)
            self.logger.info("strategy_execution_completed",
                ticker=ticker,
                success=True,
                portfolios=len(result)
            )
            return result
        except Exception as e:
            self.logger.error("strategy_execution_failed",
                ticker=ticker,
                error=str(e),
                exc_info=True
            )
            raise
```

### In API Routes

```python
from app.core.logging_factory import get_logger, bind_context, clear_context

router = APIRouter()
logger = get_logger(__name__)

@router.post("/strategy/execute")
async def execute_strategy(request: StrategyRequest):
    # Bind request context
    bind_context(
        request_id=str(uuid.uuid4()),
        endpoint="/strategy/execute",
        ticker=request.ticker
    )

    try:
        logger.info("api_request_received")
        result = await service.execute(request)
        logger.info("api_request_completed", status="success")
        return result
    except Exception as e:
        logger.error("api_request_failed", error=str(e), exc_info=True)
        raise
    finally:
        # Clean up context
        clear_context()
```

## Log File Locations

### Development

```
/path/to/project/logs/
├── app.log         # General application logs
├── app.json        # JSON-formatted logs
└── error.log       # Error-level logs only
```

### Docker/Production

```
/app/logs/
├── app.log
├── app.json
└── error.log
```

## Searching and Filtering Logs

### JSON Logs with jq

```bash
# Find all errors
cat logs/app.json | jq 'select(.level == "error")'

# Find logs for specific ticker
cat logs/app.json | jq 'select(.ticker == "AAPL")'

# Find slow operations
cat logs/app.json | jq 'select(.duration_ms > 5000)'

# Get all events of a type
cat logs/app.json | jq 'select(.event == "strategy_execution_completed")'
```

### Text Logs with grep

```bash
# Find all errors
grep "ERROR" logs/app.log

# Find logs for specific module
grep "app.cli.commands.strategy" logs/app.log

# Find logs with specific context
grep "ticker=AAPL" logs/app.log
```

## Debugging

### Enable Debug Logging

Temporarily enable debug logging for specific modules:

```python
import logging

# Enable debug for specific module
logging.getLogger("app.cli.commands.strategy").setLevel(logging.DEBUG)

# Enable debug for all app modules
logging.getLogger("app").setLevel(logging.DEBUG)
```

### Trace Complex Operations

```python
logger.debug("operation_started", operation="complex_calculation")

# ... complex code ...

logger.debug("operation_step_1_completed", intermediate_result=result1)

# ... more code ...

logger.debug("operation_completed", final_result=result)
```

## Common Patterns

### Transaction/Operation Tracking

```python
import time

operation_id = str(uuid.uuid4())
start_time = time.time()

logger.info("operation_started",
    operation_id=operation_id,
    operation="strategy_analysis"
)

try:
    result = perform_operation()
    duration = (time.time() - start_time) * 1000

    logger.info("operation_completed",
        operation_id=operation_id,
        duration_ms=duration,
        success=True
    )
except Exception as e:
    duration = (time.time() - start_time) * 1000

    logger.error("operation_failed",
        operation_id=operation_id,
        duration_ms=duration,
        error=str(e),
        exc_info=True
    )
    raise
```

### Progress Tracking

```python
total = len(items)
logger.info("batch_processing_started", total=total)

for i, item in enumerate(items):
    if i % 10 == 0:  # Log every 10 items
        progress = (i / total) * 100
        logger.info("batch_processing_progress",
            processed=i,
            total=total,
            progress_percent=progress
        )

logger.info("batch_processing_completed", total=total)
```

## Console vs Production Configuration

The logging system uses different configurations for development (console) and production (JSON logs) to balance readability and structured logging.

### Development Console Configuration

Clean, readable output for local development:

```python
# In app/core/structlog_config.py
if not should_use_json_logs():
    processors = [
        filter_by_level,
        *shared_processors,
        structlog.contextvars.merge_contextvars,
        # NO CallsiteParameterAdder - keeps console clean
        structlog.dev.ConsoleRenderer(
            colors=sys.stderr.isatty(),
            exception_formatter=structlog.dev.plain_traceback,
        ),
    ]
```

**Benefits:**

- No verbose metadata (filename, function, line number)
- Single timestamp per log line
- Color-coded output for readability
- Fast visual scanning

### Production Configuration

Structured JSON logs for machine parsing:

```python
# Production: Full metadata
if should_use_json_logs():
    processors = [
        filter_by_level,
        *shared_processors,
        structlog.contextvars.merge_contextvars,
        structlog.processors.CallsiteParameterAdder({
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.FUNC_NAME,
            structlog.processors.CallsiteParameter.LINENO,
        }),
        JSONRenderer(),
    ]
```

**Benefits:**

- Full metadata for debugging
- Searchable structured format
- Log aggregation friendly
- Audit trail complete

### Preventing Double Logging

Use `NullHandler` in development to prevent stdlib logging from duplicating output:

```python
# In configure_stdlib_logging()
if not should_use_json_logs():
    # Development: NullHandler prevents double output
    root_logger.addHandler(logging.NullHandler())
else:
    # Production: Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    root_logger.addHandler(console_handler)
```

## Handling Large Data and Visualizations

Avoid dumping large data structures to the console by saving to files instead.

### Pattern: Save Visualization to File

Instead of displaying visualizations directly (which dumps thousands of lines):

```python
# BAD: Dumps entire Plotly object to console
fig.show()

# GOOD: Save to HTML file
def save_visualization(fig: go.Figure, config: dict, logger) -> Path:
    """Save Plotly figure to HTML file instead of displaying."""
    try:
        portfolio_name = Path(config["PORTFOLIO"]).stem
        output_dir = Path("data/outputs/concurrency")
        output_dir.mkdir(parents=True, exist_ok=True)

        html_path = output_dir / f"{portfolio_name}_visualization.html"
        fig.write_html(str(html_path))

        logger.info("visualization_saved", path=str(html_path))
        return html_path

    except Exception as e:
        logger.error("visualization_save_failed", error=str(e), exc_info=True)
        raise
```

### Pattern: Summarize Large Data

Instead of logging full datasets, log summaries:

```python
# BAD: Logs entire DataFrame
logger.debug("dataframe_state", df=df.to_dict())

# GOOD: Log summary statistics
logger.debug("dataframe_state",
    rows=len(df),
    columns=list(df.columns),
    memory_mb=df.memory_usage(deep=True).sum() / 1024**2
)
```

## Migration Script Usage

For large-scale logging system migrations, use the automated migration script.

### Using migrate_logging.py

```bash
# Migrate specific directory
python scripts/migrate_logging.py --target-dir app/concurrency

# Migrate specific file
python scripts/migrate_logging.py --file app/tools/portfolio/loader.py

# Migrate entire app/ directory
python scripts/migrate_logging.py --all

# Dry run to preview changes
python scripts/migrate_logging.py --dry-run --all
```

### What the Script Migrates

The script automatically handles:

1. **Import updates**: `setup_logging` → `get_logger`
2. **Function signatures**: `log: Callable` → `logger`
3. **Call patterns**: `log("msg", "info")` → `logger.info("msg")`
4. **Type hints**: `logger | None = None` → `logger=None`
5. **Cleanup**: Removes `log_close()` calls

### When to Use Manual Migration

Use manual migration for:

- Files with complex context patterns
- Classes with custom logger initialization
- Code requiring significant refactoring
- Entry point files with special setup

See [MIGRATION_NOTES.md](./MIGRATION_NOTES.md) for manual migration instructions.

## Migration from Old System

If you're migrating from the old logging system:

### Old Way

```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Processing {ticker} with {count} parameters")
```

### New Way

```python
from app.core.logging_factory import get_logger

logger = get_logger(__name__)

logger.info("processing_ticker", ticker=ticker, param_count=count)
```

See [MIGRATION_NOTES.md](./MIGRATION_NOTES.md) for detailed migration instructions.
