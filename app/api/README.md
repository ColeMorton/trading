# Trading API Server

This API server provides endpoints for executing Python scripts and retrieving data files from the trading codebase.

## Features

- Execute Python scripts with parameters
- Support for both synchronous and asynchronous execution
- Status updates for long-running scripts
- Retrieve CSV and JSON data files
- List available scripts and data files
- Comprehensive logging and monitoring

## API Endpoints

### Script Execution

- `POST /api/scripts/execute` - Execute a script
- `GET /api/scripts/status/{execution_id}` - Get script execution status
- `GET /api/scripts/list` - List available scripts

### Data Retrieval

- `GET /api/data/csv/{file_path}` - Get CSV data
- `GET /api/data/json/{file_path}` - Get JSON data
- `GET /api/data/list` - List files in the default directory
- `GET /api/data/list/{directory}` - List files in a specific directory

## Running the API Server

To run the API server:

```bash
python -m app.api.run
```

Command-line options:

- `--host` - Host to bind to (default: 127.0.0.1)
- `--port` - Port to bind to (default: 8000)
- `--reload` - Enable auto-reload
- `--workers` - Number of worker processes (default: 1)
- `--log-level` - Log level (default: info)

## API Documentation

Once the server is running, you can access the API documentation at:

```
http://127.0.0.1:8000/docs
```

## Configuration

The API server configuration is defined in `app/api/config.py`. The main configuration options are:

- `BASE_DIR` - Base directory for the project
- `ALLOWED_SCRIPT_DIRS` - Directories where scripts can be executed
- `ALLOWED_DATA_DIRS` - Directories where data can be accessed
- `MAX_FILE_SIZE` - Maximum file size for data retrieval
- `SCRIPT_TIMEOUT` - Timeout for script execution
- `ENABLE_ASYNC` - Whether to enable asynchronous script execution
- `LOG_DIR` - Directory for API logs

## Examples

### Execute a Script

```bash
curl -X POST "http://127.0.0.1:8000/api/scripts/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "script_path": "app/ma_cross/1_get_portfolios.py",
    "async_execution": true,
    "parameters": {
      "TICKER": ["NVDA", "NFLX"],
      "WINDOWS": 89,
      "DIRECTION": "Long"
    }
  }'
```

### Get Script Execution Status

```bash
curl -X GET "http://127.0.0.1:8000/api/scripts/status/12345678-1234-1234-1234-123456789abc"
```

### Get CSV Data

```bash
curl -X GET "http://127.0.0.1:8000/api/data/csv/strategies/DAILY.csv"
```

### List Files

```bash
curl -X GET "http://127.0.0.1:8000/api/data/list/strategies"
```

## Future Enhancements

- Authentication with API keys
- Rate limiting
- Webhooks for script execution events
- Advanced monitoring with Prometheus metrics
- Docker containerization