# Configuration Guide - Equity Data Export

## Overview

The Equity Data Export feature provides configuration options to control the export of detailed equity curve data during strategy processing. This guide explains all configuration options, validation rules, and best practices.

## Configuration Schema

### EQUITY_DATA Section

The `EQUITY_DATA` configuration section controls equity data export functionality:

```python
"EQUITY_DATA": {
    "EXPORT": bool,      # Enable/disable equity data export
    "METRIC": str        # Backtest metric selection
}
```

## Configuration Properties

### EXPORT (Boolean)

Controls whether equity data export is enabled.

**Valid Values:**

- `True` / `true` / `"true"` / `"1"` / `"yes"` / `"on"` - Enable export
- `False` / `false` / `"false"` / `"0"` / `"no"` / `"off"` - Disable export

**Default:** `False` (disabled for backwards compatibility)

**Examples:**

```python
# Enable export
"EXPORT": True

# Enable export with string
"EXPORT": "yes"

# Disable export
"EXPORT": False
```

### METRIC (String)

Selects which backtest result to use when multiple backtests exist.

**Valid Values:**

- `"mean"` - Average performance across all backtests
- `"median"` - Median performance across all backtests
- `"best"` - Best performing backtest
- `"worst"` - Worst performing backtest

**Default:** `"mean"`

**Case Sensitivity:** Values are case-insensitive (`"MEAN"`, `"Mean"`, `"mean"` are all valid)

**Examples:**

```python
# Use mean performance
"METRIC": "mean"

# Use best performance
"METRIC": "best"

# Case insensitive
"METRIC": "MEDIAN"
```

## Configuration Examples

### Complete Configuration

```python
config = {
    "EQUITY_DATA": {
        "EXPORT": True,
        "METRIC": "mean"
    },
    # Other configuration sections...
    "USE_EXTENDED_SCHEMA": True,
    "REFRESH": True
}
```

### Disabled Export

```python
config = {
    "EQUITY_DATA": {
        "EXPORT": False,
        "METRIC": "mean"  # Ignored when export is disabled
    }
}
```

### Minimal Configuration

```python
# Missing EQUITY_DATA section - uses defaults
config = {
    "PORTFOLIO": "my_portfolio.csv"
    # EQUITY_DATA defaults: EXPORT=False, METRIC="mean"
}
```

## Configuration Validation

### Automatic Validation

The system automatically validates configuration during processing:

1. **Type Checking**: Ensures correct data types for all values
2. **Value Validation**: Checks that values are within allowed ranges
3. **Default Application**: Applies defaults for missing values
4. **Warning Generation**: Logs warnings for invalid values while applying fallbacks

### Validation Behavior

| Invalid Value         | Behavior     | Fallback                          | Warning Generated |
| --------------------- | ------------ | --------------------------------- | ----------------- |
| Invalid EXPORT type   | Use fallback | `False`                           | Yes               |
| Invalid EXPORT string | Use fallback | `False`                           | Yes               |
| Invalid METRIC value  | Use fallback | `"mean"`                          | Yes               |
| Invalid METRIC type   | Use fallback | `"mean"`                          | Yes               |
| Missing EQUITY_DATA   | Use defaults | `{EXPORT: False, METRIC: "mean"}` | Yes               |

### Example Validation Logs

```
INFO: Equity data export: ENABLED
INFO: Equity metric selection: best
WARNING: Configuration warning: Invalid EXPORT value 'maybe', defaulting to False
WARNING: Configuration warning: Invalid METRIC value 'average', defaulting to 'mean'
```

## Integration with update_portfolios.py

### Default Configuration

The default configuration in `update_portfolios.py` includes:

```python
config = {
    "EQUITY_DATA": {
        "EXPORT": True,
        "METRIC": "mean"
    }
}
```

### Runtime Configuration

Configuration can be modified at runtime:

```python
# Enable equity export for specific run
config["EQUITY_DATA"]["EXPORT"] = True
config["EQUITY_DATA"]["METRIC"] = "best"

# Run portfolio update
run(portfolio_name)
```

## Usage Patterns

### Development and Testing

```python
# Disable during development for faster processing
"EQUITY_DATA": {
    "EXPORT": False,
    "METRIC": "mean"
}
```

### Production Analysis

```python
# Enable with mean metric for stable results
"EQUITY_DATA": {
    "EXPORT": True,
    "METRIC": "mean"
}
```

### Performance Analysis

```python
# Use best metric to identify top performers
"EQUITY_DATA": {
    "EXPORT": True,
    "METRIC": "best"
}
```

### Risk Analysis

```python
# Use worst metric to analyze downside scenarios
"EQUITY_DATA": {
    "EXPORT": True,
    "METRIC": "worst"
}
```

## Error Handling

### Configuration Errors

The system handles configuration errors gracefully:

1. **Invalid Values**: Log warnings and use fallback values
2. **Missing Sections**: Apply default configuration
3. **Type Errors**: Convert or fallback to appropriate types
4. **Critical Errors**: Raise `ConfigurationError` for unrecoverable issues

### Export Errors

Export errors are isolated from main processing:

1. **File System Errors**: Log error but continue portfolio processing
   2, **Data Validation Errors**: Skip export for affected strategies
2. **Directory Creation Errors**: Log error and skip export

## Performance Considerations

### Export Impact

- **Enabled**: Minimal performance impact (<5% processing time increase)
- **Large Portfolios**: May increase memory usage for equity data storage
- **File I/O**: Export operations are performed after main processing

### Optimization Tips

1. **Disable During Development**: Use `EXPORT: False` for faster iteration
2. **Selective Export**: Enable only when equity analysis is needed
3. **Metric Selection**: Use `"mean"` for most use cases (fastest processing)

## Troubleshooting

### Common Issues

#### Equity Data Not Exported

**Problem**: No equity CSV files are generated

**Solutions:**

1. Check `EQUITY_DATA.EXPORT` is `True`
2. Verify strategies have valid backtest results
3. Check export directory permissions
4. Review logs for export errors

#### Invalid Configuration Warnings

**Problem**: Configuration validation warnings in logs

**Solutions:**

1. Check configuration values match allowed values
2. Use boolean `True`/`False` instead of strings when possible
3. Ensure METRIC values are valid (`"mean"`, `"median"`, `"best"`, `"worst"`)

#### Export Directory Not Created

**Problem**: Export directories don't exist

**Solutions:**

1. Ensure adequate file system permissions
2. Check disk space availability
3. Verify project root path is accessible

### Debugging Configuration

Enable debug logging to see configuration validation details:

```python
# In logging configuration
log_level = "debug"

# This will show:
# - Configuration validation steps
# - Metric selection for each strategy
# - Export enable/disable decisions
```

## Best Practices

### Configuration Management

1. **Use Constants**: Define configuration in constants for consistency
2. **Environment-Specific**: Use different configs for dev/test/prod
3. **Validation**: Always validate configuration before processing
4. **Documentation**: Document any non-standard configuration choices

### Export Management

1. **Disk Space**: Monitor disk usage when export is enabled
2. **File Organization**: Use consistent export directory structure
3. **Cleanup**: Implement cleanup for old export files if needed
4. **Backup**: Consider backing up export data for historical analysis

### Performance

1. **Profile Impact**: Measure performance impact in your environment
2. **Selective Use**: Enable export only when equity analysis is needed
3. **Batch Processing**: Process multiple strategies efficiently
4. **Memory Monitoring**: Monitor memory usage with large portfolios
