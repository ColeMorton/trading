"""
Portfolio management tools for MCP server.
"""

from typing import Dict, Any, List, Optional
import structlog
from mcp import Tool

from ..handlers.api_client import get_api_client, APIError
from ..config import config

logger = structlog.get_logger(__name__)


class PortfolioTools:
    """Manages portfolio-related MCP tools."""
    
    def __init__(self):
        self.config = config
        self.api_client = get_api_client()
        self.tools = self._create_tools()
        logger.info("PortfolioTools initialized", tool_count=len(self.tools))
    
    def _create_tools(self) -> List[Tool]:
        """Create portfolio management tools."""
        return [
            Tool(
                name="update_portfolio",
                description="Update portfolio with new trading positions from a CSV file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "csv_filename": {
                            "type": "string",
                            "description": "CSV file containing portfolio data (e.g., 'positions.csv')"
                        },
                        "script_dir": {
                            "type": "string",
                            "description": "Script directory (default: 'strategies')",
                            "default": "strategies"
                        }
                    },
                    "required": ["csv_filename"]
                }
            )
        ]
    
    async def update_portfolio(self, csv_filename: str, script_dir: str = "strategies") -> Dict[str, Any]:
        """
        Update portfolio with new trading data.
        
        Args:
            csv_filename: Name of the CSV file containing portfolio data
            script_dir: Directory containing the script (default: "strategies")
            
        Returns:
            Dict containing update results or error information
        """
        logger.info("Updating portfolio", csv_filename=csv_filename, script_dir=script_dir)
        
        # Validate inputs
        if not csv_filename:
            error_msg = "csv_filename is required"
            logger.error("Portfolio update failed", error=error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
        
        # Validate csv_filename format
        if not csv_filename.endswith('.csv'):
            error_msg = "csv_filename must be a CSV file (end with .csv)"
            logger.error("Portfolio update failed", error=error_msg)
            return {
                "status": "error", 
                "error": error_msg
            }
        
        try:
            # Call the update_portfolios script
            # Note: The script is in app/strategies/update_portfolios.py
            response = await self.api_client.post(
                "/api/scripts/execute",
                json={
                    "script_path": "app/strategies/update_portfolios.py",
                    "parameters": {
                        "csv_filename": csv_filename,
                        "script_dir": script_dir
                    },
                    "async_execution": False  # Portfolio updates should be synchronous
                }
            )
            
            logger.info("Portfolio update successful", 
                       csv_filename=csv_filename,
                       response_status=response.get("status"))
            
            # Extract the result from the response
            # The API returns a 'success' status for synchronous execution
            if response.get("status") == "success" and response.get("result"):
                result = response.get("result", {})
                if result.get("success"):
                    return {
                        "status": "success",
                        "message": f"Portfolio updated successfully from {csv_filename}",
                        "result": result.get("data"),
                        "execution_time": result.get("execution_time")
                    }
                else:
                    # Script executed but returned an error
                    return {
                        "status": "error",
                        "error": result.get("message", "Portfolio update failed"),
                        "details": result
                    }
            else:
                return {
                    "status": "error",
                    "error": response.get("error", "Portfolio update failed"),
                    "details": response
                }
                
        except APIError as e:
            logger.error("API error during portfolio update", 
                        error=str(e),
                        csv_filename=csv_filename)
            return {
                "status": "error",
                "error": f"API error: {str(e)}"
            }
        except Exception as e:
            logger.exception("Unexpected error during portfolio update", 
                            csv_filename=csv_filename)
            return {
                "status": "error",
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a tool call by name.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if name == "update_portfolio":
            return await self.update_portfolio(
                csv_filename=arguments.get("csv_filename", ""),
                script_dir=arguments.get("script_dir", "strategies")
            )
        else:
            logger.error("Unknown portfolio tool", tool_name=name)
            return {
                "status": "error",
                "error": f"Unknown portfolio tool: {name}"
            }


# Global instance
_portfolio_tools = None


def get_portfolio_tools() -> PortfolioTools:
    """Get or create the global PortfolioTools instance."""
    global _portfolio_tools
    if _portfolio_tools is None:
        _portfolio_tools = PortfolioTools()
    return _portfolio_tools