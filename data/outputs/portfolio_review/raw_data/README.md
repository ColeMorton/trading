# Portfolio Raw Data Export Guide

This directory contains raw data exported from VectorBT portfolios to enable external chart generation and custom analysis.

## Overview

The raw data export system extracts all underlying data from VectorBT portfolio objects and makes it available in multiple formats for external analysis and visualization.

## Available Data Types

### Core Time Series Data

- **portfolio_value**: Portfolio value over time (equity curves)
- **returns**: Daily returns series
- **cumulative_returns**: Cumulative returns over time
- **drawdowns**: Drawdown calculations with peak values

### Trading Data

- **trades**: Complete trade records with P&L details
- **orders**: Order history with entry/exit information
- **positions**: Position data with sizing and duration

### Analysis Data

- **statistics**: Comprehensive portfolio performance metrics
- **price_data**: Underlying price data used in backtests

### VectorBT Objects

- **vectorbt_portfolio.pickle**: Complete VectorBT portfolio objects for full functionality

## Export Formats

### CSV Format

- Human-readable format
- Easy to import into Excel, R, Python pandas
- Good for manual analysis and inspection

### JSON Format

- Structured format with proper data types
- Easy to import into web applications
- Good for programmatic access

### Parquet Format

- Compressed columnar format
- Fast loading and efficient storage
- Good for large datasets and analytics

### Pickle Format (VectorBT Objects Only)

- Binary format preserving full VectorBT functionality
- Allows access to all VectorBT methods and properties
- Requires Python environment with VectorBT installed

## CLI Usage Examples

### Basic Raw Data Export

```bash
# Export all data types in CSV and JSON formats
trading-cli portfolio review --profile portfolio_review_btc --export-raw-data

# Export specific data types
trading-cli portfolio review --ticker AAPL --export-raw-data \
    --raw-data-types portfolio_value,returns,trades

# Export in specific formats
trading-cli portfolio review --profile portfolio_review_multi_crypto \
    --export-raw-data --raw-data-formats csv,parquet

# Include VectorBT objects for full functionality
trading-cli portfolio review --ticker BTC-USD --export-raw-data \
    --include-vectorbt --raw-data-output-dir ./custom_exports
```

### Advanced Usage

```bash
# Export with custom output directory
trading-cli portfolio review --profile portfolio_review_op \
    --export-raw-data --raw-data-output-dir ./analysis/raw_data

# Export only trading data for trade analysis
trading-cli portfolio review --ticker TSLA --export-raw-data \
    --raw-data-types trades,orders,positions --raw-data-formats json

# Full export for comprehensive analysis
trading-cli portfolio review --profile portfolio_review_multi_crypto \
    --export-raw-data --raw-data-types all --raw-data-formats csv,json,parquet \
    --include-vectorbt
```

## File Naming Convention

Files are named using the following pattern:

```
{portfolio_name}_{data_type}.{format}
```

Examples:

- `AAPL_SMA_20_50_portfolio_value.csv`
- `multi_strategy_portfolio_trades.json`
- `BTC-USD_MACD_12_26_9_statistics.csv`
- `portfolio_benchmark.parquet`

## External Chart Generation Examples

### Using Python with Matplotlib/Plotly

#### Portfolio Value Chart

```python
import pandas as pd
import plotly.graph_objects as go

# Load portfolio value data
df = pd.read_csv('AAPL_SMA_20_50_portfolio_value.csv', parse_dates=['Date'], index_col='Date')

# Create interactive chart
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['Portfolio_Value'],
    mode='lines',
    name='Portfolio Value',
    line=dict(color='#26c6da', width=2)
))

fig.update_layout(
    title='AAPL SMA Strategy - Portfolio Value',
    xaxis_title='Date',
    yaxis_title='Portfolio Value ($)',
    template='plotly_white'
)

fig.show()
```

#### Returns Distribution Analysis

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load returns data
returns_df = pd.read_csv('AAPL_SMA_20_50_returns.csv', parse_dates=['Date'], index_col='Date')

