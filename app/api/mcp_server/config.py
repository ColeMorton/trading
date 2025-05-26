"""Configuration management for MCP Server"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class MCPConfig(BaseSettings):
    """MCP Server configuration settings"""
    
    # API connection settings
    api_base_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    
    # Request settings
    request_timeout: int = 30
    max_retries: int = 3
    connection_pool_size: int = 10
    
    # MCP server settings
    server_name: str = "trading-api-mcp"
    server_version: str = "0.1.0"
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    class Config:
        env_prefix = "MCP_"
        env_file = ".env"


# Global config instance
config = MCPConfig()