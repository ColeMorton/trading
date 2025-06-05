# Sensylate UX Flow: Complete Technical Guide

## Overview

Sensylate is a React PWA for CSV-based portfolio analysis and strategy visualization. It connects to a FastAPI backend for data retrieval and portfolio updates, with comprehensive offline support and MCP server integration for AI assistant access.

## 1. Application Initialization

### User Action

User navigates to the application URL (http://localhost:5173 for development or the deployed PWA URL)

### Technical Execution

1. **Browser loads `index.html`**

   - Vite injects the React application bundle
   - Service worker registration begins for PWA functionality

2. **React Application Mounts**

   ```typescript
   // main.tsx renders the app with nested providers
   <React.StrictMode>
     <OfflineProvider>
       <AppProvider>
         <App />
       </AppProvider>
     </OfflineProvider>
   </React.StrictMode>
   ```

3. **Context Providers Initialize**

   - `OfflineProvider`: Sets up online/offline detection listeners
   - `AppProvider`: Initializes application state with default values

4. **Service Worker Registration**
   - PWA plugin registers service worker for offline support
   - Caching strategies are configured via Workbox

## 2. Initial Data Loading

### User Experience

User sees a loading indicator while the application fetches available CSV files

### Technical Execution

1. **`useFileList` Hook Activates**

   ```bash
   GET /api/data/list/strategies
   # Alternative: GET /api/data/list?directory=strategies
   ```

2. **Observed API Behavior**

   - **Duplicate Requests**: React often makes two simultaneous requests (likely due to StrictMode or concurrent renders)

   ```
   2025-05-26 13:47:38,779 - INFO - Listing files in directory: strategies
   2025-05-26 13:47:38,792 - INFO - Listing files in directory: strategies
   INFO: 127.0.0.1:64433 - "GET /api/data/list/strategies HTTP/1.1" 200 OK
   INFO: 127.0.0.1:64434 - "GET /api/data/list/strategies HTTP/1.1" 200 OK
   ```

3. **API Request Flow**

   - Request proxied through Vite to `http://localhost:8000`
   - **Actual Response Format**:

   ```json
   {
     "status": "success",
     "files": [
       {
         "name": "DAILY.csv",
         "path": "csv/strategies/DAILY.csv",
         "size": 12345
       },
       {
         "name": "WEEKLY.csv",
         "path": "csv/strategies/WEEKLY.csv",
         "size": 23456
       },
       {
         "name": "DAILY_test.csv",
         "path": "csv/strategies/DAILY_test.csv",
         "size": 34567
       }
     ],
     "directory": "csv/strategies"
   }
   ```

4. **Caching**

   - Response stored in in-memory cache with 1-hour TTL
   - Service worker caches response for offline access

5. **Auto-selection**
   - If `DAILY.csv` exists in the list, it's automatically selected
   - Triggers immediate CSV data fetch for the selected file
   ```
   2025-05-26 13:47:38,867 - INFO - Reading CSV file: csv/strategies/DAILY.csv
   INFO: 127.0.0.1:64437 - "GET /api/data/csv/csv/strategies/DAILY.csv HTTP/1.1" 200 OK
   ```

## 3. CSV Data Display

### User Action

User can select different CSV files from the dropdown or view the auto-selected file

### Technical Execution

1. **File Selection**

   ```typescript
   // FileSelector component updates context
   setSelectedFile(newFile);
   ```

2. **Data Fetch via `useCSVData` Hook**

   ```bash
   # Example: User selects DAILY_test.csv
   GET /api/data/csv/csv/strategies/DAILY_test.csv
   ```

   **Observed API Call:**

   ```
   2025-05-26 13:47:59,483 - INFO - Reading CSV file: csv/strategies/DAILY_test.csv
   INFO: 127.0.0.1:64488 - "GET /api/data/csv/csv/strategies/DAILY_test.csv HTTP/1.1" 200 OK
   ```

3. **Actual API Response**

   ```json
   {
     "status": "success",
     "data": {
       "data": [
         {
           "Ticker": "BTC-USD_RSP",
           "Short Window": 61,
           "Long Window": 66,
           "Strategy Type": "SMA",
           "Signal Window": 0,
           "Signal Entry": false,
           "Signal Exit": false,
           "Total Open Trades": 0,
           "Total Trades": 39,
           "Score": 2.0971743838296493,
           "Win Rate [%]": 74.35897435897436
         }
       ],
       "columns": ["Ticker", "Short Window", "Long Window", "Strategy Type", ...]
     },
     "format": "csv",
     "file_path": "csv/strategies/DAILY_test.csv"
   }
   ```

4. **Data Processing**

   - PapaParse converts CSV data to JSON objects
   - Data cached in memory with 24-hour TTL
   - Updates AppContext with parsed data

5. **Rendering**
   - DataTable component uses @tanstack/react-table
   - Features: sorting, filtering, pagination (25 rows/page)
   - Column headers are dynamically generated from strategy data
   - Displays trading metrics, signals, and performance statistics

## 4. View Mode Toggle

### User Action

User clicks the view toggle button to switch between Table and Raw Text views

### Technical Execution

1. **State Update**

   ```typescript
   setViewMode(viewMode === 'table' ? 'text' : 'table');
   ```

2. **Conditional Rendering**
   - Table View: Renders `DataTable` component with interactive features
   - Text View: Renders `RawTextView` component showing raw CSV content

## 5. Portfolio Update Process

### User Action

User clicks the "Update" button to refresh portfolio data

### Technical Execution

1. **Update Request**

   ```bash
   POST /api/scripts/update-portfolio
   Content-Type: application/json

   {
     "portfolio": "DAILY_test.csv"
   }
   ```

   **Observed API Call:**

   ```
   2025-05-26 13:48:04,721 - INFO - Updating portfolio: DAILY_test.csv
   2025-05-26 13:48:04,723 - INFO - Executing script app/strategies/update_portfolios.py with parameters: {'portfolio': 'DAILY_test.csv'}
   INFO: 127.0.0.1:64505 - "POST /api/scripts/update-portfolio HTTP/1.1" 200 OK
   ```

2. **Initial Response**

   ```json
   {
     "status": "accepted",
     "execution_id": "9322338b-68ee-4ed6-ae5c-2db7f965584e",
     "message": "Portfolio update started",
     "script_path": "app/strategies/update_portfolios.py"
   }
   ```

3. **Server-Sent Events (SSE) Connection**

   ```bash
   GET /api/scripts/status-stream/9322338b-68ee-4ed6-ae5c-2db7f965584e
   Accept: text/event-stream
   ```

   **Observed SSE Setup:**

   ```
   2025-05-26 13:48:04,733 - INFO - Starting SSE stream for execution ID: 9322338b-68ee-4ed6-ae5c-2db7f965584e
   INFO: 127.0.0.1:64508 - "GET /api/scripts/status-stream/9322338b-68ee-4ed6-ae5c-2db7f965584e HTTP/1.1" 200 OK
   ```

4. **Detailed Portfolio Processing**

   **Phase 1: Portfolio Loading**

   ```
   2025-05-26 13:48:07,787 - INFO - Loading portfolio: DAILY_test.csv
   2025-05-26 13:48:07,787 - INFO - Config BASE_DIR: /Users/colemorton/Projects/trading
   2025-05-26 13:48:07,787 - INFO - Successfully read CSV file with 3 strategies
   ```

   **Phase 2: Synthetic Pair Creation** (for each strategy)

   - **BTC-USD_RSP**: Downloads BTC-USD (3904 records) + RSP (5553 records) → 2688 merged rows
   - **BTC-USD_QQQ**: Downloads BTC-USD (3904 records) + QQQ (6594 records) → 2688 merged rows
   - **BTC-USD_SPY**: Downloads BTC-USD (3904 records) + SPY (8136 records) → 2688 merged rows

   **Phase 3: Strategy Analysis**

   ```
   # For each strategy: SMA calculation, signal detection, performance metrics
   2025-05-26 13:48:07,831 - INFO - Processing strategy configuration for BTC-USD_RSP
   2025-05-26 13:48:07,831 - INFO - Using strategy type 'SMA' from field 'STRATEGY_TYPE' for BTC-USD_RSP
   2025-05-26 13:48:13,567 - INFO - Current SMA signal for BTC-USD_RSP: False
   2025-05-26 13:48:14,831 - INFO - Score: 1.9922
   ```

   **Phase 4: Results Generation**

   ```
   2025-05-26 13:48:18,404 - INFO - === Strategy Summary ===
   2025-05-26 13:48:18,404 - INFO - Total Strategies: 3
   2025-05-26 13:48:18,404 - INFO - Total Open Trades: 2
   2025-05-26 13:48:18,404 - INFO - Total Signal Entries: 1
   2025-05-26 13:48:18,404 - INFO - Signal Entry Ratio: 0.3333 (Signal Entries / Total Strategies)
   ```

5. **Strategy Results Summary**

   - **BTC-USD_RSP**: SMA(61,66), Score: 1.9922, Signal Entry: False, Open Trades: 0
   - **BTC-USD_QQQ**: SMA(71,77), Score: 2.0922, Signal Entry: False, Open Trades: 0
   - **BTC-USD_SPY**: SMA(73,76), Score: 2.0743, Signal Entry: **True**, Open Trades: 0

6. **Completion Actions**

   ```
   2025-05-26 13:48:18,404 - INFO - Total execution time: 10.62 seconds
   2025-05-26 13:48:18,404 - INFO - Script execution completed in 10.62 seconds
   2025-05-26 13:48:18,412 - INFO - Script execution 9322338b-68ee-4ed6-ae5c-2db7f965584e completed, closing SSE connection
   ```

7. **Auto-refresh Data**

   ```bash
   GET /api/data/csv/csv/strategies/DAILY_test.csv
   ```

   **Observed Auto-refresh:**

   ```
   2025-05-26 13:48:19,432 - INFO - Reading CSV file: csv/strategies/DAILY_test.csv
   INFO: 127.0.0.1:64558 - "GET /api/data/csv/csv/strategies/DAILY_test.csv HTTP/1.1" 200 OK
   ```

8. **Performance Metrics**
   - **Total Execution Time**: 10.62 seconds (script) + 13.68 seconds (total with overhead)
   - **Data Downloads**: Fresh market data for all components (BTC-USD, RSP, QQQ, SPY)
   - **Strategy Processing**: 3 synthetic pairs analyzed with SMA signals
   - **Signal Detection**: 1 buy signal generated (BTC-USD_SPY)
   - **Portfolio Breadth**: 66.67% strategies with open positions

## 6. Offline Functionality

### User Experience

When offline, user sees an offline banner but can still view cached data

### Technical Execution

1. **Offline Detection**

   ```typescript
   // OfflineContext monitors network events
   window.addEventListener('offline', () => setIsOffline(true));
   ```

2. **UI Updates**

   - `OfflineBanner` component appears
   - Update button disabled
   - Cached data remains accessible

3. **Cache Retrieval**
   - In-memory cache checked first
   - Service worker cache as fallback
   - Error message if no cached data available

## 7. PWA Installation

### User Action

User can install the app as a PWA when prompted

### Technical Execution

1. **Install Prompt Detection**

   ```typescript
   window.addEventListener('beforeinstallprompt', (e) => {
     e.preventDefault();
     setDeferredPrompt(e);
   });
   ```

2. **Custom Install UI**

   - `InstallPrompt` component displays
   - User choice stored in localStorage

3. **Installation Process**
   - User clicks "Install"
   - Browser native install dialog appears
   - App installs with manifest configuration

## 8. PWA Updates

### User Experience

User receives notification when app updates are available

### Technical Execution

1. **Update Detection**

   - Service worker detects new version
   - `PWAUpdateNotification` component displays

2. **Update Process**
   ```typescript
   // User clicks update
   wb.messageSkipWaiting();
   wb.addEventListener('controlling', () => {
     window.location.reload();
   });
   ```

## API Endpoints Reference

### Data Endpoints

- `GET /api/data/list/strategies` - List CSV files in strategies directory
- `GET /api/data/csv/{file_path}` - Retrieve CSV file data
- `GET /api/data/json/{file_path}` - Retrieve JSON file data
- `GET /api/data/list?directory={dir}` - List files in specific directory

### Script Endpoints

- `POST /api/scripts/update-portfolio` - Portfolio update (specialized)
- `POST /api/scripts/execute` - Execute any script (generic)
- `GET /api/scripts/status/{execution_id}` - Get execution status
- `GET /api/scripts/status-stream/{execution_id}` - SSE status stream
- `GET /api/scripts/list` - List available scripts

### Health & Info

- `GET /` - API information
- `GET /health` - Health check

## MCP Server Integration

### Configuration

```json
{
  "mcpServers": {
    "trading-mcp": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "env": {
        "API_BASE_URL": "http://localhost:8000",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Available MCP Tools

1. **Script Tools**:

   - `list_trading_scripts` - Lists available Python scripts
   - `execute_trading_script` - Executes scripts with parameters
   - `check_script_status` - Checks execution status

2. **Data Tools**:

   - `list_data_files` - Lists CSV/JSON data files
   - `get_trading_data` - Retrieves file contents

3. **Portfolio Tools**:
   - `update_portfolio` - Specialized portfolio update tool

## Error Handling

### Network Errors

```json
{
  "status": "error",
  "error": "Network request failed",
  "message": "Unable to connect to server",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Script Execution Errors

```json
{
  "status": "failed",
  "error": "ScriptExecutionError",
  "message": "Portfolio update failed: Invalid data format",
  "traceback": "...",
  "execution_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Caching Implementation

### In-Memory Cache (Frontend)

```typescript
// api.ts cache structure
const cache = new Map<
  string,
  {
    data: any;
    timestamp: number;
    ttl: number;
  }
>();

// Cache TTLs:
// - File lists: 1 hour (3600000ms)
// - CSV data: 24 hours (86400000ms)
```

### Service Worker Cache (PWA)

```javascript
// Workbox strategies
runtimeCaching: [
  {
    urlPattern: /^\/api\/data\/.*/,
    handler: 'NetworkFirst',
    options: {
      cacheName: 'api-data-cache',
      expiration: {
        maxEntries: 50,
        maxAgeSeconds: 86400, // 24 hours
      },
    },
  },
];
```

## Technical Architecture Overview

### State Management

- **AppContext**: Centralizes app state (selectedFile, viewMode, csvData, loading/error states)
- **OfflineContext**: Tracks network connectivity
- Component-level state for UI-specific concerns

### Data Flow

```
User Action → React Component → Custom Hook → API Service → FastAPI Backend
                    ↓                              ↓              ↓
              Context Update               Memory Cache    Database/Scripts
                    ↓                              ↓              ↓
              Re-render                   Service Worker   Response
```

### Key Technologies

- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Build**: Vite with React plugin + PWA plugin
- **Data**: @tanstack/react-table for advanced table features
- **HTTP**: Axios with proxy to localhost:8000
- **CSV**: PapaParse for parsing
- **PWA**: vite-plugin-pwa with Workbox for caching strategies

### Offline Capabilities

1. **Detection & Notification**: Browser online/offline events tracked
2. **Functionality When Offline**: Cached file lists and CSV data remain accessible
3. **Service Worker Strategies**: Auto-update registration, runtime caching for API responses

### PWA Features

1. **Installation**: Custom install UI with dismiss option
2. **Updates**: Seamless update process with user notifications
3. **Manifest**: Full PWA manifest with theme color #6366f1 (indigo)

## Real-World Portfolio Update Example

Based on actual API logs, here's what happens during a complete portfolio update cycle:

### Input Portfolio (DAILY_test.csv)

```csv
Ticker,Short Window,Long Window,Strategy Type,Signal Window,Signal Entry,Signal Exit
BTC-USD_RSP,61,66,SMA,0,False,False
BTC-USD_QQQ,71,77,SMA,0,False,False
BTC-USD_SPY,73,76,SMA,0,False,False
```

### Processing Pipeline

1. **Market Data Download**: Real-time data for BTC-USD, RSP, QQQ, SPY
2. **Synthetic Pair Creation**: Creates ratio-based pairs (BTC-USD/RSP, BTC-USD/QQQ, BTC-USD/SPY)
3. **Technical Analysis**: Calculates SMA crossovers for each pair
4. **Signal Detection**: Identifies entry/exit signals based on moving average crossovers
5. **Performance Metrics**: Computes 40+ trading statistics per strategy

### Output Results

```csv
Ticker,Strategy Type,Short Window,Long Window,Score,Signal Entry,Signal Exit,Total Trades,Win Rate [%],Total Return [%]
BTC-USD_QQQ,SMA,71,77,2.0922,False,False,37,70.27,7327.54
BTC-USD_SPY,SMA,73,76,2.0743,True,False,41,70.73,12779.20
BTC-USD_RSP,SMA,61,66,1.9922,False,False,39,74.36,6283.20
```

### Key Trading Insights

- **BTC-USD_SPY** generated a buy signal (Signal Entry: True)
- **Portfolio Breadth**: 66.67% of strategies showing bullish conditions
- **Best Performer**: BTC-USD_SPY with 12,779% total return over test period
- **Highest Win Rate**: BTC-USD_RSP with 74.36% winning trades

This comprehensive example demonstrates how the Sensylate application processes real trading strategies and provides actionable market signals through an intuitive web interface.

---

This guide provides a complete technical reference for understanding how Sensylate functions from both user experience and implementation perspectives, verified against actual API logs and MCP server implementations.