# Create distribution plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Histogram
ax1.hist(returns_df['Returns_Pct'], bins=50, alpha=0.7, color='#26c6da')
ax1.set_title('Returns Distribution')
ax1.set_xlabel('Returns (%)')
ax1.set_ylabel('Frequency')

# Box plot
ax2.boxplot(returns_df['Returns_Pct'])
ax2.set_title('Returns Box Plot')
ax2.set_ylabel('Returns (%)')

plt.tight_layout()
plt.show()
```

#### Trade Analysis

```python
import pandas as pd
import plotly.express as px

# Load trades data
trades_df = pd.read_json('AAPL_SMA_20_50_trades.json')

# Convert date columns
trades_df['Entry Timestamp'] = pd.to_datetime(trades_df['Entry Timestamp'])
trades_df['Exit Timestamp'] = pd.to_datetime(trades_df['Exit Timestamp'])

# Create P&L scatter plot
fig = px.scatter(
    trades_df,
    x='Entry Timestamp',
    y='PnL',
    color='PnL',
    color_continuous_scale=['red', 'green'],
    title='Trade P&L Over Time',
    hover_data=['Size', 'Return']
)

fig.show()
```

#### Drawdown Analysis

```python
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load portfolio value and drawdown data
portfolio_df = pd.read_csv('AAPL_SMA_20_50_portfolio_value.csv', parse_dates=['Date'], index_col='Date')
drawdown_df = pd.read_csv('AAPL_SMA_20_50_drawdowns.csv', parse_dates=['Date'], index_col='Date')

# Create subplot
fig = make_subplots(
    rows=2, cols=1,
    subplot_titles=['Portfolio Value with Peaks', 'Drawdowns'],
    vertical_spacing=0.1
)

# Portfolio value and peaks
fig.add_trace(
    go.Scatter(x=portfolio_df.index, y=portfolio_df['Portfolio_Value'],
               name='Portfolio Value', line=dict(color='#26c6da')),
    row=1, col=1
)

fig.add_trace(
    go.Scatter(x=drawdown_df.index, y=drawdown_df['Peak_Value'],
               name='Peak Value', line=dict(color='#7e57c2', dash='dash')),
    row=1, col=1
)

# Drawdowns
fig.add_trace(
    go.Scatter(x=drawdown_df.index, y=drawdown_df['Drawdown_Pct'],
               fill='tonexty', name='Drawdowns',
               line=dict(color='red'), fillcolor='rgba(255,0,0,0.3)'),
    row=2, col=1
)

fig.update_layout(title='Portfolio Drawdown Analysis', height=600)
fig.show()
```

### Using R with ggplot2

```r
library(ggplot2)
library(dplyr)
library(readr)

# Load portfolio value data
portfolio_data <- read_csv("AAPL_SMA_20_50_portfolio_value.csv") %>%
  mutate(Date = as.Date(Date))

# Create portfolio value chart
ggplot(portfolio_data, aes(x = Date, y = Portfolio_Value)) +
  geom_line(color = "#26c6da", size = 1) +
  labs(
    title = "AAPL SMA Strategy - Portfolio Performance",
    x = "Date",
    y = "Portfolio Value ($)"
  ) +
  theme_minimal() +
  scale_y_continuous(labels = scales::dollar_format())
