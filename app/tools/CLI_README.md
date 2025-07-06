# Statistical Performance Divergence System - CLI

## Quick Start

The CLI provides an easy way to observe, configure, and execute the Statistical Performance Divergence System.

### Basic Usage

```bash
# Quick portfolio analysis
python -m app.tools --portfolio risk_on.csv

# Analysis with trade history
python -m app.tools --portfolio risk_on.csv --trade-history

# Analysis with equity curves only
python -m app.tools --portfolio conservative.csv --no-trade-history

# Interactive mode
python -m app.tools --interactive

# Show configuration
python -m app.tools --show-config

# List available portfolios
python -m app.tools --list-portfolios

# Create demo files and run example
python -m app.tools --demo
```

### Output Formats

```bash
# Table format (default)
python -m app.tools --portfolio risk_on.csv

# Summary format
python -m app.tools --portfolio risk_on.csv --output-format summary

# JSON format
python -m app.tools --portfolio risk_on.csv --output-format json

# Save results to file
python -m app.tools --portfolio risk_on.csv --save-results results.json
```

### Configuration Options

```bash
# Custom thresholds
python -m app.tools --portfolio risk_on.csv \
  --percentile-threshold 90 \
  --dual-layer-threshold 0.80 \
  --sample-size-min 10

# Confidence level filtering
python -m app.tools --portfolio risk_on.csv --confidence-level high
```

### Utility Commands

```bash
# Verbose output
python -m app.tools --portfolio risk_on.csv --verbose

# Quiet mode (errors only)
python -m app.tools --portfolio risk_on.csv --quiet

# Help
python -m app.tools --help
```

## File Structure Requirements

The CLI expects files in these locations:

```
./csv/strategies/portfolio_name.csv     # Portfolio definition (required)
./csv/positions/portfolio_name.csv      # Trade history (optional, same filename)
./json/return_distribution/ticker.json  # Asset return data (auto-loaded)
```

### Portfolio CSV Format

```csv
strategy_name,ticker,allocation,risk_level
AAPL_SMA_20_50,AAPL,0.15,medium
TSLA_EMA_12_26,TSLA,0.12,high
NVDA_SMA_15_35,NVDA,0.10,high
```

### Trade History CSV Format (Optional)

```csv
strategy_name,ticker,entry_date,exit_date,return,mfe,mae,duration_days
AAPL_SMA_20_50,AAPL,2024-01-15,2024-02-28,0.187,0.234,0.057,44
TSLA_EMA_12_26,TSLA,2024-02-01,2024-03-15,0.143,0.189,0.034,43
```

## Available Commands

| Command              | Description                         |
| -------------------- | ----------------------------------- |
| `--portfolio`        | Specify portfolio filename          |
| `--trade-history`    | Use trade history data              |
| `--no-trade-history` | Use equity curves only              |
| `--output-format`    | Output format: table, summary, json |
| `--save-results`     | Save results to file                |
| `--show-config`      | Display current configuration       |
| `--list-portfolios`  | List available portfolios           |
| `--interactive`      | Interactive mode                    |
| `--demo`             | Create demo files and run examples  |
| `--verbose`          | Detailed logging                    |
| `--quiet`            | Errors only                         |

## Configuration Parameters

| Parameter                | Default | Description                            |
| ------------------------ | ------- | -------------------------------------- |
| `--percentile-threshold` | 95      | Exit signal threshold (%)              |
| `--dual-layer-threshold` | 0.85    | Convergence threshold                  |
| `--sample-size-min`      | 15      | Minimum sample size                    |
| `--confidence-level`     | medium  | Required confidence: low, medium, high |

## Example Output

### Table Format

```
📊 Analyzing Portfolio: risk_on.csv
   Data Source: Trade History
------------------------------------------------------------

📈 Portfolio Analysis Summary
========================================
Portfolio: risk_on.csv
Total Strategies: 6
Data Source: Trade History

🎯 Signal Distribution:
  EXIT_IMMEDIATELY: 2
  STRONG_SELL: 1
  HOLD: 3

📊 Analysis Quality:
  High Confidence: 5
  Confidence Rate: 83.3%

🚨 Action Items:
  ⚠️  2 strategies require IMMEDIATE EXIT
  📉 1 strategies show STRONG SELL signals
  ✅ 3 strategies can continue (HOLD)

📋 Detailed Analysis Results
================================================================================
Strategy                  Ticker   Signal          Confidence  Recommendation
--------------------------------------------------------------------------------
TSLA_BREAKOUT_14_3        TSLA     🚨 EXIT_IMMEDIATELY  89.4%    Exit now
NVDA_MOMENTUM_RSI         NVDA     🚨 EXIT_IMMEDIATELY  86.7%    Exit now
AAPL_SMA_20_50           AAPL     📉 STRONG_SELL        78.2%    Exit soon
MSFT_EMA_21_50           MSFT     ✅ HOLD               71.5%    Continue holding
SPY_TREND_FOLLOW         SPY      ✅ HOLD               68.9%    Continue holding
QQQ_MACD_CROSS           QQQ      ✅ HOLD               65.3%    Continue holding
```

### JSON Format

```json
{
  "summary": {
    "portfolio": "risk_on.csv",
    "total_strategies": 6,
    "immediate_exits": 2,
    "strong_sells": 1,
    "holds": 3,
    "confidence_rate": 0.833
  },
  "results": {
    "TSLA_BREAKOUT_14_3": {
      "exit_signal": "EXIT_IMMEDIATELY",
      "confidence": 89.4,
      "dual_layer_score": 0.92
    }
  }
}
```

## Interactive Mode

The interactive mode provides a guided experience:

```bash
python -m app.tools --interactive
```

This will present a menu allowing you to:

1. Analyze portfolio
2. List portfolios
3. Show configuration
4. Create demo files
5. Exit

## Troubleshooting

### Common Issues

1. **Portfolio file not found**

   ```bash
   python -m app.tools --list-portfolios  # Check available files
   ```

2. **No return distribution data**

   - Ensure `./json/return_distribution/TICKER.json` exists for each ticker

3. **No trade history**

   - Use `--no-trade-history` to fall back to equity curves
   - Check that trade history file exists in `./csv/positions/`

4. **Low confidence results**
   - Use `--sample-size-min 5` for smaller datasets
   - Check data quality and completeness

### Getting Help

```bash
python -m app.tools --help              # Full help
python -m app.tools --show-config       # Current configuration
python -m app.tools --demo              # Create demo files
```

## Integration with Existing Workflows

This CLI integrates seamlessly with existing trading analysis workflows:

```bash
# After running strategy analysis
python app/ma_cross/1_get_portfolios.py

# Analyze the results statistically
python -m app.tools --portfolio AAPL_d_results.csv

# Export and save for further analysis
python -m app.tools --portfolio AAPL_d_results.csv \
  --output-format json \
  --save-results statistical_analysis.json
```
