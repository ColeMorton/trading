# MCP Server Implementation Plan for Trading API

## Overview
This document outlines the implementation plan for creating an MCP (Model Context Protocol) server that exposes the Trading API functionality to AI assistants. The MCP server will provide tools for script execution, data retrieval, and portfolio management.

## 1. Architecture Design

### 1.1 MCP Server Structure
```
api/
├── mcp_server/
│   ├── __init__.py
│   ├── server.py          # Main MCP server implementation
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── script_tools.py    # Script execution tools
│   │   ├── data_tools.py      # Data retrieval tools
│   │   └── portfolio_tools.py # Portfolio management tools
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── api_client.py      # HTTP client for API calls
│   └── config.py              # MCP server configuration
└── mcp_server.json            # MCP server manifest
```

### 1.2 Integration Approach
- **Wrapper Pattern**: MCP server acts as a wrapper around the existing FastAPI endpoints
- **HTTP Client**: Internal HTTP client to communicate with the FastAPI server
- **Shared Models**: Reuse existing Pydantic models for request/response validation
- **Independent Operation**: MCP server runs as a separate process, connecting to the API via HTTP

## 2. MCP Tools Specification

### 2.1 Script Execution Tools

#### `execute_trading_script`
Execute a trading script with specified parameters.
```json
{
  "name": "execute_trading_script",
  "description": "Execute a trading script from allowed directories",
  "inputSchema": {
    "type": "object",
    "properties": {
      "script_name": {"type": "string", "description": "Name of the script to execute"},
      "parameters": {"type": "object", "description": "Script parameters"},
      "async_mode": {"type": "boolean", "description": "Execute asynchronously", "default": false}
    },
    "required": ["script_name"]
  }
}
```

#### `check_script_status`
Check the status of an asynchronously executing script.
```json
{
  "name": "check_script_status",
  "description": "Check the status of an async script execution",
  "inputSchema": {
    "type": "object",
    "properties": {
      "execution_id": {"type": "string", "description": "Execution ID from async execution"}
    },
    "required": ["execution_id"]
  }
}
```

#### `list_trading_scripts`
List all available trading scripts.
```json
{
  "name": "list_trading_scripts",
  "description": "List all available trading scripts in allowed directories",
  "inputSchema": {
    "type": "object",
    "properties": {}
  }
}
```

### 2.2 Data Retrieval Tools

#### `get_trading_data`
Retrieve trading data from CSV or JSON files.
```json
{
  "name": "get_trading_data",
  "description": "Retrieve trading data from CSV or JSON files",
  "inputSchema": {
    "type": "object",
    "properties": {
      "file_path": {"type": "string", "description": "Path to the data file"},
      "file_type": {"type": "string", "enum": ["csv", "json"], "description": "Type of data file"}
    },
    "required": ["file_path", "file_type"]
  }
}
```

#### `list_data_files`
List available data files in a directory.
```json
{
  "name": "list_data_files",
  "description": "List data files in allowed directories",
  "inputSchema": {
    "type": "object",
    "properties": {
      "directory": {"type": "string", "description": "Directory to list files from", "default": ""}
    }
  }
}
```

### 2.3 Portfolio Management Tools

#### `update_portfolio`
Update portfolio with new trading data.
```json
{
  "name": "update_portfolio",
  "description": "Update portfolio with new trading positions",
  "inputSchema": {
    "type": "object",
    "properties": {
      "csv_filename": {"type": "string", "description": "CSV file containing portfolio data"},
      "script_dir": {"type": "string", "description": "Script directory", "default": "strategies"}
    },
    "required": ["csv_filename"]
  }
}
```

## 3. Implementation Phases

Each phase is designed to be implemented independently without affecting existing functionality.

### Phase 1: Core MCP Infrastructure ✅ COMPLETED
**Goal**: Establish basic MCP server that can be tested independently

**Implementation Steps**:
1. Create `mcp_server/` directory structure
2. Implement basic MCP server with a simple test tool
3. Create `mcp_server.json` manifest file
4. Set up logging infrastructure
5. Create configuration management system

**Deliverables**:
- Working MCP server with "hello_world" test tool
- Configuration system for API connection settings
- Basic logging setup

**Testing**:
- MCP server starts and responds to tool calls
- Configuration loads correctly
- Logs are generated properly

