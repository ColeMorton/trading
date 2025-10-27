# Logging Migration Notes

## Overview

This document describes the breaking changes in the new logging system and provides migration guidance.

## Breaking Changes

### 1. Logger Creation

**OLD:**

```python
import logging
logger = logging.getLogger(__name__)
```

**NEW:**

```python
from app.core.logging_factory import get_logger
logger = get_logger(__name__)
```

**Find and Replace:**

```bash
# Find all old logger creation
grep -r "logging.getLogger(__name__)" app/

# Pattern to replace
# OLD: logger = logging.getLogger(__name__)
# NEW:
# from app.core.logging_factory import get_logger
# logger = get_logger(__name__)
```

### 2. setup_logging() Removed

**OLD:**

```python
from app.tools.setup_logging import setup_logging

log, log_close, logger, handler = setup_logging('module', 'file.log')
log("Message")
log_close()
```

**NEW:**

```python
from app.core.logging_factory import get_logger

logger = get_logger(__name__)
logger.info("message")
# No need to close - automatic cleanup
```

### 3. structured_logging Module Removed

**OLD:**

```python
from app.tools.structured_logging import get_logger

logger = get_logger('module')
logger.info("message", context={"key": "value"})
```

**NEW:**

```python
from app.core.logging_factory import get_logger

logger = get_logger(__name__)
logger.info("message", key="value")
```

### 4. String Formatting Changed

**OLD:**

```python
logger.info(f"Processing {ticker} with {count} params")
logger.info("Processing {} with {} params".format(ticker, count))
logger.info("Processing %s with %d params" % (ticker, count))
```

**NEW:**

```python
logger.info("processing_ticker", ticker=ticker, param_count=count)
```

### 5. Console Logging Separated

**OLD:**

```python
from app.tools.console_logging import ConsoleLogger

console = ConsoleLogger()
console.success("Task completed")  # Also wrote to log file
```

**NEW:**

```python
from app.ui.console_display import ConsoleDisplay
from app.core.logging_factory import get_logger

console = ConsoleDisplay()  # Only displays
logger = get_logger(__name__)  # Only logs

console.show_success("Task completed")  # User display
logger.info("task_completed", task_id=123)  # Audit log
```

### 6. Context Management Changed

**OLD:**

```python
from app.tools.console_logging import console_logging_context

with console_logging_context('module', 'file.log') as (log, console):
    log("Message")
    console.info("Display message")
```

**NEW:**

```python
from app.core.logging_factory import get_logger, bind_context, clear_context
from app.ui.console_display import ConsoleDisplay

logger = get_logger(__name__)
console = ConsoleDisplay()

bind_context(operation_id="123")
logger.info("processing")  # Includes operation_id
clear_context()
```

## Migration Steps

### Step 1: Update Imports

Replace all logging imports with new factory:

```bash
# Find files with old imports
grep -r "from app.tools.setup_logging import" app/
grep -r "from app.tools.structured_logging import" app/
grep -r "import logging" app/ | grep "getLogger"

# Manual replacement needed for each file
```

### Step 2: Update Logger Creation

For each file with `logger = logging.getLogger(__name__)`:

```python
# OLD
import logging
logger = logging.getLogger(__name__)

# NEW
from app.core.logging_factory import get_logger
logger = get_logger(__name__)
```

### Step 3: Convert Log Calls

Convert string-formatted logs to structured format:

```python
# OLD
logger.info(f"Processing {ticker} with {count} parameters")

# NEW
logger.info("processing_ticker", ticker=ticker, param_count=count)
```

**Pattern Matching:**

- Look for `f"` strings in logger calls
- Look for `.format()` in logger calls
- Look for `%` formatting in logger calls

### Step 4: Update Exception Logging

```python
# OLD
try:
    do_something()
except Exception as e:
    logger.error(f"Failed: {str(e)}")

# NEW
try:
    do_something()
except Exception as e:
    logger.error("operation_failed", error=str(e), exc_info=True)
```

### Step 5: Separate Console and Logging

For files using `ConsoleLogger`:

```python
# OLD
from app.tools.console_logging import ConsoleLogger
console = ConsoleLogger()
console.success("Done")
console.info("Processing...")

# NEW
from app.ui.console_display import ConsoleDisplay
from app.core.logging_factory import get_logger

console = ConsoleDisplay()
logger = get_logger(__name__)

console.show_success("Done")
logger.info("task_completed")
```

### Step 6: Update Service Classes

Add logger and console to service **init**:

