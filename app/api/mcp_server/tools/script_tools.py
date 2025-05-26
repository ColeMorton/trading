"""
Script execution tools for the Trading API MCP server.

This module provides MCP tools for listing, executing, and monitoring
trading scripts through the Trading API.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from mcp.types import Tool
import structlog

from ..handlers import get_api_client
from ..config import config

logger = structlog.get_logger(__name__)


class ScriptTools:
    """Container for script-related MCP tools."""
    
    def __init__(self):
        """Initialize script tools."""
        self.api_client = get_api_client()
        logger.info("Script tools initialized")
    
    def get_tools(self) -> List[Tool]:
        """Get all script-related tools."""
        return [
            self._list_trading_scripts_tool(),
            self._execute_trading_script_tool(),
            self._check_script_status_tool()
        ]
    
    def _list_trading_scripts_tool(self) -> Tool:
        """Create the list_trading_scripts tool."""
        return Tool(
            name="list_trading_scripts",
            description="List all available trading scripts in allowed directories",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    
    def _execute_trading_script_tool(self) -> Tool:
        """Create the execute_trading_script tool."""
        return Tool(
            name="execute_trading_script",
            description="Execute a trading script from allowed directories",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_name": {
                        "type": "string",
                        "description": "Name of the script to execute (e.g., 'ma_cross/optimize.py')"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Script parameters as key-value pairs",
                        "additionalProperties": True
                    },
                    "async_mode": {
                        "type": "boolean",
                        "description": "Execute asynchronously (returns execution ID)",
                        "default": False
                    }
                },
                "required": ["script_name"]
            }
        )
    
    def _check_script_status_tool(self) -> Tool:
        """Create the check_script_status tool."""
        return Tool(
            name="check_script_status",
            description="Check the status of an asynchronously executing script",
            inputSchema={
                "type": "object",
                "properties": {
                    "execution_id": {
                        "type": "string",
                        "description": "Execution ID from async execution"
                    }
                },
                "required": ["execution_id"]
            }
        )
    
    async def list_trading_scripts(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        List all available trading scripts.
        
        This tool discovers scripts in the allowed directories:
        - app/ma_cross
        - app/concurrency
        - app/strategies
        
        Args:
            arguments: Empty dict (no arguments needed)
        
        Returns:
            Dict containing list of available scripts with metadata
        """
        try:
            logger.info("Listing trading scripts")
            
            # Get list of scripts from the API
            # Since the API doesn't have a dedicated endpoint for listing scripts,
            # we'll need to discover them from the file system
            # In a real implementation, this might query the API or use a predefined list
            
            # For now, return a hardcoded list based on known scripts
            # In production, this would query the API or file system
            scripts = [
                {
                    "name": "app/ma_cross/optimize.py",
                    "description": "Moving average crossover optimization",
                    "directory": "app/ma_cross",
                    "parameters": {
                        "strategy": "Strategy name (e.g., 'DAILY', 'INTRADAY', 'LONG')",
                        "optimize": "Whether to run optimization (true/false)"
                    }
                },
                {
                    "name": "app/ma_cross/run.py",
                    "description": "Run moving average crossover strategy",
                    "directory": "app/ma_cross",
                    "parameters": {
                        "strategy": "Strategy name"
                    }
                },
                {
                    "name": "app/strategies/backtest.py",
                    "description": "Run strategy backtests",
                    "directory": "app/strategies",
                    "parameters": {
                        "strategy_file": "Path to strategy CSV file",
                        "start_date": "Start date for backtest",
                        "end_date": "End date for backtest"
                    }
                },
                {
                    "name": "app/strategies/update_portfolios.py",
                    "description": "Update portfolio positions from CSV file",
                    "directory": "app/strategies",
                    "parameters": {
                        "csv_filename": "Name of the CSV file containing portfolio data",
                        "script_dir": "Script directory (default: 'strategies')"
                    }
                }
            ]
            
            logger.info("Found scripts", count=len(scripts))
            
            return {
                "success": True,
                "scripts": scripts,
                "total": len(scripts)
            }
            
        except Exception as e:
            logger.error("Failed to list scripts", error=str(e))
            return {
                "success": False,
                "error": f"Failed to list scripts: {str(e)}"
            }
    
    async def execute_trading_script(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trading script.
        
        Args:
            arguments: Dict containing:
                - script_name: Name of the script to execute
                - parameters: Optional dict of script parameters
                - async_mode: Whether to execute asynchronously
        
        Returns:
            Dict containing execution result or execution ID for async mode
        """
        script_name = arguments.get("script_name")
        parameters = arguments.get("parameters", {})
        async_mode = arguments.get("async_mode", False)
        
        if not script_name:
            return {
                "success": False,
                "error": "script_name is required"
            }
        
        try:
            logger.info(
                "Executing script",
                script=script_name,
                async_mode=async_mode,
                parameters=parameters
            )
            
            # Prepare the request payload
            payload = {
                "script_path": script_name,  # API expects script_path
                "parameters": parameters,
                "async_execution": async_mode  # API expects async_execution
            }
            
            # Call the API
            response = await self.api_client.post("/api/scripts/execute", json=payload)
            
            if async_mode and "execution_id" in response:
                logger.info(
                    "Script execution started",
                    script=script_name,
                    execution_id=response["execution_id"]
                )
                return {
                    "success": True,
                    "execution_id": response["execution_id"],
                    "message": f"Script '{script_name}' started executing asynchronously"
                }
            else:
                logger.info("Script executed successfully", script=script_name)
                return {
                    "success": True,
                    "result": response.get("result"),
                    "output": response.get("output"),
                    "message": f"Script '{script_name}' executed successfully"
                }
                
        except Exception as e:
            logger.error(
                "Failed to execute script",
                script=script_name,
                error=str(e)
            )
            return {
                "success": False,
                "error": f"Failed to execute script '{script_name}': {str(e)}"
            }
    
    async def check_script_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check the status of an async script execution.
        
        Args:
            arguments: Dict containing:
                - execution_id: ID of the execution to check
        
        Returns:
            Dict containing execution status and results if available
        """
        execution_id = arguments.get("execution_id")
        
        if not execution_id:
            return {
                "success": False,
                "error": "execution_id is required"
            }
        
        try:
            logger.info("Checking script status", execution_id=execution_id)
            
            # Call the API
            response = await self.api_client.get(f"/api/scripts/status/{execution_id}")
            
            status = response.get("status", "unknown")
            logger.info(
                "Script status retrieved",
                execution_id=execution_id,
                status=status
            )
            
            result = {
                "success": True,
                "execution_id": execution_id,
                "status": status
            }
            
            # Include additional fields based on status
            if status == "completed":
                result["result"] = response.get("result")
                result["output"] = response.get("output")
                result["completed_at"] = response.get("completed_at")
            elif status == "failed":
                result["error"] = response.get("error")
                result["failed_at"] = response.get("failed_at")
            elif status == "running":
                result["started_at"] = response.get("started_at")
                result["progress"] = response.get("progress")
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to check script status",
                execution_id=execution_id,
                error=str(e)
            )
            return {
                "success": False,
                "error": f"Failed to check status for execution '{execution_id}': {str(e)}"
            }


# Module-level instance
_script_tools: Optional[ScriptTools] = None


def get_script_tools() -> ScriptTools:
    """Get or create the script tools instance."""
    global _script_tools
    if _script_tools is None:
        _script_tools = ScriptTools()
    return _script_tools