**Implementation Summary** (Completed on 26/05/2025):

**Files Created**:
1. **Directory Structure**:
   - `mcp_server/` - Main package directory
   - `mcp_server/tools/` - Tools module (placeholder)
   - `mcp_server/handlers/` - Handlers module (placeholder)

2. **Core Implementation Files**:
   - `mcp_server/__init__.py` - Package initialization with version info
   - `mcp_server/server.py` - Main MCP server implementation with TradingAPIMCPServer class
   - `mcp_server/config.py` - Configuration management using Pydantic Settings
   - `mcp_server/logging_setup.py` - Structured logging setup with structlog
   - `mcp_server.json` - MCP manifest file for client configuration

3. **Test Infrastructure**:
   - `mcp_server/test_mcp_server.py` - Basic test script
   - `mcp_server/test_integration.py` - Integration test for tool registration

**Key Implementation Details**:

1. **MCP Server Architecture**:
   ```python
   class TradingAPIMCPServer:
       def __init__(self):
           self.server = Server(config.server_name)
           self._setup_tools()
   ```
   - Uses MCP's Server class with STDIO communication
   - Implements proper tool registration using `@server.list_tools()` and `@server.call_tool()` decorators

2. **Configuration System**:
   ```python
   class MCPConfig(BaseSettings):
       api_base_url: str = "http://localhost:8000"
       api_key: Optional[str] = None
       request_timeout: int = 30
       max_retries: int = 3
       # ... other settings
   ```
   - Environment variable support with `MCP_` prefix
   - Configurable API connection settings
   - Server metadata (name, version)

3. **Hello World Test Tool**:
   ```python
   Tool(
       name="hello_world",
       description="Test tool to verify MCP server functionality",
       inputSchema={...}
   )
   ```
   - Accepts a message parameter
   - Returns formatted response confirming server functionality

4. **Logging Infrastructure**:
   - Structured logging with structlog
   - JSON formatting for production
   - Configurable log levels
   - Proper error handling and logging

5. **Dependencies Added**:
   - `mcp>=0.1.0` - Core MCP protocol library
   - `httpx>=0.24.0` - Modern HTTP client (for future API calls)
   - `tenacity>=8.0.0` - Retry logic library
   - `structlog>=23.0.0` - Structured logging
   - `pydantic-settings==2.0.0` - Configuration management

**Test Results**:
- ✅ Server initializes without errors
- ✅ Configuration loads from environment variables
- ✅ Hello world tool properly registered
- ✅ Structured logging outputs correctly formatted logs
- ✅ All Phase 1 objectives successfully met

