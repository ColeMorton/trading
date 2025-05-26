# Puppeteer MCP Server Examples for Trading

This directory contains practical examples of using the MCP Puppeteer server for trading-related automation tasks.

## Available Examples

### 1. Market Data Scraper (`market_data_scraper.py`)

Demonstrates how to scrape real-time market data from financial websites:
- Yahoo Finance stock prices
- Cryptocurrency prices from CoinMarketCap
- Automated screenshots for verification

**Usage:**
```bash
python puppeteer_examples/market_data_scraper.py
```

### 2. Trading Alerts Monitor (`trading_alerts_monitor.py`)

Monitor multiple sources for trading signals and alerts:
- TradingView trading ideas
- Economic calendar events
- Chart screenshots for analysis

**Usage:**
```bash
python puppeteer_examples/trading_alerts_monitor.py
```

## Common Use Cases

### 1. Data Collection
- Scrape real-time prices when APIs are limited
- Collect sentiment data from trading forums
- Monitor news sites for market-moving events

### 2. Alert Monitoring
- Watch for specific price levels
- Monitor trading signals from multiple sources
- Track economic calendar events

### 3. Research Automation
- Capture charts for technical analysis
- Download financial reports
- Collect historical data not available via APIs

### 4. Testing Trading Interfaces
- Automate testing of web-based trading platforms
- Verify order execution interfaces
- Test portfolio management tools

## Integration with Trading Workflows

### Example: Automated Price Monitoring
```python
# Run every 5 minutes to check prices
while True:
    scraper = PuppeteerMarketScraper()
    scraper.start_server()
    
    # Check multiple symbols
    for symbol in ['AAPL', 'GOOGL', 'MSFT']:
        data = scraper.scrape_yahoo_finance(symbol)
        
        # Trigger alerts based on conditions
        if float(data['change'].replace('%', '')) > 5:
            send_alert(f"{symbol} moved more than 5%!")
    
    scraper.cleanup()
    time.sleep(300)  # 5 minutes
```

### Example: Daily Chart Collection
```python
# Capture charts at market close
symbols = ['SPY', 'QQQ', 'BTC-USD', 'ETH-USD']
monitor = TradingAlertsMonitor()
monitor.start_server()

for symbol in symbols:
    monitor.take_chart_screenshot(symbol, "1D")
    
monitor.cleanup()
```

## Best Practices

1. **Rate Limiting**: Add delays between requests to avoid being blocked
2. **Error Handling**: Wrap operations in try-except blocks
3. **Resource Management**: Always cleanup server processes
4. **Headless Mode**: Use `headless: true` for production
5. **Screenshots**: Take screenshots for debugging and verification

## Security Considerations

- Be cautious with credentials - never hardcode them
- Use environment variables for sensitive data
- Run in isolated environments when possible
- Be aware of website terms of service

## Extending the Examples

You can extend these examples to:
- Integrate with your existing trading strategies
- Send notifications via email/SMS/Slack
- Store data in databases
- Create trading dashboards
- Automate report generation

## Troubleshooting

If examples don't work:
1. Ensure MCP Puppeteer server is installed
2. Check that Node.js and npx are available
3. Verify websites haven't changed their structure
4. Add more delays if pages load slowly
5. Use `headless: false` to see what's happening