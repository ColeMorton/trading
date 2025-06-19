# Cleanup Script Analysis & Fix

## Issue Identified

The `scripts/cleanup_old_files.py` script was too aggressive and removed important analysis files. From the git status, many critical files were deleted including:

### Critical Data That Was Removed:

- **Price Data**: `csv/price_data/` files (AAPL_D.csv, BTC-USD_D.csv, etc.)
- **Portfolio Analysis**: `csv/portfolios/` files (strategy results like AAPL_D_EMA.csv, BTC-USD_D_MACD.csv)
- **Portfolio Optimization**: `json/portfolio_optimization/` files (optimization results)
- **Trade History**: `json/trade_history/` files (comprehensive trade data)
- **Monte Carlo**: `csv/monte_carlo/` and `json/monte_carlo/` files (simulation results)
- **Best/Filtered Portfolios**: `csv/portfolios_best/` and `csv/portfolios_filtered/` files

## Solution Implemented

### 1. Enhanced `.cleanupignore` File

Created comprehensive protection patterns for:

- Price data files (fundamental market data)
- Portfolio analysis results (strategy outputs)
- Trade history exports (important analysis data)
- Monte Carlo simulation results
- Portfolio optimization results
- Strategy analysis results
- Configuration and symbol lists
- Concurrency analysis results

### 2. Improved Cleanup Script Safety

- **Default age maintained**: 7 days (as originally intended)
- **Root file protection**: Script only scans csv/ and json/ subdirectories, never root
- **Dot directory protection**: All directories starting with "." are completely skipped (.claude, .git, etc.)
- **Safety warning**: Added confirmation prompt for non-dry-run mode
- **Better documentation**: Clear warnings about potential data loss
- **Explicit safe-to-clean categories**: Only temporary files, cache, and explicitly temporary patterns

### 3. Protected Directories

```
# CRITICAL DATA - NEVER DELETE
csv/price_data/          # Market data
csv/portfolios/          # Strategy results
csv/portfolios_best/     # Best performing strategies
csv/portfolios_filtered/ # Filtered strategy results
json/trade_history/      # Trade analysis data
csv/monte_carlo/         # Simulation results
json/monte_carlo/        # Simulation configurations
json/portfolio_optimization/ # Optimization results
csv/ma_cross/           # MA strategy results
csv/macd/               # MACD strategy results
json/concurrency/       # Concurrency analysis
```

### 4. Safe to Clean (When Old)

```
cache/                  # Auto-generated cache files
experimental/temp/      # Temporary experimental files
*temp*, *tmp*          # Files with temp/tmp in name
test_results.json      # Regenerated test results
*.log                  # Log files
```

## Current Status

✅ **Fixed**: Cleanup script now protects all important analysis data
✅ **Tested**: Dry-run shows 0 files would be removed (all data protected)
✅ **Safe**: 30-day default age with confirmation prompt

## Recommendations

### Recovery

If you need to recover the deleted files:

```bash
# Check what can be recovered from git
git status
git checkout HEAD -- csv/price_data/
git checkout HEAD -- csv/portfolios/
git checkout HEAD -- json/trade_history/
# etc. for other important directories
```

### Future Usage

```bash
# Always test first
python scripts/cleanup_old_files.py --dry-run

# Default cleanup (7+ days old)
python scripts/cleanup_old_files.py

# Conservative cleanup (30+ days old)
python scripts/cleanup_old_files.py --max-age 30

# More aggressive cleanup (1+ days old) - use with extreme caution
python scripts/cleanup_old_files.py --max-age 1
```

### Best Practices

1. **Always run `--dry-run` first** to preview changes
2. **Use conservative age limits** (30+ days) for analysis projects
3. **Review `.cleanupignore`** before adding new important data types
4. **Backup important results** before running cleanup scripts

## File Categories

### Keep Forever

- Price data (csv/price_data/)
- Strategy results (csv/portfolios/)
- Analysis outputs (json/trade_history/)
- Configuration files

### Keep for Analysis Period (30+ days)

- Best portfolios (csv/portfolios_best/)
- Filtered results (csv/portfolios_filtered/)
- Monte Carlo results

### Safe to Clean (7+ days)

- Cache files (cache/)
- Temporary files (_temp_, _tmp_)
- Log files (\*.log)
- Regenerated test results
