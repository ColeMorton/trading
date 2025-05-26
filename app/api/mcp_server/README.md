# Trading API MCP Server

Model Context Protocol (MCP) server that exposes Trading API functionality to AI assistants.

## Phase 1 Implementation Status

This is the Phase 1 implementation providing core MCP infrastructure:

### ✅ Completed
- Basic MCP server structure
- Configuration management system
- Logging infrastructure
- Test tool (`hello_world`) for verification
- MCP server manifest file

### Directory Structure
```
mcp_server/
├── __init__.py
├── server.py          # Main MCP server implementation
├── config.py          # Configuration management
├── tools/
│   └── __init__.py
├── handlers/
│   └── __init__.py
├── test_server.py     # Test script
└── README.md          # This file
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The MCP server can be configured using environment variables:

- `MCP_API_BASE_URL`: Base URL for the Trading API (default: http://localhost:8000)
- `MCP_API_KEY`: Optional API key for authentication
- `MCP_REQUEST_TIMEOUT`: Request timeout in seconds (default: 30)
- `MCP_MAX_RETRIES`: Maximum number of retries (default: 3)
- `MCP_LOG_LEVEL`: Logging level (default: INFO)
- `MCP_LOG_FILE`: Optional log file path

## Running the Server

### Option 1: Direct Python
```bash
# From the project root
python -m app.api.mcp_server.server

# From the api directory
python -m mcp_server.server
```

### Option 2: Using MCP Client
Configure your MCP client to use the manifest file at `mcp_server.json`.

## Testing

The server includes a test tool `hello_world` that echoes messages:

```json
{
  "name": "hello_world",
  "arguments": {
    "message": "Test message"
  }
}
```

## Next Phases

- Phase 2: API Client Infrastructure
- Phase 3: Script Execution Tools
- Phase 4: Data Retrieval Tools
- Phase 5: Portfolio Management Tools
- Phase 6: Security & Error Handling
- Phase 7: Performance Optimization
- Phase 8: Documentation & Testing
- Phase 9: Monitoring & Observability
- Phase 10: Production Deployment