# CSV Schema Audit Report

==================================================

## Executive Summary

- Total CSV files analyzed: 277
- Compliant files: 207 (74.7%)
- Non-compliant files: 70
- Error files: 0

## Directory: csv/portfolios

**Expected Schema**: base
**Expected Columns**: 58

### Statistics

- Total files: 107
- Compliant: 107
- Non-compliant: 0
- Errors: 0

### Column Count Distribution

- 58 columns: 107 files

### Schema Type Distribution

- base: 107 files

---

## Directory: csv/portfolios_filtered

**Expected Schema**: filtered
**Expected Columns**: 61

### Statistics

- Total files: 58
- Compliant: 0
- Non-compliant: 58
- Errors: 0

### Column Count Distribution

- 61 columns: 58 files

### Schema Type Distribution

- filtered: 58 files

### Most Common Issues

- Column count mismatch: expected 58, got 61: 58 files
- Schema type mismatch: expected base, detected filtered: 58 files

### Non-Compliant Files

- `csv/portfolios_filtered/QQQ_D_SMA.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_filtered/MSTR_D_EMA.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_filtered/USLM_D_SMA.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_filtered/BTC-USD_D_SMA.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_filtered/MSTR_D_SMA.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_filtered/BTC-USD_D_EMA.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_filtered/FMC_D_SMA.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_filtered/QQQ_D_EMA.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_filtered/20250604/NTRA_D_SMA.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_filtered/20250604/AAPL_D_EMA.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
  - ... and 48 more files

---

## Directory: csv/portfolios_best

**Expected Schema**: filtered
**Expected Columns**: 61

### Statistics

- Total files: 12
- Compliant: 0
- Non-compliant: 12
- Errors: 0

### Column Count Distribution

- 61 columns: 12 files

### Schema Type Distribution

- filtered: 12 files

### Most Common Issues

- Column count mismatch: expected 58, got 61: 12 files
- Schema type mismatch: expected base, detected filtered: 12 files

### Non-Compliant Files

- `csv/portfolios_best/20250603/PENDLE-USD_20250603_2135_D.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_best/20250603/PENDLE-USD_20250603_2137_D.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_best/20250603/20250603_2112_D.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_best/20250603/20250603_1801_D.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_best/20250603/PENDLE-USD_20250603_2140_D.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_best/20250603/20250603_1808_D.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_best/20250602/20250602_1313_D.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_best/20250602/V_20250602_1345_D.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_best/20250605/PENDLE-USD_20250605_2137_D.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
- `csv/portfolios_best/20250605/20250605_2112_D.csv` (61 cols)
  - Column count mismatch: expected 58, got 61
  - Schema type mismatch: expected base, detected filtered
  - ... and 2 more files

---

## Directory: csv/strategies

**Expected Schema**: mixed
**Expected Columns**: variable

### Statistics

- Total files: 100
- Compliant: 100
- Non-compliant: 0
- Errors: 0

### Column Count Distribution

- 40 columns: 1 files
- 53 columns: 5 files
- 54 columns: 1 files
- 55 columns: 11 files
- 56 columns: 40 files
- 57 columns: 1 files
- 58 columns: 37 files
- 59 columns: 4 files

### Schema Type Distribution

- base: 58 files
- extended: 18 files
- filtered: 1 files
- unknown: 23 files

---

## Migration Recommendations

### Priority 1: csv/portfolios_filtered (MEDIUM)

- Non-compliant files: 58
- Error files: 0
- **Action**: Migrate to Filtered schema (61 columns)

### Priority 2: csv/portfolios_best (MEDIUM)

- Non-compliant files: 12
- Error files: 0
- **Action**: Migrate to Filtered schema (61 columns)
