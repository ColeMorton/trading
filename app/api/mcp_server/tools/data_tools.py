"""
Data retrieval tools for the Trading API MCP server.

Provides tools for listing and retrieving trading data files (CSV and JSON).
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import json

from mcp.types import Tool

from ..handlers.api_client import get_api_client, APIError
from ..logging_setup import get_logger
from ..config import config

logger = get_logger(__name__)


class DataTools:
    """Manages data retrieval tools for the MCP server."""
    
    def __init__(self):
        """Initialize data tools."""
        self.client = get_api_client()
        logger.info("DataTools initialized")
    
    def get_tools(self) -> List[Tool]:
        """Return the list of data-related tools."""
        return [
            Tool(
                name="list_data_files",
                description="List data files in allowed directories",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory to list files from (e.g., 'csv', 'json'). Defaults to listing all allowed directories.",
                            "default": ""
                        }
                    }
                }
            ),
            Tool(
                name="get_trading_data",
                description="Retrieve trading data from CSV or JSON files",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the data file (relative to project root)"
                        },
                        "file_type": {
                            "type": "string",
                            "enum": ["csv", "json"],
                            "description": "Type of data file"
                        }
                    },
                    "required": ["file_path", "file_type"]
                }
            )
        ]
    
    async def list_data_files(self, directory: str = "") -> Dict[str, Any]:
        """
        List available data files in allowed directories.
        
        Args:
            directory: Specific directory to list files from (e.g., 'csv', 'json').
                      If empty, lists files from all allowed directories.
        
        Returns:
            Dictionary containing list of files and metadata
        """
        try:
            logger.info("Listing data files", directory=directory)
            
            # For now, return a hardcoded list of allowed directories and sample files
            # In a real implementation, this would query the API or filesystem
            result = {
                "success": True,
                "directories": {},
                "total_files": 0
            }
            
            # Define allowed directories
            allowed_dirs = ["csv", "json"]
            
            # Filter directories based on input
            if directory:
                if directory not in allowed_dirs:
                    return {
                        "success": False,
                        "error": f"Directory '{directory}' is not in allowed list: {allowed_dirs}"
                    }
                dirs_to_list = [directory]
            else:
                dirs_to_list = allowed_dirs
            
            # Mock file listings for each directory
            mock_files = {
                "csv": [
                    {"name": "strategies/DAILY.csv", "size": 15420, "modified": "2025-05-26T10:30:00"},
                    {"name": "backtest_results.csv", "size": 8943, "modified": "2025-05-25T14:22:00"},
                    {"name": "portfolio_history.csv", "size": 23156, "modified": "2025-05-24T09:15:00"}
                ],
                "json": [
                    {"name": "config/trading_params.json", "size": 1245, "modified": "2025-05-20T08:00:00"},
                    {"name": "market_data.json", "size": 45782, "modified": "2025-05-26T11:00:00"}
                ]
            }
            
            # Build response
            for dir_name in dirs_to_list:
                files = mock_files.get(dir_name, [])
                result["directories"][dir_name] = {
                    "path": dir_name,
                    "file_count": len(files),
                    "files": files
                }
                result["total_files"] += len(files)
            
            logger.info("Listed data files successfully", 
                       directories_count=len(result["directories"]),
                       total_files=result["total_files"])
            
            return result
            
        except Exception as e:
            logger.error("Failed to list data files", error=str(e), directory=directory)
            return {
                "success": False,
                "error": f"Failed to list data files: {str(e)}"
            }
    
    async def get_trading_data(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        Retrieve trading data from a CSV or JSON file.
        
        Args:
            file_path: Path to the data file (relative to project root)
            file_type: Type of file ('csv' or 'json')
        
        Returns:
            Dictionary containing the file data or error information
        """
        try:
            logger.info("Retrieving trading data", file_path=file_path, file_type=file_type)
            
            # Validate file type
            if file_type not in ["csv", "json"]:
                return {
                    "success": False,
                    "error": f"Invalid file type: {file_type}. Must be 'csv' or 'json'"
                }
            
            # Call the appropriate API endpoint
            endpoint = f"/api/data/{file_type}/{file_path}"
            
            try:
                response = await self.client.get(endpoint)
                
                # Format response based on file type
                result = {
                    "success": True,
                    "file_path": file_path,
                    "file_type": file_type,
                    "data": response
                }
                
                # Add metadata if available
                if isinstance(response, dict):
                    if "size" in response:
                        result["size"] = response["size"]
                    if "rows" in response:
                        result["rows"] = response["rows"]
                    if "columns" in response:
                        result["columns"] = response["columns"]
                
                logger.info("Retrieved trading data successfully", 
                           file_path=file_path,
                           file_type=file_type)
                
                return result
                
            except APIError as e:
                logger.error("API error retrieving data", 
                            error=str(e),
                            file_path=file_path,
                            status_code=getattr(e, 'status_code', None))
                
                # Provide helpful error messages
                error_msg = str(e)
                if "404" in error_msg:
                    error_msg = f"File not found: {file_path}"
                elif "403" in error_msg:
                    error_msg = f"Access denied: {file_path} is not in an allowed directory"
                elif "413" in error_msg:
                    error_msg = f"File too large: {file_path} exceeds the 100MB limit"
                
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except Exception as e:
            logger.error("Failed to retrieve trading data", 
                        error=str(e),
                        file_path=file_path,
                        file_type=file_type)
            return {
                "success": False,
                "error": f"Failed to retrieve data: {str(e)}"
            }


# Global instance
_data_tools = None


def get_data_tools() -> DataTools:
    """Get or create the global DataTools instance."""
    global _data_tools
    if _data_tools is None:
        _data_tools = DataTools()
    return _data_tools