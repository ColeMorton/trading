"""Test suite for script tools."""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch

from mcp_server.tools.script_tools import ScriptTools, get_script_tools


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = AsyncMock()
    return client


@pytest.fixture
def script_tools(mock_api_client):
    """Create script tools instance with mocked API client."""
    with patch("mcp_server.tools.script_tools.get_api_client", return_value=mock_api_client):
        tools = ScriptTools()
        return tools


class TestScriptTools:
    """Test cases for script tools."""
    
    def test_get_tools(self, script_tools):
        """Test that get_tools returns all expected tools."""
        tools = script_tools.get_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "list_trading_scripts" in tool_names
        assert "execute_trading_script" in tool_names
        assert "check_script_status" in tool_names
    
    def test_list_trading_scripts_tool_schema(self, script_tools):
        """Test list_trading_scripts tool schema."""
        tools = script_tools.get_tools()
        list_tool = next(t for t in tools if t.name == "list_trading_scripts")
        
        assert list_tool.description == "List all available trading scripts in allowed directories"
        assert list_tool.inputSchema["type"] == "object"
        assert list_tool.inputSchema["properties"] == {}
    
    def test_execute_trading_script_tool_schema(self, script_tools):
        """Test execute_trading_script tool schema."""
        tools = script_tools.get_tools()
        exec_tool = next(t for t in tools if t.name == "execute_trading_script")
        
        assert exec_tool.description == "Execute a trading script from allowed directories"
        assert exec_tool.inputSchema["type"] == "object"
        assert "script_name" in exec_tool.inputSchema["properties"]
        assert "parameters" in exec_tool.inputSchema["properties"]
        assert "async_mode" in exec_tool.inputSchema["properties"]
        assert exec_tool.inputSchema["required"] == ["script_name"]
    
    def test_check_script_status_tool_schema(self, script_tools):
        """Test check_script_status tool schema."""
        tools = script_tools.get_tools()
        status_tool = next(t for t in tools if t.name == "check_script_status")
        
        assert status_tool.description == "Check the status of an asynchronously executing script"
        assert status_tool.inputSchema["type"] == "object"
        assert "execution_id" in status_tool.inputSchema["properties"]
        assert status_tool.inputSchema["required"] == ["execution_id"]
    
    @pytest.mark.asyncio
    async def test_list_trading_scripts(self, script_tools):
        """Test listing trading scripts."""
        result = await script_tools.list_trading_scripts({})
        
        assert result["success"] is True
        assert "scripts" in result
        assert "total" in result
        assert isinstance(result["scripts"], list)
        assert result["total"] == len(result["scripts"])
        
        # Check that scripts have required fields
        for script in result["scripts"]:
            assert "name" in script
            assert "description" in script
            assert "directory" in script
            assert "parameters" in script
    
    @pytest.mark.asyncio
    async def test_execute_trading_script_sync(self, script_tools, mock_api_client):
        """Test executing a script synchronously."""
        # Mock API response
        mock_api_client.post.return_value = {
            "result": "success",
            "output": "Script completed"
        }
        
        arguments = {
            "script_name": "ma_cross/optimize.py",
            "parameters": {"strategy": "DAILY"},
            "async_mode": False
        }
        
        result = await script_tools.execute_trading_script(arguments)
        
        assert result["success"] is True
        assert result["result"] == "success"
        assert result["output"] == "Script completed"
        assert "Script 'ma_cross/optimize.py' executed successfully" in result["message"]
        
        # Verify API was called correctly
        mock_api_client.post.assert_called_once_with(
            "/api/scripts/execute",
            json={
                "script_name": "ma_cross/optimize.py",
                "parameters": {"strategy": "DAILY"},
                "async_mode": False
            }
        )
    
    @pytest.mark.asyncio
    async def test_execute_trading_script_async(self, script_tools, mock_api_client):
        """Test executing a script asynchronously."""
        # Mock API response
        mock_api_client.post.return_value = {
            "execution_id": "exec-12345"
        }
        
        arguments = {
            "script_name": "strategies/backtest.py",
            "parameters": {"strategy_file": "DAILY.csv"},
            "async_mode": True
        }
        
        result = await script_tools.execute_trading_script(arguments)
        
        assert result["success"] is True
        assert result["execution_id"] == "exec-12345"
        assert "Script 'strategies/backtest.py' started executing asynchronously" in result["message"]
    
    @pytest.mark.asyncio
    async def test_execute_trading_script_missing_name(self, script_tools):
        """Test executing a script without script_name."""
        arguments = {"parameters": {}}
        
        result = await script_tools.execute_trading_script(arguments)
        
        assert result["success"] is False
        assert result["error"] == "script_name is required"
    
    @pytest.mark.asyncio
    async def test_execute_trading_script_error(self, script_tools, mock_api_client):
        """Test handling errors during script execution."""
        # Mock API error
        mock_api_client.post.side_effect = Exception("API Error")
        
        arguments = {
            "script_name": "ma_cross/run.py"
        }
        
        result = await script_tools.execute_trading_script(arguments)
        
        assert result["success"] is False
        assert "Failed to execute script 'ma_cross/run.py': API Error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_check_script_status_completed(self, script_tools, mock_api_client):
        """Test checking status of a completed script."""
        # Mock API response
        mock_api_client.get.return_value = {
            "status": "completed",
            "result": "success",
            "output": "Script output",
            "completed_at": "2024-01-01T12:00:00"
        }
        
        arguments = {"execution_id": "exec-12345"}
        
        result = await script_tools.check_script_status(arguments)
        
        assert result["success"] is True
        assert result["execution_id"] == "exec-12345"
        assert result["status"] == "completed"
        assert result["result"] == "success"
        assert result["output"] == "Script output"
        assert result["completed_at"] == "2024-01-01T12:00:00"
        
        mock_api_client.get.assert_called_once_with("/api/scripts/status/exec-12345")
    
    @pytest.mark.asyncio
    async def test_check_script_status_running(self, script_tools, mock_api_client):
        """Test checking status of a running script."""
        # Mock API response
        mock_api_client.get.return_value = {
            "status": "running",
            "started_at": "2024-01-01T11:00:00",
            "progress": 50
        }
        
        arguments = {"execution_id": "exec-67890"}
        
        result = await script_tools.check_script_status(arguments)
        
        assert result["success"] is True
        assert result["status"] == "running"
        assert result["started_at"] == "2024-01-01T11:00:00"
        assert result["progress"] == 50
    
    @pytest.mark.asyncio
    async def test_check_script_status_failed(self, script_tools, mock_api_client):
        """Test checking status of a failed script."""
        # Mock API response
        mock_api_client.get.return_value = {
            "status": "failed",
            "error": "Script error message",
            "failed_at": "2024-01-01T11:30:00"
        }
        
        arguments = {"execution_id": "exec-failed"}
        
        result = await script_tools.check_script_status(arguments)
        
        assert result["success"] is True
        assert result["status"] == "failed"
        assert result["error"] == "Script error message"
        assert result["failed_at"] == "2024-01-01T11:30:00"
    
    @pytest.mark.asyncio
    async def test_check_script_status_missing_id(self, script_tools):
        """Test checking status without execution_id."""
        arguments = {}
        
        result = await script_tools.check_script_status(arguments)
        
        assert result["success"] is False
        assert result["error"] == "execution_id is required"
    
    @pytest.mark.asyncio
    async def test_check_script_status_error(self, script_tools, mock_api_client):
        """Test handling errors during status check."""
        # Mock API error
        mock_api_client.get.side_effect = Exception("Network error")
        
        arguments = {"execution_id": "exec-error"}
        
        result = await script_tools.check_script_status(arguments)
        
        assert result["success"] is False
        assert "Failed to check status for execution 'exec-error': Network error" in result["error"]


def test_get_script_tools_singleton():
    """Test that get_script_tools returns the same instance."""
    tools1 = get_script_tools()
    tools2 = get_script_tools()
    
    assert tools1 is tools2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])