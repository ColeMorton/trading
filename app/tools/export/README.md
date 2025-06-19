# Unified Export System

This module provides a centralized export management system for the trading application, supporting multiple export formats through a common interface.

## Architecture

The export system follows the Strategy pattern, making it easy to add new export formats:

```
ExportManager
    ├── CSVExporter (implements ExportStrategy)
    └── JSONExporter (implements ExportStrategy)
```

## Usage

### Basic Export

```python
from app.tools.export import ExportManager, ExportContext, ExportFormat

manager = ExportManager()
context = ExportContext(
    data=df,
    format=ExportFormat.CSV,
    feature_path="portfolios",
    config={"BASE_DIR": "/data", "TICKER": "BTC-USD"},
    log=logger
)
result = manager.export(context)

if result.success:
    print(f"Exported {result.rows_exported} rows to {result.path}")
```

### Batch Export

```python
contexts = [
    ExportContext(data=csv_data, format=ExportFormat.CSV, ...),
    ExportContext(data=json_data, format=ExportFormat.JSON, ...)
]
results = manager.export_batch(contexts)
```

### Integration with PortfolioOrchestrator

```python
# Enable new export system
orchestrator = PortfolioOrchestrator(log, use_new_export=True)
```

## Adding New Export Formats

1. Create a new exporter class implementing `ExportStrategy`:

```python
class ParquetExporter(ExportStrategy):
    def export(self, context: ExportContext) -> ExportResult:
        # Implementation
        pass
```

2. Register with ExportManager:

```python
manager.register_exporter("PARQUET", ParquetExporter())
```

## Backward Compatibility

The system provides adapters for existing export functions:

- `export_csv_adapter()` - Drop-in replacement for legacy `export_csv()`
- `export_portfolios_adapter()` - Compatible with existing portfolio export
- `save_json_report_adapter()` - Compatible with JSON report saving

## Migration Path

1. **Phase 1**: Use adapters for immediate compatibility
2. **Phase 2**: Gradually migrate to ExportContext/ExportManager
3. **Phase 3**: Remove legacy code and adapters

## Features

- **Unified Interface**: Consistent API for all export formats
- **Extensible**: Easy to add new formats
- **Validation**: Built-in data validation and error handling
- **Batch Operations**: Export multiple datasets efficiently
- **Custom Encoders**: Support for custom JSON encoders
- **Date Subdirectories**: Optional date-based organization
- **Synthetic Tickers**: Automatic formatting for pair trades

## Testing

Comprehensive test coverage includes:

- Unit tests for each component
- Integration tests with existing systems
- Real file I/O tests
- Backward compatibility verification

Run tests:

```bash
poetry run pytest tests/test_export_manager.py tests/test_export_integration.py -v
```
