#!/usr/bin/env python3
"""
Test script to verify MCP Puppeteer server is working at new location
Tests both direct path and npx methods
"""

import json
import subprocess
import time
import sys
from pathlib import Path

def test_server_configuration(server_path=None, use_npx=False):
    """Test a specific server configuration"""
    
    if use_npx:
        print("\n📋 Testing npx-based Puppeteer server...")
        cmd = ["npx", "-y", "@modelcontextprotocol/server-puppeteer"]
        config_name = "npx"
    else:
        print(f"\n📋 Testing Puppeteer server at: {server_path}")
        if not Path(server_path).exists():
            print(f"❌ Server file not found at: {server_path}")
            return False
        cmd = ["node", server_path]
        config_name = "direct path"
    
    try:
        # Start the server
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Give it time to start
        print(f"   Starting {config_name} server...")
        time.sleep(3 if use_npx else 2)  # npx needs more time
        
        # Check if process is running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"❌ Server failed to start")
            if stderr:
                print(f"   Error: {stderr}")
            return False
            
        print(f"✅ Server started successfully")
        
        # Send a list tools request
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
        
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()
        
        # Read response with timeout
        import select
        readable, _, _ = select.select([process.stdout], [], [], 5.0)
        
        if readable:
            response_line = process.stdout.readline()
            if response_line:
                try:
                    response = json.loads(response_line)
                    if "result" in response and "tools" in response["result"]:
                        tools = response["result"]["tools"]
                        print(f"✅ Server responded with {len(tools)} tools available")
                        return True
                    else:
                        print("❌ Invalid response from server")
                        return False
                except json.JSONDecodeError:
                    print("❌ Could not parse server response")
                    return False
        else:
            print("❌ Server did not respond")
            return False
            
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False
        
    finally:
        # Clean up
        if 'process' in locals() and process.poll() is None:
            process.terminate()
            time.sleep(1)
            if process.poll() is None:
                process.kill()

def main():
    """Main test function"""
    print("MCP Puppeteer Server Verification")
    print("=" * 50)
    
    # Test 1: Direct path configuration
    direct_path = "/Users/colemorton/mcp-servers/puppeteer/dist/index.js"
    direct_success = test_server_configuration(server_path=direct_path)
    
    # Test 2: NPX configuration
    npx_success = test_server_configuration(use_npx=True)
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"  Direct path configuration: {'✅ PASS' if direct_success else '❌ FAIL'}")
    print(f"  NPX configuration: {'✅ PASS' if npx_success else '❌ FAIL'}")
    
    if direct_success or npx_success:
        print("\n✅ MCP Puppeteer server is active and enabled!")
        print("\nRecommended configuration files:")
        print("  - Use mcp_config.json for direct path method")
        print("  - Use mcp_config_recommended.json for npx method (preferred)")
        return 0
    else:
        print("\n❌ MCP Puppeteer server tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())