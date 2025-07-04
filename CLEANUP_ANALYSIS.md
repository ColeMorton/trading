# Cleanup Script Analysis & Fix

## Issue Identified

The `scripts/cleanup_old_files.py` script was too aggressive and removed important analysis files. From the git status, many critical files were deleted including:

### Critical Data That Was Removed:

- **Portfolio Analysis**: `csv/portfolios/` files (strategy results like AAPL_D_EMA.csv, BTC-USD_D_MACD.csv)
- **Portfolio Optimization**: `json/portfolio_optimization/` files (optimization results)
- **Trade History**: `json/trade_history/` files (comprehensive trade data)
- **Monte Carlo**: `csv/monte_carlo/` and `json/monte_carlo/` files (simulation results)
- **Best/Filtered Portfolios**: `csv/portfolios_best/` and `csv/portfolios_filtered/` files

### Data That Should Be Cleaned When Old:

- **Price Data**: `csv/price_data/` files (AAPL_D.csv, BTC-USD_D.csv, etc.) - regenerated automatically
- **Equity Data**: Strategy equity data (`csv/ma_cross/equity_data/`, `csv/macd_cross/equity_data/`) - generated during analysis

## Solution Implemented

### 1. **CONSERVATIVE WHITELIST APPROACH**

**BREAKING CHANGE**: Replaced `.cleanupignore` blacklist with `.cleanupwhitelist` for maximum safety.

**New Safety Policy**:

- **ONLY** files explicitly listed in `.cleanupwhitelist` can be cleaned
- **ALL** other files are automatically protected
- Script exits immediately if no whitelist file exists
- No more accidental deletion of important files

**Whitelisted for cleanup** (when old):

- Price data files (`csv/price_data/*.csv`) - regenerated automatically
- Strategy equity curves (`csv/ma_cross/equity_data/*.csv`, `csv/macd_cross/equity_data/*.csv`)
- Stop loss analysis (`csv/stop_loss/*.csv`) - regenerated from analysis
- Trade history positions (`csv/trade_history/*_positions.csv`) - derived data
- Cache and temporary files
- Test files and logs

### 2. Enhanced Script Safety Features

- **WHITELIST-ONLY**: Only files matching `.cleanupwhitelist` patterns are considered
- **Fail-safe mode**: Script exits if no whitelist file exists
- **Default age maintained**: 7 days (as originally intended)
- **Root file protection**: Script only scans csv/ and json/ subdirectories, never root
- **Dot directory protection**: All directories starting with "." are completely skipped (.claude, .git, etc.)
- **Safety warning**: Added confirmation prompt for non-dry-run mode
- **Conservative by design**: Unknown files are never cleaned

### 3. Current Protection Status

```
# AUTOMATICALLY PROTECTED (not in whitelist)
csv/portfolios/                    # Strategy results - PROTECTED
csv/portfolios_best/               # Best performing strategies - PROTECTED
csv/portfolios_filtered/           # Filtered strategy results - PROTECTED
json/trade_history/                # Trade analysis data - PROTECTED
csv/monte_carlo/                   # Simulation results - PROTECTED
json/monte_carlo/                  # Simulation configurations - PROTECTED
json/portfolio_optimization/       # Optimization results - PROTECTED
csv/ma_cross/current_signals/      # MA strategy signals - PROTECTED
csv/ma_cross/price_data/           # MA strategy price data - PROTECTED
csv/ma_cross/protective_stop_loss/ # MA strategy stop loss - PROTECTED
csv/ma_cross/rsi/                  # MA strategy RSI - PROTECTED
csv/ma_cross/signals/              # MA strategy signals - PROTECTED
csv/macd/                          # MACD strategy results - PROTECTED
csv/macd_cross/current_signals/    # MACD strategy signals - PROTECTED
csv/macd_cross/price_data/         # MACD strategy price data - PROTECTED
json/concurrency/                  # Concurrency analysis - PROTECTED
ALL OTHER FILES                    # Everything else - PROTECTED BY DEFAULT
```

```
# WHITELISTED FOR CLEANUP (when old, only these can be removed)
csv/price_data/*.csv               # Market data (regenerated automatically)
csv/ma_cross/equity_data/*.csv     # MA strategy equity curves
csv/macd_cross/equity_data/*.csv   # MACD strategy equity curves
csv/stop_loss/*.csv                # Stop loss analysis (regenerated)
csv/trade_history/*_positions.csv  # Trade position files (derived data)
cache/*                            # Cache files
experimental/temp/*                # Temporary experimental files
*temp*, *tmp*                      # Files with temp/tmp in name
test_results.json                  # Test result files
*.log                              # Log files
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

✅ **ULTRA-SAFE**: Conservative whitelist approach implemented
✅ **TESTED**: Only explicitly whitelisted files are considered for cleanup
✅ **FAIL-SAFE**: Script exits if no whitelist file exists
✅ **VERIFIED**: All critical analysis data automatically protected by default

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
# Always test first - ONLY whitelisted files considered
python scripts/cleanup_old_files.py --dry-run

# Default cleanup (7+ days old, whitelisted files only)
python scripts/cleanup_old_files.py

# Conservative cleanup (30+ days old, whitelisted files only)
python scripts/cleanup_old_files.py --max-age 30

# Aggressive cleanup (1+ days old, still only whitelisted files)
python scripts/cleanup_old_files.py --max-age 1

# To add new cleanable files, edit .cleanupwhitelist
```

### Best Practices

1. **Always run `--dry-run` first** to preview changes
2. **Review `.cleanupwhitelist`** before adding new cleanable patterns
3. **Only add files to whitelist that are truly regenerable**
4. **Use conservative age limits** (30+ days) for important derived data
5. **Test whitelist changes thoroughly** with dry-run mode

## File Categories

### Automatically Protected (Not in Whitelist)

- **Strategy results** (csv/portfolios/) - PROTECTED
- **Analysis outputs** (json/trade_history/) - PROTECTED
- **Configuration files** - PROTECTED
- **Strategy analysis core data** (signals, price_data subdirectories) - PROTECTED
- **Best portfolios** (csv/portfolios_best/) - PROTECTED
- **Filtered results** (csv/portfolios_filtered/) - PROTECTED
- **Monte Carlo results** - PROTECTED
- **ALL OTHER FILES** - PROTECTED BY DEFAULT

### Whitelisted for Cleanup (Only When Explicitly Added)

- **Price data** (csv/price_data/\*.csv) - regenerated automatically
- **Strategy equity data** (csv/_/equity_data/_.csv) - generated during analysis
- **Stop loss analysis** (csv/stop_loss/\*.csv) - regenerated from analysis
- **Trade positions** (csv/trade_history/\*\_positions.csv) - derived data
- **Cache files** (cache/\*) - temporary data
- **Temporary files** (_temp_, _tmp_) - temporary data
- **Log files** (\*.log) - regenerated
- **Test results** (test_results.json) - regenerated