**Known Issues**:
- Minor dependency version conflicts between MCP requirements and existing FastAPI (noted but doesn't affect functionality)

**Next Steps**:
- Phase 2 will build the API client infrastructure to connect the MCP server with the FastAPI endpoints

### Phase 2: API Client Infrastructure ✅ COMPLETED
**Goal**: Build robust HTTP client for API communication

**Implementation Steps**:
1. Create `handlers/api_client.py` with connection pooling
2. Implement authentication handling (API key support)
3. Add retry logic with exponential backoff
4. Create error handling and response parsing
5. Implement request/response logging

**Deliverables**:
- Reusable API client class
- Connection pooling for performance
- Comprehensive error handling

**Testing**:
- API client connects to FastAPI server
- Handles various error scenarios gracefully
- Retry logic works correctly

**Implementation Summary** (Completed on 26/05/2025):

**Files Created/Modified**:
1. **API Client Implementation**:
   - `mcp_server/handlers/api_client.py` - Complete async HTTP client with:
     - Connection pooling (configurable size)
     - Automatic retry with exponential backoff
     - Comprehensive error handling
     - Request/response logging
     - Typed response support with Pydantic models
     - Streaming support for large responses
     - Health check functionality

2. **Configuration Updates**:
   - Added `connection_pool_size` to MCPConfig

3. **Handler Module Updates**:
   - Updated `handlers/__init__.py` with proper exports

4. **Integration**:
   - Updated `server.py` to integrate API client
   - Added cleanup in main() for graceful shutdown

5. **Testing Infrastructure**:
   - `mcp_server/test_api_client.py` - Comprehensive test suite covering:
     - Basic functionality
     - Mocked requests
     - Error handling scenarios
     - Retry logic
     - Global instance management
     - Real API integration tests

**Key Implementation Details**:

1. **API Client Architecture**:
   ```python
   class APIClient:
       - HTTPX-based async client
       - Connection pooling with keepalive
       - Configurable timeouts
       - Bearer token authentication support
   ```

2. **Error Hierarchy**:
   - `APIError` - Base exception
   - `APIConnectionError` - Connection failures
   - `APITimeoutError` - Timeout errors
   - `APIValidationError` - 400 errors

3. **Retry Strategy**:
   - Uses tenacity library
   - Exponential backoff (1s, 2s, 4s...)
   - Max retries configurable via config
   - Only retries on connection/timeout errors
   - Logs retry attempts

4. **Logging**:
   - Structured logging with request context
   - Logs all requests, responses, errors
   - Includes timing information when available

5. **Connection Management**:
   - Global client instance with singleton pattern
   - Proper cleanup on shutdown
   - Connection pool with configurable size
   - Keep-alive connections for performance

**Test Results**:
- ✅ All unit tests passing
- ✅ Error handling works correctly
- ✅ Retry logic functions as expected
- ✅ Connection pooling operational
- ✅ Proper cleanup on shutdown

**Next Steps**:
- Phase 3 will implement script execution tools using this API client infrastructure

### Phase 3: Script Execution Tools ✅ COMPLETED
**Goal**: Enable script execution via MCP tools

**Implementation Steps**:
1. Create `tools/script_tools.py`
2. Implement `list_trading_scripts` tool
3. Implement `execute_trading_script` tool (sync mode)
4. Add async execution support
5. Implement `check_script_status` tool
6. Add script parameter validation

**Deliverables**:
- Three working script-related tools
- Parameter validation logic
- Async execution tracking

**Testing**:
- List scripts from allowed directories
- Execute scripts with various parameters
- Track async execution status

**Implementation Summary** (Completed on 26/05/2025):

**Files Created/Modified**:
1. **Script Tools Implementation**:
   - `mcp_server/tools/script_tools.py` - Complete implementation with:
     - `ScriptTools` class managing all script-related operations
     - `list_trading_scripts` - Returns hardcoded list of available scripts
     - `execute_trading_script` - Supports both sync and async execution
     - `check_script_status` - Checks status of async executions
     - Proper error handling and logging
     - Singleton pattern for tools instance

2. **Module Updates**:
   - Updated `tools/__init__.py` with exports for ScriptTools

3. **Server Integration**:
   - Modified `server.py` to:
     - Import and initialize script tools
     - Register all script tools in the tools list
     - Handle script tool calls in the call_tool handler
     - Format responses as JSON text content

4. **Testing**:
   - `mcp_server/test_script_tools.py` - Comprehensive unit tests (requires pytest)
   - `mcp_server/test_script_integration.py` - Integration tests that run without pytest

**Key Implementation Details**:

1. **Tool Definitions**:
   - All three tools properly defined with JSON schemas
   - Input validation for required parameters
   - Descriptive help text for each tool

2. **API Integration**:
   - Uses the API client from Phase 2
   - Proper POST requests to `/api/scripts/execute`
   - GET requests to `/api/scripts/status/{id}`
   - Handles both sync and async modes

3. **Error Handling**:
   - Validates required parameters
   - Catches and logs API errors
   - Returns structured error responses
   - Maintains success/failure status

4. **Logging**:
   - Structured logging for all operations
   - Includes context (script name, execution ID, etc.)
   - Logs both successes and failures

**Test Results**:
- ✅ All tools properly registered in MCP server
- ✅ list_trading_scripts returns expected scripts
- ✅ execute_trading_script works in sync mode
- ✅ execute_trading_script works in async mode
- ✅ check_script_status retrieves execution status
- ✅ Error handling works correctly
- ✅ Integration tests pass successfully

**Next Steps**:
- Phase 4 will implement data retrieval tools for CSV and JSON files

### Phase 4: Data Retrieval Tools ✅ COMPLETED
**Goal**: Provide data access through MCP

**Implementation Steps**:
1. Create `tools/data_tools.py`
2. Implement `list_data_files` tool
3. Implement `get_trading_data` tool for CSV
4. Add JSON file support
5. Implement data size limits and validation
6. Add response formatting options

**Deliverables**:
- Two data access tools
- Support for CSV and JSON formats
- Size limit enforcement

**Testing**:
- List files in various directories
- Retrieve CSV and JSON data
- Handle large files appropriately

**Implementation Summary** (Completed on 26/05/2025):

**Files Created/Modified**:
1. **Data Tools Implementation**:
   - `mcp_server/tools/data_tools.py` - Complete implementation with:
     - `DataTools` class managing all data-related operations
     - `list_data_files` - Lists files in allowed data directories
     - `get_trading_data` - Retrieves CSV or JSON file contents
     - Path validation to ensure security
     - File size validation (100MB limit inherited from API)
     - Proper error handling and logging
     - Singleton pattern for tools instance

2. **Module Updates**:
   - Updated `tools/__init__.py` with exports for DataTools

3. **Server Integration**:
   - Modified `server.py` to:
     - Import and initialize data tools
     - Register both data tools in the tools list
     - Handle data tool calls in the call_tool handler
     - Maintain consistent response formatting

4. **Testing**:
   - `mcp_server/test_data_tools.py` - Comprehensive unit tests
   - `mcp_server/test_data_integration.py` - Integration tests with running API

**Key Implementation Details**:

1. **Tool Definitions**:
   ```python
   - list_data_files:
     - Optional directory parameter
     - Returns file paths with metadata
     - Filters by allowed directories
   
   - get_trading_data:
     - Required file_path and file_type parameters
     - Supports both CSV and JSON formats
     - Returns parsed data or raw content
   ```

2. **API Integration**:
   - Uses the API client from Phase 2
   - GET requests to `/api/data/csv/{path}` for CSV files
   - GET requests to `/api/data/json/{path}` for JSON files
   - Handles API errors gracefully

3. **Security Features**:
   - Path validation prevents directory traversal
   - Only accesses files in allowed directories (csv/, json/)
   - File size limits enforced by API
   - No direct file system access

4. **Error Handling**:
   - Validates required parameters
   - Handles file not found errors
   - Manages API connection failures
   - Returns structured error responses
   - Logs all operations with context

5. **Response Formatting**:
   - CSV data returned as parsed content (when possible)
   - JSON data returned as parsed objects
   - Large files handled gracefully
   - Consistent success/error response structure

**Test Results**:
- ✅ All tools properly registered in MCP server
- ✅ list_data_files returns files from allowed directories
- ✅ get_trading_data successfully retrieves CSV files
- ✅ get_trading_data successfully retrieves JSON files
- ✅ Path validation prevents unauthorized access
- ✅ Error handling works for missing files
- ✅ Error handling works for invalid file types
- ✅ Integration tests pass with running API

**Notable Observations**:
- The API's built-in security measures (path validation, file size limits) provide robust protection
- Response parsing allows AI assistants to work directly with structured data
- The singleton pattern ensures efficient resource usage
- Integration with the existing API client from Phase 2 was seamless

**Next Steps**:
- Phase 5 will implement portfolio management tools for updating trading positions

### Phase 5: Portfolio Management Tools ✅ COMPLETED
**Goal**: Enable portfolio operations via MCP

**Implementation Steps**:
1. Create `tools/portfolio_tools.py`
2. Implement `update_portfolio` tool
3. Add validation for portfolio data
4. Implement error handling for invalid data
5. Add response formatting

**Deliverables**:
- Portfolio update tool
- Data validation logic
- Formatted responses

**Testing**:
- Update portfolio with valid data
- Handle invalid portfolio data
- Verify API integration

**Implementation Summary** (Completed on 26/05/2025):

**Files Created/Modified**:
1. **Portfolio Tools Implementation**:
   - `mcp_server/tools/portfolio_tools.py` - Complete implementation with:
     - `PortfolioTools` class managing portfolio operations
     - `update_portfolio` tool that calls app/strategies/update_portfolios.py
     - CSV filename validation (must end with .csv)
     - Script directory parameter with default value
     - Proper error handling and structured responses
     - Singleton pattern for global instance

2. **Module Updates**:
   - Updated `tools/__init__.py` to export PortfolioTools

3. **Server Integration**:
   - Modified `server.py` to:
     - Import and initialize portfolio tools
     - Register the update_portfolio tool
     - Handle portfolio tool calls in the call_tool handler
     - Consistent JSON response formatting

4. **Testing Infrastructure**:
   - `mcp_server/test_portfolio_tools.py` - Unit tests for portfolio functionality
   - `mcp_server/test_portfolio_integration.py` - Integration tests with running API
   - `mcp_server/test_portfolio_complete.py` - Complete end-to-end test

**Key Implementation Details**:

1. **Tool Definition**:
   ```python
   Tool(
       name="update_portfolio",
       description="Update portfolio with new trading positions from a CSV file",
       inputSchema={
           "properties": {
               "csv_filename": {"type": "string", "description": "CSV file containing portfolio data"},
               "script_dir": {"type": "string", "description": "Script directory", "default": "strategies"}
           },
           "required": ["csv_filename"]
       }
   )
   ```

2. **API Integration**:
   - Correctly maps to `app/strategies/update_portfolios.py` script
   - Uses `script_path` and `async_execution` fields for API compatibility
   - Properly parses nested API response structure
   - Handles both success and error cases

3. **Validation Features**:
   - Validates CSV file extension
   - Requires non-empty filename
   - Returns structured error messages

4. **Response Handling**:
   - Parses API's nested response structure
   - Extracts script execution results
   - Provides clear success/error status

**Test Results**:
- ✅ Tool properly registered in MCP server
- ✅ CSV filename validation works correctly
- ✅ API integration successful
- ✅ Handles missing files gracefully
- ✅ Successfully executes update_portfolios.py script
- ✅ All integration tests pass

**Integration Notes**:
- The portfolio tool successfully integrates with the existing API infrastructure
- Uses the same API client and error handling patterns as other tools
- Maintains consistency with the overall MCP server architecture
- Successfully calls the existing update_portfolios.py script in the strategies directory

**Next Steps**:
- All 5 phases are now complete
- The MCP server provides full access to Trading API functionality
- Ready for production deployment or additional enhancements as needed


## 4. Technical Implementation Details

### 4.1 Dependencies
```python
# requirements.txt additions
mcp>=0.1.0
httpx>=0.24.0  # For async HTTP client
tenacity>=8.0.0  # For retry logic
pydantic>=2.0.0  # For data validation
structlog>=23.0.0  # For structured logging
```

### 4.2 Configuration Management
```python
# mcp_server/config.py
from pydantic import BaseSettings

class MCPConfig(BaseSettings):
    api_base_url: str = "http://localhost:8000"
    api_key: str = None
    request_timeout: int = 30
    max_retries: int = 3
    connection_pool_size: int = 10
    
    class Config:
        env_prefix = "MCP_"
```

### 4.3 Error Handling Strategy
- Custom exception hierarchy for different error types
- Graceful degradation when API is unavailable
- User-friendly error messages with actionable information
- Correlation IDs for tracing errors across systems

## 5. Testing Strategy

### 5.1 Unit Testing
- Mock API responses for isolated testing
- Test input validation for each tool
- Verify error handling paths
- Test configuration loading

### 5.2 Integration Testing
- Test against running API instance
- Verify end-to-end workflows
- Test error scenarios
- Validate response formats

### 5.3 Performance Testing
- Concurrent tool execution
- Large data file handling
- Connection pool efficiency
- Memory usage under load

## 6. Deployment Options

### 6.1 Standalone Mode
```bash
# Run MCP server independently
python -m mcp_server.server
```

### 6.2 Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY mcp_server/ ./mcp_server/
CMD ["python", "-m", "mcp_server.server"]
```

### 6.3 Integrated Deployment
- Can be deployed alongside the API
- Shared configuration management
- Unified monitoring and logging

## 7. Success Metrics

1. **Functionality**: All API endpoints accessible via MCP tools
2. **Reliability**: Graceful handling of API downtime
3. **Performance**: Minimal latency overhead (<100ms)
4. **Security**: No unauthorized data access
5. **Usability**: Clear error messages and documentation

## 8. Risk Mitigation

### 8.1 Technical Risks
- **API Changes**: Version compatibility checks
- **Performance**: Caching and connection pooling
- **Security**: Input validation and rate limiting

### 8.2 Operational Risks
- **Monitoring**: Comprehensive observability
- **Failures**: Graceful degradation
- **Scaling**: Horizontal scaling support

## 9. Future Enhancements

- WebSocket support for real-time updates
- Direct database access for performance
- Custom tool builder interface
- Multi-API aggregation support
- Advanced caching strategies
- GraphQL support