```python
# OLD
class StrategyService:
    def __init__(self):
        from app.tools.console_logging import ConsoleLogger
        self.console = ConsoleLogger()

# NEW
from app.core.logging_factory import get_logger
from app.ui.console_display import ConsoleDisplay

class StrategyService:
    def __init__(
        self,
        logger = None,
        console = None
    ):
        self.logger = logger or get_logger(__name__)
        self.console = console or ConsoleDisplay()
```

## File-by-File Migration Checklist

### High Priority Files

Files with most logging calls that should be migrated first:

1. ✅ `app/api/main.py` - API startup (COMPLETED)
2. ⏳ `app/cli/commands/strategy.py` - 177 print statements
3. ⏳ `app/cli/commands/concurrency.py` - 210 instances
4. ⏳ `app/cli/main.py` - 46 instances
5. ⏳ `app/cli/services/strategy_services.py`
6. ⏳ `app/cli/services/strategy_dispatcher.py`
7. ⏳ `app/api/services/command_services/*.py`

### Logger Creation Files

Files with `logging.getLogger()` (90 files total):

- `app/api/services/*.py`
- `app/database/*.py`
- `app/tools/**/*.py`
- `app/contexts/**/*.py`
- `app/strategies/**/*.py`

## Testing After Migration

### 1. Verify Logger Creation

```python
# Test script
from app.core.logging_factory import get_logger

logger = get_logger("test")
logger.info("test_event", key="value")
print("If you see this, logging works!")
```

### 2. Verify Log Output

```bash
# Run application
trading-cli status

# Check logs were created
ls -la logs/
cat logs/app.log
```

### 3. Verify Structured Format

```bash
# Check JSON logs are properly formatted
cat logs/app.json | jq '.'

# Should see structured output:
# {
#   "event": "api_starting",
#   "timestamp": "2025-10-25T14:30:00Z",
#   "level": "info",
#   ...
# }
```

### 4. Verify Console Display

```bash
# Run a command and verify output still looks good
trading-cli strategy run --help

# Should see nice Rich-formatted output
```

## Common Issues

### Import Errors

**Error:** `ImportError: cannot import name 'get_logger' from 'app.core.logging_factory'`

**Solution:** Ensure structlog is installed:

```bash
poetry install
# or
pip install structlog python-json-logger
```

### Missing Logger Context

**Error:** Logs don't include expected context

**Solution:** Ensure context is bound before logging:

```python
from app.core.logging_factory import bind_context

bind_context(request_id="123")
logger.info("event")  # Now includes request_id
```

### Console Output Not Showing

**Error:** Console output is blank

**Solution:** Make sure you're using ConsoleDisplay, not logger:

```python
from app.ui.console_display import ConsoleDisplay

console = ConsoleDisplay()
console.show_info("This will display")  # User-facing
logger.info("this_will_log")  # Log file only
```

### Performance Issues

**Error:** Logging is slow

**Solution:**

1. Check if expensive operations are in log calls
2. Use lazy evaluation for expensive formatting
3. Consider log sampling in tight loops

```python
# BAD - Always evaluated
logger.debug("data", value=expensive_function())

# GOOD - Only evaluated if DEBUG enabled
logger.debug("data", value=lambda: expensive_function())
```

## Rollback Plan

If the new logging system causes issues:

1. **Revert key files**: Restore old logger creation in critical paths
2. **Keep factory available**: New and old systems can coexist temporarily
3. **Gradual migration**: Don't migrate everything at once

```python
# Temporary coexistence
import logging
from app.core.logging_factory import get_logger

# Use old system for now
old_logger = logging.getLogger(__name__)

# Use new system where tested
new_logger = get_logger(__name__)
```

## Console Output Issues and Solutions

### Problem: Double Timestamps

**Symptom:**

```
2025-10-27T00:03:18.119154Z [info] 2025-10-27T00:03:18.119054Z [info] Strategy type...
```

**Cause:** Both structlog and stdlib logging are processing the same log entry.

**Solution:** Use `NullHandler` in development to prevent stdlib from outputting:

```python
# In configure_stdlib_logging()
if not should_use_json_logs():
    root_logger.addHandler(logging.NullHandler())
```

### Problem: Verbose Metadata on Every Line

**Symptom:**

```
[info] concurrency_analysis_started [app.cli.commands.concurrency] filename=concurrency.py func_name=analyze lineno=320
```

**Cause:** `CallsiteParameterAdder` is enabled for console output.

**Solution:** Only enable `CallsiteParameterAdder` for production/JSON logs:

```python
if should_use_json_logs():
    # Production: Include metadata
    processors.append(structlog.processors.CallsiteParameterAdder({
        structlog.processors.CallsiteParameter.FILENAME,
        structlog.processors.CallsiteParameter.FUNC_NAME,
        structlog.processors.CallsiteParameter.LINENO,
    }))
else:
    # Development: Skip metadata for clean output
    pass
```

