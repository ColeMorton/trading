# SensitivityTrader MA Cross API Integration

This document describes how to use the SensitivityTrader UI with the MA Cross API backend.

## Prerequisites

1. **Start the API Server**
   ```bash
   cd /Users/colemorton/Projects/trading
   python -m app.api.run
   ```
   The API will be available at `http://127.0.0.1:8000`

2. **Start SensitivityTrader**
   ```bash
   cd /Users/colemorton/Projects/trading/app/SensitivityTrader
   python main.py
   ```
   The UI will be available at `http://localhost:5000`

## Using the Integration

### Running an Analysis

1. Open the SensitivityTrader UI in your browser: `http://localhost:5000`

2. Enter your parameters:
   - **Tickers**: Comma-separated list (e.g., `BTC-USD, ETH-USD, AAPL`)
   - **Windows**: Maximum window size for MA analysis (default: 89)
   - **Strategy Types**: Check SMA and/or EMA
   - **Direction**: Long or Short

3. Configure advanced settings (optional):
   - Click "Advanced Configuration" to expand options
   - Set minimum requirements for filtering results
   - Choose sort criteria and direction

4. Click **"Run Analysis"** to start

### Understanding Results

The analysis will:
1. Send parameters to the MA Cross API
2. Show a loading indicator during processing
3. Display results in the data table when complete
4. Show notifications about available portfolios

### Working with Portfolios Best

When the analysis finds optimal portfolios, you'll see:
- A notification about available "best portfolios"
- **"Load Best Portfolios"** button - loads the best results into the table
- **"Export Best"** button - downloads the best portfolio CSV files

### Features

- **Synchronous Analysis**: For quick analyses with few tickers
- **Asynchronous Analysis**: For longer analyses (automatically handled)
- **Progress Updates**: Shows status during async execution
- **CSV Export**: Download portfolio results for further analysis
- **Portfolio Builder**: Add selected results to build custom portfolios

## Troubleshooting

### Connection Errors
If you see "Failed to connect to MA Cross API":
1. Ensure the API server is running on port 8000
2. Check for CORS issues in browser console
3. Verify no firewall is blocking connections

### No Results
If analysis completes but shows no results:
1. Check your minimum criteria aren't too restrictive
2. Try different tickers or parameters
3. Look at the browser console for errors

### Missing Buttons
If Export/Load buttons don't appear:
1. The analysis may not have found any "best" portfolios
2. Check browser console for JavaScript errors
3. Ensure the full analysis completed successfully

## API Endpoints Used

- `POST /api/ma-cross/analyze` - Main analysis endpoint
- `GET /api/ma-cross/status/{id}` - Check async execution status  
- `GET /api/data/csv/{path}` - Retrieve CSV files

## Testing

Run the integration test script:
```bash
python app/SensitivityTrader/test_integration.py
```

This will verify:
- API connectivity
- Request/response format
- CSV retrieval functionality