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

2. **API Request Flow**
   - Request proxied through Vite to `http://localhost:8000`
   - **Actual Response Format**:
   ```json
   {
     "status": "success",
     "files": [
       {"name": "DAILY.csv", "path": "csv/strategies/DAILY.csv", "size": 12345},
       {"name": "WEEKLY.csv", "path": "csv/strategies/WEEKLY.csv", "size": 23456}
     ],
     "directory": "csv/strategies"
   }
   ```

3. **Caching**
   - Response stored in in-memory cache with 1-hour TTL
   - Service worker caches response for offline access

4. **Auto-selection**
   - If `DAILY.csv` exists in the list, it's automatically selected
   - Triggers CSV data fetch for the selected file

## 3. CSV Data Display

### User Action
User can select different CSV files from the dropdown or view the auto-selected file

### Technical Execution
1. **File Selection**
   ```typescript
   // FileSelector component updates context
   setSelectedFile(newFile)
   ```

2. **Data Fetch via `useCSVData` Hook**
   ```bash
   GET /api/data/csv/csv/strategies/DAILY.csv
   ```
   
3. **Actual API Response**
   ```json
   {
     "status": "success",
     "data": {
       "data": [
         {
           "Date": "2024-01-01",
           "Symbol": "AAPL",
           "Price": "185.50",
           "Volume": "45000000"
         }
       ],
       "columns": ["Date", "Symbol", "Price", "Volume"]
     },
     "format": "csv",
     "file_path": "csv/strategies/DAILY.csv"
   }
   ```

4. **Data Processing**
   - PapaParse converts CSV data to JSON objects
   - Data cached in memory with 24-hour TTL
   - Updates AppContext with parsed data

5. **Rendering**
   - DataTable component uses @tanstack/react-table
   - Features: sorting, filtering, pagination (25 rows/page)
   - Column headers are dynamically generated

## 4. View Mode Toggle

### User Action
User clicks the view toggle button to switch between Table and Raw Text views

### Technical Execution
1. **State Update**
   ```typescript
   setViewMode(viewMode === 'table' ? 'text' : 'table')
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
     "portfolio": "DAILY.csv"
   }
   ```

2. **Initial Response**
   ```json
   {
     "status": "accepted",
     "execution_id": "550e8400-e29b-41d4-a716-446655440000",
     "message": "Portfolio update started",
     "script_path": "app/strategies/update_portfolios.py"
   }
   ```

3. **Server-Sent Events (SSE) Connection**
   ```bash
   GET /api/scripts/status-stream/550e8400-e29b-41d4-a716-446655440000
   Accept: text/event-stream
   ```

4. **Progress Updates**
   ```
   data: {"status": "running", "progress": 25, "message": "Fetching market data...", "timestamp": "2024-01-01T12:00:00Z"}
   
   data: {"status": "running", "progress": 50, "message": "Processing calculations...", "timestamp": "2024-01-01T12:00:05Z"}
   
   data: {"status": "completed", "progress": 100, "message": "Portfolio update completed", "timestamp": "2024-01-01T12:00:10Z", "result": {"updated_rows": 150}}
   ```

5. **Completion Actions**
   - SSE connection closes
   - CSV data automatically refreshes
   - Success message displayed to user

## 6. Offline Functionality

### User Experience
When offline, user sees an offline banner but can still view cached data

### Technical Execution
1. **Offline Detection**
   ```typescript
   // OfflineContext monitors network events
   window.addEventListener('offline', () => setIsOffline(true))
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
     e.preventDefault()
     setDeferredPrompt(e)
   })
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
   wb.messageSkipWaiting()
   wb.addEventListener('controlling', () => {
     window.location.reload()
   })
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
const cache = new Map<string, {
  data: any;
  timestamp: number;
  ttl: number;
}>();

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
        maxAgeSeconds: 86400 // 24 hours
      }
    }
  }
]
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

This guide provides a complete technical reference for understanding how Sensylate functions from both user experience and implementation perspectives, verified against the actual API and MCP server implementations.