### Problem: Console Data Dumps

**Symptom:** Thousands of lines of Plotly JSON, date arrays, or HTML dumped to console.

**Cause:** Calling `fig.show()` or logging large data structures.

**Solution:** Save visualizations to files:

```python
# Instead of fig.show()
output_path = Path("data/outputs") / f"{name}_visualization.html"
fig.write_html(str(output_path))
logger.info("visualization_saved", path=str(output_path))
```

## Common Migration Pitfalls

### Pitfall: Logger Type Mismatch

**Error:**

```
TypeError: 'BoundLoggerLazyProxy' object is not callable
```

**Cause:** New logger object passed to function expecting old callable pattern:

```python
# Function expects old pattern
def process_data(log):
    log("Processing started", "info")  # Old: callable function

# But receives new logger object
logger = get_logger(__name__)
process_data(logger)  # Error: logger is object, not callable
```

**Solution:** Update function to use new logger methods:

```python
def process_data(logger):
    logger.info("processing_started")  # New: logger object
```

**Quick Fix (Temporary):** Create adapter wrapper:

```python
def log_adapter(message: str, level: str = "info"):
    """Temporary adapter for old-style log calls."""
    if level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    else:
        logger.info(message)

# Pass adapter to old-style functions
process_data(log_adapter)
```

### Pitfall: Parameter Order Issues

**Error:**

```
TypeError: log_func() got multiple values for argument 'level'
```

**Cause:** Old signature `(level, message)` vs new signature `(message, level)`.

**Solution:** Update function signatures consistently:

```python
# OLD
def log_func(level: str, message: str) -> None:
    ...

# NEW
def log_func(message: str, level: str = "info") -> None:
    ...
```

### Pitfall: Decorator Reraise Behavior

**Error:**

```
TypeError: cannot unpack non-iterable bool object
```

**Cause:** Error decorator returning `False` instead of raising exception:

```python
@handle_errors(..., reraise=False)  # Returns False on error
def calculate_risk():
    result = some_function()
    return result  # If error, decorator returns False

# Later code tries to unpack:
risk, contribution = calculate_risk()  # Error: can't unpack False
```

**Solution:** Set `reraise=True` to propagate exceptions:

```python
@handle_errors(..., reraise=True)  # Raises exception on error
def calculate_risk():
    ...
```

## Migration Tools

### Automated Migration Script

**Location:** `scripts/migrate_logging.py`

**Usage:**

```bash
# Migrate specific directory
python scripts/migrate_logging.py --target-dir app/concurrency

# Migrate specific file
python scripts/migrate_logging.py --file app/tools/portfolio/loader.py

# Dry run (preview changes)
python scripts/migrate_logging.py --dry-run --target-dir app/tools

# Migrate entire app
python scripts/migrate_logging.py --all
```

**What It Migrates:**

1. Import statements:

   - `from app.tools.setup_logging import setup_logging` → `from app.core.logging_factory import get_logger`
   - `import logging; logging.getLogger()` → `from app.core.logging_factory import get_logger`

2. Function signatures:

   - `log: Callable[[str, str], None]` → `logger`
   - `log_func: Callable` → `logger`

3. Call patterns:

   - `log("message", "info")` → `logger.info("message")`
   - `log("error occurred", "error")` → `logger.error("error occurred")`

4. Variable renames:

   - `log` → `logger`
   - `log_func` → `logger`

5. Cleanup:
   - Removes `log_close()` calls
   - Removes unused `setup_logging` imports

**Limitations:**

- May place imports incorrectly (inside docstrings)
- Doesn't handle complex context managers
- Requires manual review of changes
- Best for leaf nodes (files with no complex dependencies)

### Multiline Logger Call Fixer

**Location:** `scripts/fix_multiline_logger_calls.py`

Specialized script for fixing multiline logger calls that span multiple lines.

**When to Use:** After automated migration when you see syntax errors from multiline calls.

## Support

For questions or issues:

1. Check examples in this document
2. See [LOGGING_GUIDE.md](./LOGGING_GUIDE.md) for usage patterns
3. Review existing migrated files as examples
4. Ask team for help with complex migrations

## Progress Tracking

Track migration progress:

```bash
# Count files with old logging
grep -r "logging.getLogger(__name__)" app/ | wc -l

# Count files with new logging
grep -r "from app.core.logging_factory import get_logger" app/ | wc -l

# Files still using print()
grep -r "print(" app/ --include="*.py" | wc -l
```

Target: 0 old patterns, all files using new system.
