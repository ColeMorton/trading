"""Test script for data tools without pytest"""

import asyncio
import json

from app.api.mcp_server.tools.data_tools import DataTools


async def test_list_data_files():
    """Test listing data files."""
    print("\n=== Testing list_data_files ===")

    tools = DataTools()

    # Test 1: List all files
    print("\n1. List all data files:")
    result = await tools.list_data_files()
    print(json.dumps(result, indent=2))
    assert result["success"] == True
    assert "directories" in result
    print("✓ List all files successful")

    # Test 2: List CSV files only
    print("\n2. List CSV files only:")
    result = await tools.list_data_files("csv")
    print(json.dumps(result, indent=2))
    assert result["success"] == True
    assert "csv" in result["directories"]
    assert len(result["directories"]) == 1
    print("✓ List CSV files successful")

    # Test 3: List JSON files only
    print("\n3. List JSON files only:")
    result = await tools.list_data_files("json")
    print(json.dumps(result, indent=2))
    assert result["success"] == True
    assert "json" in result["directories"]
    assert len(result["directories"]) == 1
    print("✓ List JSON files successful")

    # Test 4: Invalid directory
    print("\n4. List files from invalid directory:")
    result = await tools.list_data_files("invalid")
    print(json.dumps(result, indent=2))
    assert result["success"] == False
    assert "error" in result
    print("✓ Invalid directory handled correctly")


async def test_get_trading_data():
    """Test retrieving trading data."""
    print("\n\n=== Testing get_trading_data ===")

    tools = DataTools()

    # Test 1: Get CSV data (will fail without running API)
    print("\n1. Get CSV data:")
    result = await tools.get_trading_data("strategies/DAILY.csv", "csv")
    print(json.dumps(result, indent=2))
    # We expect this to fail without the API running
    if not result["success"]:
        print("✓ CSV retrieval failed as expected (API not running)")

    # Test 2: Get JSON data (will fail without running API)
    print("\n2. Get JSON data:")
    result = await tools.get_trading_data("config/trading_params.json", "json")
    print(json.dumps(result, indent=2))
    # We expect this to fail without the API running
    if not result["success"]:
        print("✓ JSON retrieval failed as expected (API not running)")

    # Test 3: Invalid file type
    print("\n3. Invalid file type:")
    result = await tools.get_trading_data("test.xml", "xml")
    print(json.dumps(result, indent=2))
    assert result["success"] == False
    assert "Invalid file type" in result["error"]
    print("✓ Invalid file type handled correctly")


async def test_get_tools():
    """Test tools registration."""
    print("\n\n=== Testing get_tools ===")

    tools = DataTools()
    tool_list = tools.get_tools()

    print(f"Number of tools: {len(tool_list)}")
    for tool in tool_list:
        print(f"- {tool.name}: {tool.description}")

    assert len(tool_list) == 2
    assert any(t.name == "list_data_files" for t in tool_list)
    assert any(t.name == "get_trading_data" for t in tool_list)
    print("✓ All tools registered correctly")


async def main():
    """Run all tests."""
    print("Starting data tools tests...")

    try:
        await test_list_data_files()
        await test_get_trading_data()
        await test_get_tools()

        print("\n\n✅ All tests completed!")

    except Exception as e:
        print(f"\n\n❌ Test failed: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
