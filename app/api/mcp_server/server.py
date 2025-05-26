"""Main MCP Server implementation for Trading API"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, 
    TextContent, 
    CallToolResult,
    CallToolRequest,
    ListToolsRequest
)
from pydantic import BaseModel, Field

from .config import config
from .logging_setup import setup_logging, get_logger
from .handlers import get_api_client, cleanup_api_client
from .tools import get_script_tools, get_data_tools, get_portfolio_tools

# Setup logging
setup_logging()
logger = get_logger(__name__)


class HelloWorldArgs(BaseModel):
    """Arguments for the hello_world test tool"""
    message: str = Field(description="Message to echo back")


class TradingAPIMCPServer:
    """MCP Server for Trading API integration"""
    
    def __init__(self):
        self.server = Server(config.server_name)
        self.api_client = get_api_client()
        self.script_tools = get_script_tools()
        self.data_tools = get_data_tools()
        self.portfolio_tools = get_portfolio_tools()
        self._setup_tools()
        
    def _setup_tools(self):
        """Register all available tools"""
        logger.info("Setting up MCP tools")
        
        # Define available tools
        self.tools = [
            Tool(
                name="hello_world",
                description="Test tool to verify MCP server functionality. Echoes back the provided message.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo back"
                        }
                    },
                    "required": ["message"]
                }
            )
        ]
        
        # Add script tools
        self.tools.extend(self.script_tools.get_tools())
        
        # Add data tools
        self.tools.extend(self.data_tools.get_tools())
        
        # Add portfolio tools
        self.tools.extend(self.portfolio_tools.tools)
        
        # Register list tools handler
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return self.tools
        
        # Register call tool handler
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> List[TextContent]:
            if name == "hello_world":
                message = arguments.get("message", "")
                logger.info("hello_world called", message=message)
                return [
                    TextContent(
                        type="text",
                        text=f"Hello from Trading API MCP Server! You said: {message}"
                    )
                ]
            elif name == "list_trading_scripts":
                result = await self.script_tools.list_trading_scripts(arguments)
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )
                ]
            elif name == "execute_trading_script":
                result = await self.script_tools.execute_trading_script(arguments)
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )
                ]
            elif name == "check_script_status":
                result = await self.script_tools.check_script_status(arguments)
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )
                ]
            elif name == "list_data_files":
                directory = arguments.get("directory", "")
                result = await self.data_tools.list_data_files(directory)
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )
                ]
            elif name == "get_trading_data":
                file_path = arguments.get("file_path")
                file_type = arguments.get("file_type")
                result = await self.data_tools.get_trading_data(file_path, file_type)
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )
                ]
            elif name == "update_portfolio":
                result = await self.portfolio_tools.handle_tool_call(name, arguments)
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )
                ]
            else:
                raise ValueError(f"Unknown tool: {name}")
        
        logger.info("MCP tools setup completed")
    
    async def start(self):
        """Start the MCP server"""
        logger.info("Starting MCP server", 
                   server_name=config.server_name, 
                   version=config.server_version,
                   api_endpoint=config.api_base_url)
        
        # Run the stdio server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    try:
        server = TradingAPIMCPServer()
        await server.start()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error("Server error", error=str(e), exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup resources
        await cleanup_api_client()


if __name__ == "__main__":
    asyncio.run(main())