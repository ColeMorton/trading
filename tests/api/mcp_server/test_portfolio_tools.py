"""
Unit tests for portfolio tools.
"""

import asyncio
import os

# Import directly for testing
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.api.mcp_server.tools.portfolio_tools import PortfolioTools, get_portfolio_tools


class TestPortfolioTools:
    """Test PortfolioTools class"""

    @pytest.fixture
    def portfolio_tools(self):
        """Create PortfolioTools instance for testing"""
        with patch("app.api.mcp_server.tools.portfolio_tools.get_api_client"):
            return PortfolioTools()

    def test_tool_creation(self, portfolio_tools):
        """Test that tools are created correctly"""
        tools = portfolio_tools.tools
        assert len(tools) == 1

        # Check update_portfolio tool
        tool = tools[0]
        assert tool.name == "update_portfolio"
        assert "Update portfolio" in tool.description
        assert "csv_filename" in tool.inputSchema["properties"]
        assert "script_dir" in tool.inputSchema["properties"]
        assert tool.inputSchema["required"] == ["csv_filename"]

    @pytest.mark.asyncio
    async def test_update_portfolio_success(self, portfolio_tools):
        """Test successful portfolio update"""
        # Mock API response
        mock_response = {
            "status": "completed",
            "result": {"positions_updated": 5},
            "execution_time": 1.23,
        }

        portfolio_tools.api_client.post = AsyncMock(return_value=mock_response)

        result = await portfolio_tools.update_portfolio("positions.csv", "strategies")

        assert result["status"] == "success"
        assert "Portfolio updated successfully" in result["message"]
        assert result["result"] == {"positions_updated": 5}
        assert result["execution_time"] == 1.23

        # Verify API call
        portfolio_tools.api_client.post.assert_called_once_with(
            "/api/scripts/execute",
            json={
                "script_name": "update_portfolio",
                "parameters": {
                    "csv_filename": "positions.csv",
                    "script_dir": "strategies",
                },
                "async": False,
            },
        )

    @pytest.mark.asyncio
    async def test_update_portfolio_missing_filename(self, portfolio_tools):
        """Test portfolio update with missing filename"""
        result = await portfolio_tools.update_portfolio("")

        assert result["status"] == "error"
        assert "csv_filename is required" in result["error"]

    @pytest.mark.asyncio
    async def test_update_portfolio_invalid_extension(self, portfolio_tools):
        """Test portfolio update with invalid file extension"""
        result = await portfolio_tools.update_portfolio("positions.txt")

        assert result["status"] == "error"
        assert "must be a CSV file" in result["error"]

    @pytest.mark.asyncio
    async def test_update_portfolio_api_error(self, portfolio_tools):
        """Test portfolio update with API error"""
        from app.api.mcp_server.handlers.api_client import APIError

        portfolio_tools.api_client.post = AsyncMock(
            side_effect=APIError("Connection failed")
        )

        result = await portfolio_tools.update_portfolio("positions.csv")

        assert result["status"] == "error"
        assert "API error: Connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_update_portfolio_execution_error(self, portfolio_tools):
        """Test portfolio update with execution error"""
        mock_response = {"status": "error", "error": "File not found"}

        portfolio_tools.api_client.post = AsyncMock(return_value=mock_response)

        result = await portfolio_tools.update_portfolio("missing.csv")

        assert result["status"] == "error"
        assert result["error"] == "File not found"

    @pytest.mark.asyncio
    async def test_handle_tool_call_update_portfolio(self, portfolio_tools):
        """Test handle_tool_call for update_portfolio"""
        portfolio_tools.update_portfolio = AsyncMock(return_value={"status": "success"})

        result = await portfolio_tools.handle_tool_call(
            "update_portfolio", {"csv_filename": "test.csv", "script_dir": "strategies"}
        )

        assert result["status"] == "success"
        portfolio_tools.update_portfolio.assert_called_once_with(
            csv_filename="test.csv", script_dir="strategies"
        )

    @pytest.mark.asyncio
    async def test_handle_tool_call_unknown_tool(self, portfolio_tools):
        """Test handle_tool_call with unknown tool"""
        result = await portfolio_tools.handle_tool_call("unknown_tool", {})

        assert result["status"] == "error"
        assert "Unknown portfolio tool: unknown_tool" in result["error"]

    def test_get_portfolio_tools_singleton(self):
        """Test that get_portfolio_tools returns the same instance"""
        with patch("app.api.mcp_server.tools.portfolio_tools.get_api_client"):
            tools1 = get_portfolio_tools()
            tools2 = get_portfolio_tools()
            assert tools1 is tools2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