```

### Using JavaScript with D3.js

```javascript
// Load and visualize portfolio data
d3.csv('AAPL_SMA_20_50_portfolio_value.csv').then(function (data) {
  // Parse dates and values
  data.forEach(function (d) {
    d.Date = d3.timeParse('%Y-%m-%d')(d.Date);
    d.Portfolio_Value = +d.Portfolio_Value;
  });

  // Set dimensions
  const margin = { top: 20, right: 30, bottom: 40, left: 50 };
  const width = 800 - margin.left - margin.right;
  const height = 400 - margin.top - margin.bottom;

  // Create SVG
  const svg = d3
    .select('#chart')
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);

  // Create scales
  const xScale = d3
    .scaleTime()
    .domain(d3.extent(data, (d) => d.Date))
    .range([0, width]);

  const yScale = d3
    .scaleLinear()
    .domain(d3.extent(data, (d) => d.Portfolio_Value))
    .range([height, 0]);

  // Create line generator
  const line = d3
    .line()
    .x((d) => xScale(d.Date))
    .y((d) => yScale(d.Portfolio_Value));

  // Add the line
  svg
    .append('path')
    .datum(data)
    .attr('fill', 'none')
    .attr('stroke', '#26c6da')
    .attr('stroke-width', 2)
    .attr('d', line);

  // Add axes
  svg
    .append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(xScale));

  svg.append('g').call(d3.axisLeft(yScale));
});
```

## Working with VectorBT Objects

If you exported VectorBT objects, you can load them to access the full VectorBT API:

```python
import pickle
import vectorbt as vbt

# Load VectorBT portfolio object
with open('AAPL_SMA_20_50_vectorbt_portfolio.pickle', 'rb') as f:
    portfolio = pickle.load(f)

# Access all VectorBT functionality
print(portfolio.stats())
print(portfolio.trades().records_readable)
print(portfolio.orders().records_readable)

# Create VectorBT's built-in plots
portfolio.plot().show()
portfolio.trades().plot().show()
portfolio.drawdowns().plot().show()

# Access advanced analytics
portfolio.returns().vbt.sharpe_ratio()
portfolio.returns().vbt.max_drawdown()
portfolio.positions().records_readable
```

## Data Schema Reference

### Portfolio Value

```
Date (datetime): Date of the measurement
Portfolio_Value (float): Absolute portfolio value
Normalized_Value (float): Portfolio value normalized to starting value
```

### Returns

```
Date (datetime): Date of the return
Returns (float): Daily return as decimal (0.01 = 1%)
Returns_Pct (float): Daily return as percentage
```

### Trades

```
Entry Timestamp (datetime): Trade entry time
Exit Timestamp (datetime): Trade exit time
Size (float): Position size
Entry Price (float): Entry price
Exit Price (float): Exit price
PnL (float): Profit/Loss in absolute terms
Return (float): Return percentage
Duration (int): Trade duration in periods
```

### Orders

```
Timestamp (datetime): Order execution time
Side (str): Buy/Sell
Size (float): Order size
Price (float): Execution price
Fees (float): Transaction fees
```

### Statistics

```
Metric (str): Performance metric name
Value (various): Metric value
```

## Tips for External Analysis

1. **Use appropriate time zones**: Ensure date/time data is handled consistently
2. **Handle missing data**: Check for NaN values and handle appropriately
3. **Validate data integrity**: Cross-check totals and ensure data consistency
4. **Performance considerations**: Use efficient libraries (Polars, Dask) for large datasets
5. **Reproducibility**: Document your analysis workflow and dependencies

## Troubleshooting

### Common Issues

**File not found**: Check that export was successful and files exist in expected directory
**Date parsing errors**: Ensure proper date format handling in your analysis tools
**Memory issues with large files**: Consider using chunked reading or more efficient formats
**VectorBT loading errors**: Ensure compatible VectorBT version and Python environment

### Getting Help

- Check the CLI help: `trading-cli portfolio review --help`
- Verify export configuration: Use `--dry-run` to preview settings
- Enable verbose output: Use `--verbose` for detailed logging
- Check file permissions and disk space for export failures

## Best Practices

1. **Start small**: Begin with single strategy exports before multi-strategy
2. **Use appropriate formats**: CSV for inspection, Parquet for performance, JSON for web apps
3. **Validate exports**: Always check a few exported files to ensure data integrity
4. **Version control**: Keep track of export parameters and analysis versions
5. **Documentation**: Document your custom analysis workflows and findings
