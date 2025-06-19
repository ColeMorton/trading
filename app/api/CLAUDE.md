# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the API Server

```bash
# From the project root (/Users/colemorton/Projects/trading)
python -m app.api.run

# From the API directory, use the helper script
./start_server.sh

# Command-line options
python -m app.api.run --host 127.0.0.1 --port 8000 --reload
```

### Testing

```bash
# Simple test - verifies basic functionality
python -m app.api.simple_test

# Comprehensive test - tests all endpoints
python -m app.api.test_api
```

### Installing Dependencies

```bash
pip install -r requirements.txt
```

## Architecture

This is a FastAPI-based REST API server that serves as the backend for a trading application. Key architectural components:

### Router Organization

- **scripts.py**: Handles Python script execution (sync/async), status tracking via SSE
- **data.py**: CSV/JSON file retrieval with security validation
- **viewer.py**: Serves the CSV viewer web interface
- **sensylate.py**: Serves the Sensylate sensitivity analysis tool

### Service Layer

- **script_executor.py**: Manages Python script execution with threading, maintains execution status in memory
- **data_service.py**: Handles file operations with path validation and security checks

### Security Model

- Path validation prevents directory traversal attacks
- Allowed directories configured in `config.py`:
  - Scripts: `app/ma_cross`, `app/concurrency`, `app/strategies`
  - Data: `csv`, `json`
- 100MB file size limit for data retrieval
- Script execution timeout: 3600 seconds (1 hour)

### Execution Flow

1. Scripts are executed in separate threads/processes
2. Status tracked via unique execution IDs
3. Real-time updates available via Server-Sent Events (SSE)
4. Results streamed back to clients

### API Endpoints

- `POST /api/scripts/execute` - Execute scripts with parameters
- `GET /api/scripts/status/{id}` - Check execution status
- `GET /api/scripts/stream/{id}` - SSE stream for real-time updates
- `GET /api/data/csv/{path}` - Retrieve CSV files
- `GET /api/data/json/{path}` - Retrieve JSON files

### Integration Points

- Executes Python scripts from the broader trading application
- Serves static files for web interfaces (CSV viewer, Sensylate)
- All paths are relative to project root (`/Users/colemorton/Projects/trading`)
