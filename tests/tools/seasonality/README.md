# Seasonality Feature Tests

## Quick Start

```bash
# Run all seasonality tests
pytest tests/tools/seasonality/ -v

# Quick check (quiet mode)
pytest tests/tools/seasonality/ -q

# Run specific test file
pytest tests/tools/seasonality/test_seasonality_auto_download.py -v
```

## Test Files

| File                                | Tests   | Focus Area                                | Risk Level    |
| ----------------------------------- | ------- | ----------------------------------------- | ------------- |
| `test_seasonality_auto_download.py` | 13      | Auto-download logic, retry mechanism      | 🔴 CRITICAL   |
| `test_seasonality_analyzer.py`      | 28      | Risk metrics (Sharpe, Sortino, etc.)      | 🔴 CRITICAL   |
| `test_seasonality_patterns.py`      | 25      | Pattern detection (monthly, weekly, etc.) | 🟡 HIGH       |
| `test_seasonality_models.py`        | 20      | Pydantic model validation                 | 🟡 HIGH       |
| `test_seasonality_exports.py`       | 16      | JSON/CSV export integrity                 | 🟡 HIGH       |
| **TOTAL**                           | **102** | **Phase 1 Critical Coverage**             | **100% PASS** |

## Test Fixtures

Located in `conftest.py`:

- `standard_5yr_data` - 5 years with clear monthly pattern
- `short_1yr_data` - Insufficient data (triggers download)
- `all_positive_returns_data` - Every return positive
- `all_negative_returns_data` - Every return negative
- `flat_returns_data` - Zero volatility
- `high_skew_data` - Right-skewed distribution
- `few_samples_data` - Minimal data for edge testing
- `mock_yfinance_success_data` - Mock download success
- `mock_yfinance_multiindex_data` - Mock MultiIndex columns

## Bugs Found & Fixed

1. **Sharpe Ratio Division by Near-Zero** 🔴 CRITICAL

   - Prevented invalid huge ratios from floating point precision issues

2. **JSON Export None Handling** 🟡 MEDIUM

   - Fixed crashes when consistency_score is None

3. **Output Format Validation** 🟢 LOW
   - Added 'both' as valid output format

## Coverage

- **Critical Paths**: ~92% coverage
- **Auto-download**: ~95% coverage
- **Risk Metrics**: 100% coverage
- **Data Models**: 100% coverage

## Next Phases

- **Phase 2**: Integration & CLI tests
- **Phase 3**: Visualization tests
- **Phase 4**: Performance benchmarks

See `PHASE1_COMPLETION_REPORT.md` for detailed analysis.
